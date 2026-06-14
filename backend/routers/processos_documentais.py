"""Gestão de processos/pacotes documentais do paciente.

Passo 11F: agrupa vários documentos na mesma ação operacional
(INCLUSAO, RENOVACAO, ADEQUACAO, ENCERRAMENTO), vinculando-os a uma
vigência comum e preservando a regra de comunicação documental: WhatsApp
somente manual para pendências de documentos.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import engine
from models.consultorio_models import (
    BaseConsultorio,
    DocumentoPaciente,
    ExtracaoDocumentoOCR,
    NotificacaoInterna,
    PacienteClinico,
    ProcessoDocumental,
)
from routers.consultorio import get_current_user_consultorio, get_db_consultorio, exigir_farmaceutico_ou_admin
from services.documentos_vigencia import status_vigencia
from services.ocr_documentos import loads_sugestoes

BaseConsultorio.metadata.create_all(bind=engine)


def _adicionar_coluna_se_nao_existir(tabela: str, definicao_coluna: str) -> None:
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql(f"ALTER TABLE {tabela} ADD COLUMN {definicao_coluna}")
            conn.commit()
    except Exception:
        pass


_adicionar_coluna_se_nao_existir("documentos_pacientes", "processo_documental_id INTEGER")

router = APIRouter(prefix="/consultorio", tags=["Processos Documentais"])

TIPOS_PROCESSO_DOCUMENTAL = ["INCLUSAO", "RENOVACAO", "ADEQUACAO", "ENCERRAMENTO"]
SITUACOES_PROCESSO_DOCUMENTAL = [
    "EM_MONTAGEM",
    "AGUARDANDO_DOCUMENTOS",
    "PRONTO_PARA_ENVIO",
    "ENVIADO",
    "DEFERIDO",
    "INDEFERIDO",
    "ENCERRADO",
]
PRIORIDADES_PROCESSO_DOCUMENTAL = ["NORMAL", "IMPORTANTE", "URGENTE"]

DOCUMENTOS_RECOMENDADOS = {
    "INCLUSAO": ["LAUDO", "RECEITA", "EXAME", "DOCUMENTO_PESSOAL", "TERMO"],
    "RENOVACAO": ["LAUDO", "RECEITA", "EXAME", "TERMO"],
    "ADEQUACAO": ["LAUDO", "RECEITA", "EXAME", "TERMO"],
    "ENCERRAMENTO": ["OUTRO"],
}

# Tipos aceitos para considerar uma exigência documental como atendida.
# A classificação OCR usa nomes mais específicos (ex.: ESPIROMETRIA,
# EXAME_LABORATORIAL, TERMO_ESCLARECIMENTO), enquanto o pacote documental
# usa categorias operacionais mais simples.
DOCUMENTOS_EQUIVALENTES = {
    "LAUDO": {"LAUDO"},
    "RECEITA": {"RECEITA"},
    "EXAME": {"EXAME", "EXAME_LABORATORIAL", "ESPIROMETRIA"},
    "DOCUMENTO_PESSOAL": {"DOCUMENTO_PESSOAL"},
    "TERMO": {"TERMO", "TERMO_ESCLARECIMENTO"},
    "OUTRO": {"OUTRO", "OUTROS"},
}

SITUACOES_COMPLETUDE_DOCUMENTAL = ["COMPLETO", "INCOMPLETO", "SEM_DOCUMENTOS", "EM_ANALISE"]


class ProcessoDocumentalCreate(BaseModel):
    tipo_processo: str
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    situacao: Optional[str] = "EM_MONTAGEM"
    prioridade: Optional[str] = "NORMAL"
    data_abertura: Optional[date] = None
    vigencia_inicio: Optional[date] = None
    vigencia_fim: Optional[date] = None
    pendencias_descricao: Optional[str] = None


class ProcessoDocumentalUpdate(BaseModel):
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    situacao: Optional[str] = None
    prioridade: Optional[str] = None
    data_conclusao: Optional[date] = None
    vigencia_inicio: Optional[date] = None
    vigencia_fim: Optional[date] = None
    pendencias_descricao: Optional[str] = None


class VincularDocumentoProcesso(BaseModel):
    documento_id: int


class NotificacaoPendenciaDocumentalCreate(BaseModel):
    titulo: Optional[str] = None
    mensagem: str
    prioridade: Optional[str] = "IMPORTANTE"


def _normalizar_tipo_processo(valor: str) -> str:
    normalizado = (valor or "").strip().upper()
    if normalizado not in TIPOS_PROCESSO_DOCUMENTAL:
        raise HTTPException(status_code=400, detail=f"Tipo de processo inválido. Use: {', '.join(TIPOS_PROCESSO_DOCUMENTAL)}")
    return normalizado


def _normalizar_situacao(valor: Optional[str]) -> str:
    normalizado = (valor or "EM_MONTAGEM").strip().upper()
    if normalizado not in SITUACOES_PROCESSO_DOCUMENTAL:
        raise HTTPException(status_code=400, detail=f"Situação inválida. Use: {', '.join(SITUACOES_PROCESSO_DOCUMENTAL)}")
    return normalizado


def _normalizar_prioridade(valor: Optional[str]) -> str:
    normalizado = (valor or "NORMAL").strip().upper()
    if normalizado not in PRIORIDADES_PROCESSO_DOCUMENTAL:
        raise HTTPException(status_code=400, detail=f"Prioridade inválida. Use: {', '.join(PRIORIDADES_PROCESSO_DOCUMENTAL)}")
    return normalizado


def _serializar_documento_resumido(doc: DocumentoPaciente) -> dict:
    return {
        "id": doc.id,
        "paciente_id": doc.paciente_id,
        "processo_documental_id": getattr(doc, "processo_documental_id", None),
        "tipo_documento": doc.tipo_documento,
        "titulo": doc.titulo,
        "nome_arquivo_original": doc.nome_arquivo_original,
        "data_emissao": doc.data_emissao.isoformat() if doc.data_emissao else None,
        "data_validade": doc.data_validade.isoformat() if doc.data_validade else None,
        "vigencia_inicio": doc.vigencia_inicio.isoformat() if getattr(doc, "vigencia_inicio", None) else None,
        "vigencia_fim": doc.vigencia_fim.isoformat() if getattr(doc, "vigencia_fim", None) else None,
        "vigencia_status": getattr(doc, "vigencia_status", None),
        "status": doc.status,
        "status_documental": getattr(doc, "status_documental", None) or "RECEBIDO",
        "status_documental_motivo": getattr(doc, "status_documental_motivo", None),
        "status_documental_atualizado_em": doc.status_documental_atualizado_em.isoformat() if getattr(doc, "status_documental_atualizado_em", None) else None,
        "ativo": doc.ativo,
    }


def _documentos_do_processo(db: Session, processo_id: int):
    return db.query(DocumentoPaciente).filter(
        DocumentoPaciente.processo_documental_id == processo_id,
        DocumentoPaciente.ativo == True,  # noqa: E712
    ).order_by(DocumentoPaciente.tipo_documento.asc(), DocumentoPaciente.criado_em.desc()).all()


def _classificacao_ocr_documento(db: Session, documento_id: int) -> Optional[str]:
    extracao = (
        db.query(ExtracaoDocumentoOCR)
        .filter(ExtracaoDocumentoOCR.documento_id == documento_id)
        .order_by(ExtracaoDocumentoOCR.criado_em.desc())
        .first()
    )
    if not extracao:
        return None
    campos = loads_sugestoes(extracao.campos_sugeridos_json)
    classificacao = campos.get("classificacao_documental") or {}
    tipo = classificacao.get("tipo") or campos.get("tipo_documento_sugerido")
    return (tipo or "").upper().strip() or None


def _tipos_presentes_documentais(db: Session, documentos: list[DocumentoPaciente]) -> set[str]:
    tipos = set()
    for doc in documentos:
        if not doc.ativo:
            continue
        # Regra 12F: somente documentos validados contam para a completude do pacote.
        status_documental = (getattr(doc, "status_documental", None) or "RECEBIDO").upper().strip()
        if status_documental != "VALIDADO":
            continue
        tipo_cadastrado = (doc.tipo_documento or "").upper().strip()
        if tipo_cadastrado:
            tipos.add(tipo_cadastrado)
        tipo_ocr = _classificacao_ocr_documento(db, doc.id)
        if tipo_ocr:
            tipos.add(tipo_ocr)
    return tipos


def _pendencias_do_processo(processo: ProcessoDocumental, documentos: list[DocumentoPaciente], db: Optional[Session] = None) -> list[str]:
    obrigatorios = DOCUMENTOS_RECOMENDADOS.get((processo.tipo_processo or "").upper(), [])
    if db is None:
        tipos_presentes = {d.tipo_documento for d in documentos if d.ativo}
    else:
        tipos_presentes = _tipos_presentes_documentais(db, documentos)

    pendentes = []
    for tipo in obrigatorios:
        equivalentes = DOCUMENTOS_EQUIVALENTES.get(tipo, {tipo})
        if not (equivalentes & tipos_presentes):
            pendentes.append(tipo)
    return pendentes


def _avaliar_completude_processo(db: Session, processo: ProcessoDocumental, documentos: Optional[list[DocumentoPaciente]] = None) -> dict:
    documentos = documentos if documentos is not None else _documentos_do_processo(db, processo.id)
    obrigatorios = DOCUMENTOS_RECOMENDADOS.get((processo.tipo_processo or "").upper(), [])
    tipos_presentes = _tipos_presentes_documentais(db, documentos)
    pendentes = _pendencias_do_processo(processo, documentos, db=db)

    documentos_ativos = [d for d in documentos if d.ativo]
    documentos_validados = [d for d in documentos_ativos if (getattr(d, "status_documental", None) or "RECEBIDO").upper() == "VALIDADO"]

    if not documentos_ativos:
        status = "SEM_DOCUMENTOS"
    elif pendentes:
        status = "INCOMPLETO"
    else:
        status = "COMPLETO"

    atendidos = []
    for tipo in obrigatorios:
        equivalentes = DOCUMENTOS_EQUIVALENTES.get(tipo, {tipo})
        if equivalentes & tipos_presentes:
            atendidos.append(tipo)

    return {
        "status": status,
        "documentos_obrigatorios": obrigatorios,
        "documentos_atendidos": atendidos,
        "documentos_pendentes": pendentes,
        "documentos_presentes": sorted(tipos_presentes),
        "total_documentos": len(documentos_ativos),
        "total_documentos_validados": len(documentos_validados),
        "total_documentos_aguardando_validacao": len([d for d in documentos_ativos if (getattr(d, "status_documental", None) or "RECEBIDO").upper() == "RECEBIDO"]),
        "total_documentos_rejeitados": len([d for d in documentos_ativos if (getattr(d, "status_documental", None) or "RECEBIDO").upper() == "REJEITADO"]),
        "regra_completude": "Somente documentos com status_documental VALIDADO contam para a completude.",
        "whatsapp_automatico": False,
        "regra_whatsapp_documental": "Pendências documentais geram apenas notificação interna; WhatsApp somente manual pelo operador.",
    }


def _serializar_processo(processo: ProcessoDocumental, documentos: Optional[list[DocumentoPaciente]] = None, db: Optional[Session] = None) -> dict:
    documentos = documentos if documentos is not None else list(getattr(processo, "documentos", []) or [])
    if db is not None:
        completude = _avaliar_completude_processo(db, processo, documentos)
        pendencias = completude["documentos_pendentes"]
        presentes = completude["documentos_presentes"]
    else:
        pendencias = _pendencias_do_processo(processo, documentos)
        presentes = sorted({d.tipo_documento for d in documentos if d.ativo})
        completude = {
            "status": "INCOMPLETO" if pendencias else "COMPLETO",
            "documentos_obrigatorios": DOCUMENTOS_RECOMENDADOS.get(processo.tipo_processo, []),
            "documentos_atendidos": [],
            "documentos_pendentes": pendencias,
            "documentos_presentes": presentes,
            "total_documentos": len([d for d in documentos if d.ativo]),
            "total_documentos_validados": len([d for d in documentos if d.ativo and (getattr(d, "status_documental", None) or "RECEBIDO").upper() == "VALIDADO"]),
            "regra_completude": "Somente documentos com status_documental VALIDADO contam para a completude.",
            "whatsapp_automatico": False,
            "regra_whatsapp_documental": "Pendências documentais geram apenas notificação interna; WhatsApp somente manual pelo operador.",
        }
    return {
        "id": processo.id,
        "paciente_id": processo.paciente_id,
        "tipo_processo": processo.tipo_processo,
        "titulo": processo.titulo,
        "descricao": processo.descricao,
        "situacao": processo.situacao,
        "prioridade": processo.prioridade,
        "data_abertura": processo.data_abertura.isoformat() if processo.data_abertura else None,
        "data_conclusao": processo.data_conclusao.isoformat() if processo.data_conclusao else None,
        "vigencia_inicio": processo.vigencia_inicio.isoformat() if processo.vigencia_inicio else None,
        "vigencia_fim": processo.vigencia_fim.isoformat() if processo.vigencia_fim else None,
        "vigencia_status": processo.vigencia_status,
        "pendencias_descricao": processo.pendencias_descricao,
        "whatsapp_documental_automatico": bool(processo.whatsapp_documental_automatico),
        "documentos_recomendados": DOCUMENTOS_RECOMENDADOS.get(processo.tipo_processo, []),
        "documentos_presentes": presentes,
        "documentos_pendentes": pendencias,
        "completude": completude,
        "completude_status": completude.get("status"),
        "total_documentos": len([d for d in documentos if d.ativo]),
        "documentos": [_serializar_documento_resumido(d) for d in documentos],
        "criado_por": processo.criado_por,
        "criado_em": processo.criado_em.isoformat() if processo.criado_em else None,
        "atualizado_em": processo.atualizado_em.isoformat() if processo.atualizado_em else None,
    }


def _sincronizar_vigencia_documentos(db: Session, processo: ProcessoDocumental) -> None:
    if not processo.vigencia_inicio or not processo.vigencia_fim:
        return
    novo_status = status_vigencia(processo.vigencia_inicio, processo.vigencia_fim)
    documentos = _documentos_do_processo(db, processo.id)
    for doc in documentos:
        if doc.tipo_documento in {"LAUDO", "RECEITA"}:
            doc.vigencia_inicio = processo.vigencia_inicio
            doc.vigencia_fim = processo.vigencia_fim
            doc.vigencia_status = novo_status
            doc.vigencia_origem_calculo = "PROCESSO_DOCUMENTAL"
            doc.atualizado_em = datetime.utcnow()


def _adotar_vigencia_do_documento_principal(db: Session, processo: ProcessoDocumental) -> None:
    if processo.vigencia_inicio and processo.vigencia_fim:
        return
    doc = db.query(DocumentoPaciente).filter(
        DocumentoPaciente.processo_documental_id == processo.id,
        DocumentoPaciente.tipo_documento == "LAUDO",
        DocumentoPaciente.vigencia_inicio.isnot(None),
        DocumentoPaciente.vigencia_fim.isnot(None),
        DocumentoPaciente.ativo == True,  # noqa: E712
    ).order_by(DocumentoPaciente.criado_em.desc()).first()
    if not doc:
        return
    processo.vigencia_inicio = doc.vigencia_inicio
    processo.vigencia_fim = doc.vigencia_fim
    processo.vigencia_status = doc.vigencia_status
    processo.atualizado_em = datetime.utcnow()


@router.get("/processos-documentais/opcoes")
def opcoes_processos_documentais(current=Depends(get_current_user_consultorio)):
    return {
        "tipos_processo": TIPOS_PROCESSO_DOCUMENTAL,
        "situacoes": SITUACOES_PROCESSO_DOCUMENTAL,
        "prioridades": PRIORIDADES_PROCESSO_DOCUMENTAL,
        "documentos_recomendados": DOCUMENTOS_RECOMENDADOS,
        "regra_whatsapp_documental": "Pendências documentais não geram WhatsApp automático; envio somente manual pelo operador.",
    }


@router.post("/paciente-clinico/{paciente_id}/processos-documentais")
def criar_processo_documental(
    paciente_id: int,
    dados: ProcessoDocumentalCreate,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    exigir_farmaceutico_ou_admin(current)
    paciente = db.query(PacienteClinico).filter(PacienteClinico.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente clínico não encontrado")
    tipo = _normalizar_tipo_processo(dados.tipo_processo)
    processo = ProcessoDocumental(
        paciente_id=paciente_id,
        tipo_processo=tipo,
        titulo=dados.titulo or f"{tipo.title()} - {paciente.nome}",
        descricao=dados.descricao,
        situacao=_normalizar_situacao(dados.situacao),
        prioridade=_normalizar_prioridade(dados.prioridade),
        data_abertura=dados.data_abertura or date.today(),
        vigencia_inicio=dados.vigencia_inicio,
        vigencia_fim=dados.vigencia_fim,
        vigencia_status=status_vigencia(dados.vigencia_inicio, dados.vigencia_fim) if (dados.vigencia_inicio or dados.vigencia_fim) else None,
        pendencias_descricao=dados.pendencias_descricao,
        whatsapp_documental_automatico=False,
        criado_por=getattr(current, "email", None) or getattr(current, "nome", None),
    )
    db.add(processo)
    db.commit()
    db.refresh(processo)
    return {"mensagem": "Processo documental criado", "processo": _serializar_processo(processo, [], db=db)}


@router.get("/paciente-clinico/{paciente_id}/processos-documentais")
def listar_processos_paciente(
    paciente_id: int,
    tipo_processo: Optional[str] = None,
    situacao: Optional[str] = None,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    paciente = db.query(PacienteClinico).filter(PacienteClinico.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente clínico não encontrado")
    query = db.query(ProcessoDocumental).filter(ProcessoDocumental.paciente_id == paciente_id)
    if tipo_processo:
        query = query.filter(ProcessoDocumental.tipo_processo == tipo_processo.upper())
    if situacao:
        query = query.filter(ProcessoDocumental.situacao == situacao.upper())
    processos = query.order_by(ProcessoDocumental.criado_em.desc()).all()
    return {"total": len(processos), "processos": [_serializar_processo(p, _documentos_do_processo(db, p.id), db=db) for p in processos]}


@router.get("/processos-documentais/dashboard")
def dashboard_processos_documentais(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    total = db.query(ProcessoDocumental).count()
    em_montagem = db.query(ProcessoDocumental).filter(ProcessoDocumental.situacao == "EM_MONTAGEM").count()
    aguardando = db.query(ProcessoDocumental).filter(ProcessoDocumental.situacao == "AGUARDANDO_DOCUMENTOS").count()
    prontos = db.query(ProcessoDocumental).filter(ProcessoDocumental.situacao == "PRONTO_PARA_ENVIO").count()
    deferidos = db.query(ProcessoDocumental).filter(ProcessoDocumental.situacao == "DEFERIDO").count()
    urgentes = db.query(ProcessoDocumental).filter(ProcessoDocumental.prioridade == "URGENTE").count()
    por_tipo = dict(db.query(ProcessoDocumental.tipo_processo, func.count(ProcessoDocumental.id)).group_by(ProcessoDocumental.tipo_processo).all())
    return {
        "total": total,
        "em_montagem": em_montagem,
        "aguardando_documentos": aguardando,
        "prontos_para_envio": prontos,
        "deferidos": deferidos,
        "urgentes": urgentes,
        "por_tipo": por_tipo,
        "regra_whatsapp_documental": "Somente manual para pendências documentais.",
    }


@router.get("/processos-documentais/completude-dashboard")
def dashboard_completude_processos_documentais(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    processos = db.query(ProcessoDocumental).all()
    resumo = {status: 0 for status in SITUACOES_COMPLETUDE_DOCUMENTAL}
    pendencias_por_tipo = {}

    for processo in processos:
        documentos = _documentos_do_processo(db, processo.id)
        completude = _avaliar_completude_processo(db, processo, documentos)
        status = completude["status"]
        resumo[status] = resumo.get(status, 0) + 1
        for pendencia in completude["documentos_pendentes"]:
            pendencias_por_tipo[pendencia] = pendencias_por_tipo.get(pendencia, 0) + 1

    return {
        "total_processos": len(processos),
        "por_status": resumo,
        "pendencias_por_tipo": pendencias_por_tipo,
        "whatsapp_documental_automatico": False,
        "regra_whatsapp_documental": "Pendências documentais geram apenas notificação interna; WhatsApp somente manual pelo operador.",
    }


@router.get("/processos-documentais/{processo_id}")
def detalhar_processo_documental(
    processo_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    processo = db.query(ProcessoDocumental).filter(ProcessoDocumental.id == processo_id).first()
    if not processo:
        raise HTTPException(status_code=404, detail="Processo documental não encontrado")
    documentos = _documentos_do_processo(db, processo.id)
    return {"processo": _serializar_processo(processo, documentos, db=db)}


@router.get("/processos-documentais/{processo_id}/completude")
def obter_completude_processo_documental(
    processo_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    processo = db.query(ProcessoDocumental).filter(ProcessoDocumental.id == processo_id).first()
    if not processo:
        raise HTTPException(status_code=404, detail="Processo documental não encontrado")
    documentos = _documentos_do_processo(db, processo.id)
    return {
        "processo_id": processo.id,
        "tipo_processo": processo.tipo_processo,
        "completude": _avaliar_completude_processo(db, processo, documentos),
    }


@router.post("/processos-documentais/{processo_id}/validar-completude")
def validar_completude_processo_documental(
    processo_id: int,
    gerar_notificacao: bool = True,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    exigir_farmaceutico_ou_admin(current)
    processo = db.query(ProcessoDocumental).filter(ProcessoDocumental.id == processo_id).first()
    if not processo:
        raise HTTPException(status_code=404, detail="Processo documental não encontrado")

    documentos = _documentos_do_processo(db, processo.id)
    completude = _avaliar_completude_processo(db, processo, documentos)

    if completude["status"] == "COMPLETO":
        if processo.situacao in {"EM_MONTAGEM", "AGUARDANDO_DOCUMENTOS"}:
            processo.situacao = "PRONTO_PARA_ENVIO"
        processo.pendencias_descricao = None
    elif completude["status"] in {"INCOMPLETO", "SEM_DOCUMENTOS"}:
        processo.situacao = "AGUARDANDO_DOCUMENTOS"
        processo.pendencias_descricao = "Documentos pendentes: " + ", ".join(completude["documentos_pendentes"])
        if gerar_notificacao:
            notificacao = NotificacaoInterna(
                paciente_id=processo.paciente_id,
                tipo="PENDENCIA_DOCUMENTAL",
                prioridade="IMPORTANTE",
                origem="PENDENCIA_DOCUMENTAL",
                titulo=f"Pacote documental incompleto - {processo.tipo_processo.title()}",
                mensagem=processo.pendencias_descricao or "Pacote documental incompleto.",
                lida=False,
                necessita_acao=True,
            )
            db.add(notificacao)

    processo.atualizado_em = datetime.utcnow()
    db.commit()
    db.refresh(processo)
    return {
        "mensagem": "Completude documental validada",
        "processo": _serializar_processo(processo, _documentos_do_processo(db, processo.id), db=db),
        "whatsapp_automatico": False,
    }


@router.put("/processos-documentais/{processo_id}")
def atualizar_processo_documental(
    processo_id: int,
    dados: ProcessoDocumentalUpdate,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    exigir_farmaceutico_ou_admin(current)
    processo = db.query(ProcessoDocumental).filter(ProcessoDocumental.id == processo_id).first()
    if not processo:
        raise HTTPException(status_code=404, detail="Processo documental não encontrado")
    if dados.titulo is not None:
        processo.titulo = dados.titulo
    if dados.descricao is not None:
        processo.descricao = dados.descricao
    if dados.situacao is not None:
        processo.situacao = _normalizar_situacao(dados.situacao)
    if dados.prioridade is not None:
        processo.prioridade = _normalizar_prioridade(dados.prioridade)
    if dados.data_conclusao is not None:
        processo.data_conclusao = dados.data_conclusao
    if dados.vigencia_inicio is not None:
        processo.vigencia_inicio = dados.vigencia_inicio
    if dados.vigencia_fim is not None:
        processo.vigencia_fim = dados.vigencia_fim
    if dados.pendencias_descricao is not None:
        processo.pendencias_descricao = dados.pendencias_descricao
    processo.vigencia_status = status_vigencia(processo.vigencia_inicio, processo.vigencia_fim) if (processo.vigencia_inicio or processo.vigencia_fim) else None
    processo.atualizado_em = datetime.utcnow()
    _sincronizar_vigencia_documentos(db, processo)
    db.commit()
    db.refresh(processo)
    return {"mensagem": "Processo documental atualizado", "processo": _serializar_processo(processo, _documentos_do_processo(db, processo.id), db=db)}


@router.post("/processos-documentais/{processo_id}/vincular-documento")
def vincular_documento_ao_processo(
    processo_id: int,
    dados: VincularDocumentoProcesso,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    exigir_farmaceutico_ou_admin(current)
    processo = db.query(ProcessoDocumental).filter(ProcessoDocumental.id == processo_id).first()
    if not processo:
        raise HTTPException(status_code=404, detail="Processo documental não encontrado")
    doc = db.query(DocumentoPaciente).filter(DocumentoPaciente.id == dados.documento_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    if doc.paciente_id != processo.paciente_id:
        raise HTTPException(status_code=400, detail="Documento pertence a outro paciente")
    doc.processo_documental_id = processo.id
    doc.atualizado_em = datetime.utcnow()
    _adotar_vigencia_do_documento_principal(db, processo)
    _sincronizar_vigencia_documentos(db, processo)
    db.commit()
    db.refresh(processo)
    return {"mensagem": "Documento vinculado ao processo", "processo": _serializar_processo(processo, _documentos_do_processo(db, processo.id), db=db)}


@router.put("/documentos/{documento_id}/desvincular-processo")
def desvincular_documento_do_processo(
    documento_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    exigir_farmaceutico_ou_admin(current)
    doc = db.query(DocumentoPaciente).filter(DocumentoPaciente.id == documento_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    processo_id = doc.processo_documental_id
    doc.processo_documental_id = None
    doc.atualizado_em = datetime.utcnow()
    db.commit()
    return {"mensagem": "Documento desvinculado", "processo_documental_id_anterior": processo_id}


@router.get("/processos-documentais/{processo_id}/documentos")
def listar_documentos_do_processo(
    processo_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    processo = db.query(ProcessoDocumental).filter(ProcessoDocumental.id == processo_id).first()
    if not processo:
        raise HTTPException(status_code=404, detail="Processo documental não encontrado")
    documentos = _documentos_do_processo(db, processo.id)
    return {"total": len(documentos), "documentos": [_serializar_documento_resumido(d) for d in documentos]}


@router.post("/processos-documentais/{processo_id}/notificar-pendencia")
def criar_notificacao_pendencia_documental(
    processo_id: int,
    dados: NotificacaoPendenciaDocumentalCreate,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    exigir_farmaceutico_ou_admin(current)
    processo = db.query(ProcessoDocumental).filter(ProcessoDocumental.id == processo_id).first()
    if not processo:
        raise HTTPException(status_code=404, detail="Processo documental não encontrado")
    prioridade = _normalizar_prioridade(dados.prioridade)
    notificacao = NotificacaoInterna(
        paciente_id=processo.paciente_id,
        tipo="PENDENCIA_DOCUMENTAL",
        prioridade=prioridade,
        origem="PENDENCIA_DOCUMENTAL",
        titulo=dados.titulo or f"Pendência documental - {processo.tipo_processo.title()}",
        mensagem=dados.mensagem,
        lida=False,
        necessita_acao=True,
    )
    db.add(notificacao)
    processo.pendencias_descricao = dados.mensagem
    processo.situacao = "AGUARDANDO_DOCUMENTOS"
    processo.atualizado_em = datetime.utcnow()
    db.commit()
    db.refresh(notificacao)
    return {
        "mensagem": "Notificação interna de pendência criada. WhatsApp automático bloqueado por regra de negócio; use envio manual se necessário.",
        "notificacao_id": notificacao.id,
        "whatsapp_automatico": False,
    }
