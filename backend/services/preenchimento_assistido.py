"""Serviço de pré-preenchimento assistido a partir de documentos validados.

Passo 12E: usa apenas documentos com status_documental VALIDADO e resultados OCR já
existentes para gerar sugestões ao operador. Nenhuma sugestão altera paciente,
vigência, agenda, notificação ou WhatsApp sem confirmação humana.
"""

from __future__ import annotations

import difflib
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy.orm import Session

from models.consultorio_models import (
    CatalogoMedicamento,
    DocumentoPaciente,
    ExtracaoDocumentoOCR,
    PacienteClinico,
    ProcessoDocumental,
)
from services.ocr_documentos import loads_sugestoes

CAMPOS_ASSISTIDOS = [
    "nome_paciente",
    "nome_mae",
    "cid",
    "diagnostico",
    "medicamento",
    "cns_paciente",
    "municipio",
    "data_solicitacao",
]


def _valor_valido(valor: Any) -> bool:
    if valor is None:
        return False
    if isinstance(valor, str):
        return bool(valor.strip())
    if isinstance(valor, list):
        return any(_valor_valido(v) for v in valor)
    return True


def _normalizar_texto(valor: Any) -> str:
    if valor is None:
        return ""
    if isinstance(valor, list):
        valor = " ".join(str(v) for v in valor if v)
    return " ".join(str(valor).upper().replace("-", " ").split())


def _ultima_extracao_documento(db: Session, documento_id: int) -> Optional[ExtracaoDocumentoOCR]:
    return (
        db.query(ExtracaoDocumentoOCR)
        .filter(ExtracaoDocumentoOCR.documento_id == documento_id)
        .order_by(ExtracaoDocumentoOCR.criado_em.desc())
        .first()
    )


def _extracoes_validadas_do_processo(db: Session, processo_id: int) -> list[tuple[DocumentoPaciente, ExtracaoDocumentoOCR]]:
    documentos = (
        db.query(DocumentoPaciente)
        .filter(
            DocumentoPaciente.processo_documental_id == processo_id,
            DocumentoPaciente.ativo == True,  # noqa: E712
        )
        .order_by(DocumentoPaciente.criado_em.desc())
        .all()
    )
    pares: list[tuple[DocumentoPaciente, ExtracaoDocumentoOCR]] = []
    for doc in documentos:
        status = (getattr(doc, "status_documental", None) or "RECEBIDO").upper().strip()
        if status != "VALIDADO":
            continue
        extracao = _ultima_extracao_documento(db, doc.id)
        if extracao:
            pares.append((doc, extracao))
    return pares


def _campos_estruturados_da_extracao(extracao: ExtracaoDocumentoOCR) -> dict:
    sugestoes = loads_sugestoes(extracao.campos_sugeridos_json)
    estruturados = sugestoes.get("campos_estruturados") or {}
    campos_lme = estruturados.get("campos") if isinstance(estruturados, dict) else None
    base = {}
    if isinstance(campos_lme, dict):
        base.update(campos_lme)
    # Mantém compatibilidade com sugestões genéricas antigas.
    for chave in ["nome_paciente", "cid", "crm", "medico", "data_emissao", "data_validade", "medicamentos"]:
        if sugestoes.get(chave) and not base.get(chave):
            base[chave] = sugestoes.get(chave)
    return base


def _adicionar_sugestao(
    sugestoes: dict,
    campo: str,
    valor: Any,
    documento: DocumentoPaciente,
    extracao: ExtracaoDocumentoOCR,
    confianca: float,
    origem: str,
) -> None:
    if not _valor_valido(valor):
        return
    if isinstance(valor, list):
        valor = ", ".join(str(v) for v in valor if _valor_valido(v))
    valor = str(valor).strip()
    if not valor:
        return
    atual = sugestoes.get(campo)
    if atual and float(atual.get("confianca", 0)) >= confianca:
        return
    sugestoes[campo] = {
        "valor": valor,
        "confianca": round(float(confianca), 2),
        "documento_id": documento.id,
        "documento_titulo": documento.titulo or documento.nome_arquivo_original,
        "extracao_id": extracao.id,
        "origem": origem,
        "status_documental": getattr(documento, "status_documental", None) or "RECEBIDO",
    }


def _buscar_medicamento_catalogo(db: Session, medicamento_texto: Optional[str]) -> Optional[dict]:
    if not medicamento_texto:
        return None
    alvo = _normalizar_texto(medicamento_texto)
    if not alvo:
        return None
    catalogo = db.query(CatalogoMedicamento).filter(CatalogoMedicamento.ativo == True).all()  # noqa: E712
    melhor = None
    melhor_score = 0.0
    for med in catalogo:
        descricao = " ".join(
            str(p) for p in [med.farmaco, med.apresentacao, med.concentracao, med.forma_farmaceutica]
            if p
        )
        candidato = _normalizar_texto(descricao)
        if not candidato:
            continue
        score = difflib.SequenceMatcher(None, alvo, candidato).ratio()
        # Bônus quando o fármaco aparece literalmente no OCR.
        farmaco = _normalizar_texto(med.farmaco)
        if farmaco and farmaco in alvo:
            score = max(score, 0.82)
        if score > melhor_score:
            melhor_score = score
            melhor = med
    if not melhor or melhor_score < 0.45:
        return None
    return {
        "id": melhor.id,
        "farmaco": melhor.farmaco,
        "apresentacao": melhor.apresentacao,
        "concentracao": melhor.concentracao,
        "forma_farmaceutica": melhor.forma_farmaceutica,
        "descricao_completa": melhor.descricao_completa,
        "confianca": round(min(0.98, melhor_score), 2),
    }


def gerar_sugestoes_preenchimento_processo(db: Session, processo_id: int) -> dict:
    processo = db.query(ProcessoDocumental).filter(ProcessoDocumental.id == processo_id).first()
    if not processo:
        raise ValueError("Processo documental não encontrado")
    paciente = db.query(PacienteClinico).filter(PacienteClinico.id == processo.paciente_id).first()

    pares = _extracoes_validadas_do_processo(db, processo.id)
    sugestoes: Dict[str, dict] = {}

    for documento, extracao in pares:
        campos = _campos_estruturados_da_extracao(extracao)
        campos_sugeridos = loads_sugestoes(extracao.campos_sugeridos_json)
        confianca_estruturada = campos_sugeridos.get("confianca_extracao_estruturada") or 0.75
        try:
            confianca_estruturada = float(confianca_estruturada)
        except Exception:
            confianca_estruturada = 0.75

        mapeamento = {
            "nome_paciente": campos.get("nome_paciente"),
            "nome_mae": campos.get("nome_mae"),
            "cid": campos.get("cid"),
            "diagnostico": campos.get("diagnostico"),
            "medicamento": campos.get("medicamento") or campos.get("medicamentos"),
            "cns_paciente": campos.get("cns_paciente"),
            "municipio": campos.get("municipio"),
            "data_solicitacao": campos.get("data_solicitacao") or campos.get("data_emissao"),
        }
        for campo, valor in mapeamento.items():
            _adicionar_sugestao(
                sugestoes,
                campo,
                valor,
                documento,
                extracao,
                confianca_estruturada,
                "OCR_DOCUMENTO_VALIDADO",
            )

    medicamento_catalogo = _buscar_medicamento_catalogo(db, sugestoes.get("medicamento", {}).get("valor"))
    if medicamento_catalogo:
        sugestoes["medicamento_catalogo"] = {
            "valor": medicamento_catalogo["descricao_completa"],
            "confianca": medicamento_catalogo["confianca"],
            "catalogo_medicamento_id": medicamento_catalogo["id"],
            "origem": "CRUZAMENTO_CATALOGO_MEDICAMENTOS",
            "detalhes": medicamento_catalogo,
        }

    vigencia_sugerida = None
    if processo.vigencia_inicio and processo.vigencia_fim:
        vigencia_sugerida = {
            "inicio": processo.vigencia_inicio.isoformat(),
            "fim": processo.vigencia_fim.isoformat(),
            "regra": "Vigência já calculada no processo documental. Conferir antes de aplicar em qualquer fluxo operacional.",
            "confianca": 0.9,
        }

    return {
        "processo_id": processo.id,
        "paciente_id": processo.paciente_id,
        "paciente_nome_atual": getattr(paciente, "nome", None),
        "tipo_processo": processo.tipo_processo,
        "fontes_utilizadas": [
            {
                "documento_id": doc.id,
                "titulo": doc.titulo or doc.nome_arquivo_original,
                "tipo_documento": doc.tipo_documento,
                "status_documental": doc.status_documental,
                "extracao_id": ext.id,
            }
            for doc, ext in pares
        ],
        "total_documentos_validados_com_ocr": len(pares),
        "sugestoes": sugestoes,
        "vigencia_sugerida": vigencia_sugerida,
        "regra_seguranca": "Usa somente documentos VALIDADOS. Nenhuma atualização automática é realizada; o operador deve confirmar antes de aplicar.",
        "atualizacao_automatica": False,
    }


def aplicar_sugestoes_ao_processo(
    db: Session,
    processo_id: int,
    campos: Iterable[str],
    usuario: Optional[str] = None,
    observacao: Optional[str] = None,
) -> dict:
    """Registra no processo as sugestões confirmadas pelo operador.

    Não altera paciente, vigência, agenda, notificações ou WhatsApp. Para evitar
    criar campos ainda instáveis no banco, as informações confirmadas são
    registradas na descrição do processo como bloco auditável de conferência.
    """
    processo = db.query(ProcessoDocumental).filter(ProcessoDocumental.id == processo_id).first()
    if not processo:
        raise ValueError("Processo documental não encontrado")

    resultado = gerar_sugestoes_preenchimento_processo(db, processo_id)
    sugestoes = resultado.get("sugestoes") or {}
    campos_solicitados = [str(c).strip() for c in campos if str(c).strip()]
    aplicados = {}
    for campo in campos_solicitados:
        if campo in sugestoes:
            aplicados[campo] = sugestoes[campo]

    if not aplicados:
        return {"processo_id": processo.id, "aplicados": {}, "mensagem": "Nenhuma sugestão válida selecionada."}

    linhas = [
        "",
        "[Pré-preenchimento assistido confirmado pelo operador]",
        f"Data/hora: {datetime.utcnow().isoformat()} UTC",
        f"Usuário: {usuario or 'não informado'}",
    ]
    if observacao:
        linhas.append(f"Observação: {observacao}")
    for campo, dados in aplicados.items():
        linhas.append(f"{campo}: {dados.get('valor')} (confiança: {dados.get('confianca')})")

    bloco = "\n".join(linhas)
    processo.descricao = ((processo.descricao or "").rstrip() + "\n" + bloco).strip()
    if not processo.titulo and sugestoes.get("cid"):
        processo.titulo = f"{processo.tipo_processo} - CID {sugestoes['cid'].get('valor')}"
    processo.atualizado_em = datetime.utcnow()
    db.commit()
    db.refresh(processo)
    return {
        "processo_id": processo.id,
        "aplicados": aplicados,
        "mensagem": "Sugestões confirmadas e registradas no processo documental. Nenhuma atualização automática foi feita em paciente, vigência, agenda ou WhatsApp.",
    }
