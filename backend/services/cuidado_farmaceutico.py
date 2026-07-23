"""Serviços do motor de cuidado farmacêutico longitudinal.

Este módulo consolida PRM, metas terapêuticas, plano de cuidado,
complexidade farmacoterapêutica e linha do tempo sem substituir as rotas
legadas. A proposta é criar contratos canônicos e progressivamente reduzir
redundâncias.
"""
from __future__ import annotations

from datetime import datetime, date
from statistics import median
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.consultorio_models import (
    PacienteClinico,
    ProntuarioClinico,
    EvolucaoClinica,
    DesfechoClinico,
    MedicamentoUso,
    IntervencaoFarmacoterapia,
    DesfechoIntervencaoFarmacoterapia,
    PlanoCuidado,
    AgendaIntegrada,
    ProcessoDocumental,
    DocumentoPaciente,
    ProblemaFarmacoterapeutico,
    MetaTerapeutica,
    AcaoPlanoCuidado,
    AvaliacaoComplexidadeFarmacoterapeutica,
    ExtracaoDocumentoOCR,
    HistoricoStatusDocumento,
    HistoricoVigenciaDocumento,
)

PRM_CATALOGO_VERSAO = "2026.1"
PRM_SISTEMA_CODIFICACAO = "PRM_FE_NEES_V1"

PRM_CATEGORIAS = ["NECESSIDADE", "EFETIVIDADE", "SEGURANCA", "ADESAO"]
PRM_NATUREZAS = ["POTENCIAL", "MANIFESTO"]
PRM_CRITICIDADES = ["BAIXA", "MODERADA", "ALTA"]
GRAVIDADES = PRM_CRITICIDADES  # compatibilidade com o código anterior
STATUS_PRM = ["ABERTO", "EM_ACOMPANHAMENTO", "RESOLVIDO", "NAO_RESOLVIDO", "REGISTRO_INVALIDO", "DESCARTADO"]
DESFECHOS_PRM = ["RESOLVIDO", "PARCIALMENTE_RESOLVIDO", "NAO_RESOLVIDO", "NAO_AVALIADO"]
ORIGENS_PRM = ["CONSULTA_FARMACEUTICA", "TRIAGEM", "RETORNO", "IMPORTACAO_APP_INTERVENCOES", "AUDITORIA_DOCUMENTAL", "OUTRO"]
CAUSAS_PRM = [
    "INTERACAO_MEDICAMENTOSA", "CONTRAINDICACAO", "MONITORAMENTO_INSUFICIENTE",
    "DIFICULDADE_ACESSO", "BAIXA_COMPREENSAO", "ESQUECIMENTO", "EVENTO_ADVERSO",
    "FALHA_DISPENSACAO", "PRESCRICAO_INCOMPLETA", "OUTRA",
]

PRM_CATALOGO = {
    "NECESSIDADE": [
        {
            "codigo": "CONDICAO_NAO_TRATADA",
            "rotulo": "Condição não tratada",
            "definicao": "Problema de saúde sem manejo farmacológico ou não farmacológico documentado quando há necessidade clínica de cuidado.",
        },
        {
            "codigo": "MEDICAMENTO_NECESSARIO_AUSENTE",
            "rotulo": "Medicamento necessário ausente",
            "definicao": "Há indicação farmacológica específica, mas o medicamento necessário não está em uso.",
        },
        {
            "codigo": "NECESSIDADE_TERAPIA_ADICIONAL",
            "rotulo": "Necessidade de terapia adicional",
            "definicao": "Necessidade de intensificação, prevenção, associação ou terapia complementar.",
        },
        {
            "codigo": "TERAPIA_DESNECESSARIA",
            "rotulo": "Terapia desnecessária",
            "definicao": "Medicamento em uso sem indicação atual clara ou com duplicidade terapêutica não justificada.",
        },
    ],
    "EFETIVIDADE": [
        {
            "codigo": "MEDICAMENTO_INEFETIVO",
            "rotulo": "Medicamento inefetivo",
            "definicao": "Medicamento não produz resposta esperada ou não é adequado para a condição/objetivo terapêutico.",
        },
        {
            "codigo": "DOSE_INSUFICIENTE",
            "rotulo": "Dose insuficiente",
            "definicao": "Dose, concentração ou exposição menor que a necessária para atingir a meta terapêutica.",
        },
        {
            "codigo": "FREQUENCIA_INADEQUADA",
            "rotulo": "Frequência inadequada",
            "definicao": "Intervalo, horário ou frequência de administração inadequado para efetividade.",
        },
        {
            "codigo": "FORMA_FARMACEUTICA_INADEQUADA",
            "rotulo": "Forma farmacêutica inadequada",
            "definicao": "Forma, dispositivo ou apresentação não favorece efetividade ou uso correto.",
        },
    ],
    "SEGURANCA": [
        {
            "codigo": "DOSE_EXCESSIVA",
            "rotulo": "Dose excessiva",
            "definicao": "Dose, concentração ou exposição superior ao necessário, com risco de dano.",
        },
        {
            "codigo": "REACAO_ADVERSA",
            "rotulo": "Reação adversa",
            "definicao": "Suspeita ou confirmação de reação adversa associada ao medicamento.",
        },
        {
            "codigo": "INTERACAO_MEDICAMENTOSA",
            "rotulo": "Interação medicamentosa",
            "definicao": "Potencial ou manifestação clínica relacionada à interação entre medicamentos, alimento, condição ou exame.",
            "observacao": "Pode ser melhor detalhada como causa/fator contribuinte em fase posterior.",
        },
        {
            "codigo": "CONTRAINDICACAO",
            "rotulo": "Contraindicação",
            "definicao": "Uso de medicamento contraindicado ou não recomendado para condição clínica, idade, gestação, alergia ou comorbidade.",
            "observacao": "Pode ser melhor detalhada como causa/fator contribuinte em fase posterior.",
        },
        {
            "codigo": "MONITORAMENTO_INSUFICIENTE",
            "rotulo": "Monitoramento insuficiente",
            "definicao": "Ausência ou atraso de monitoramento necessário para terapia que exige vigilância clínica ou laboratorial.",
            "observacao": "Pode ser melhor detalhada como causa/fator contribuinte em fase posterior.",
        },
    ],
    "ADESAO": [
        {
            "codigo": "ESQUECIMENTO",
            "rotulo": "Esquecimento",
            "definicao": "Paciente relata omissões por esquecimento ou dificuldade de manter rotina de uso.",
            "fase_adesao": "IMPLEMENTACAO",
        },
        {
            "codigo": "DIFICULDADE_ACESSO",
            "rotulo": "Dificuldade de acesso",
            "definicao": "Barreira de obtenção, retirada, custo, deslocamento ou disponibilidade que compromete início/continuidade.",
            "fase_adesao": "INICIACAO_OU_PERSISTENCIA",
        },
        {
            "codigo": "USO_INCORRETO",
            "rotulo": "Uso incorreto",
            "definicao": "Paciente utiliza dose, via, frequência, técnica ou horário diferente do orientado.",
            "fase_adesao": "IMPLEMENTACAO",
        },
        {
            "codigo": "ABANDONO_TRATAMENTO",
            "rotulo": "Abandono do tratamento",
            "definicao": "Paciente interrompeu o tratamento sem orientação profissional ou sem substituição documentada.",
            "fase_adesao": "DESCONTINUACAO",
        },
        {
            "codigo": "BAIXA_COMPREENSAO_TERAPIA",
            "rotulo": "Baixa compreensão da terapia",
            "definicao": "Dificuldade de compreender finalidade, modo de uso, riscos ou benefícios do tratamento.",
            "fase_adesao": "TRANSVERSAL",
        },
    ],
}

PRM_TIPOS = [item["codigo"] for itens in PRM_CATALOGO.values() for item in itens] + ["OUTRO"]
METAS_PARAMETROS = ["PA", "GLICEMIA", "PICO_FLUXO", "PESO", "ADESAO", "SINTOMAS", "EXAMES", "OUTRO"]
STATUS_METAS = ["ATIVA", "ALCANCADA", "PARCIAL", "NAO_ALCANCADA", "CANCELADA"]
TIPOS_ACAO = ["ORIENTACAO", "AJUSTE_TERAPEUTICO", "ENCAMINHAMENTO", "MONITORAMENTO", "CONTATO", "EDUCACAO_SAUDE", "OUTRO"]
STATUS_ACAO = ["PENDENTE", "EM_ANDAMENTO", "CONCLUIDA", "CANCELADA"]

ALTO_RISCO_TERMO = [
    "insulina", "varfarina", "warfarin", "digoxina", "lítio", "litio",
    "metotrexato", "clozapina", "opioide", "morfina", "fentanil",
    "heparina", "enoxaparina", "carbamazepina", "fenitoina", "fenitoína",
]


def _dt(v: Any):
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    return v


def _safe_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def serializar_paciente(p: PacienteClinico | None) -> dict | None:
    if not p:
        return None
    return {
        "id": p.id,
        "nome": p.nome,
        "data_nascimento": _dt(p.data_nascimento),
        "idade": p.idade,
        "sexo": p.sexo,
        "telefone": p.telefone,
        "cpf": p.cpf,
        "cns": p.cns,
        "cid_principal": p.cid_principal,
        "cid_secundario": p.cid_secundario,
        "comorbidades": p.comorbidades,
        "alergias": p.alergias,
        "adesao_terapeutica": p.adesao_terapeutica,
        "meta_pressao_arterial": p.meta_pressao_arterial,
        "meta_glicemica": p.meta_glicemica,
        "meta_peso": p.meta_peso,
    }


def serializar_medicamento(m: MedicamentoUso) -> dict:
    return {
        "id": m.id,
        "nome_medicamento": m.nome_medicamento,
        "dose": m.dose,
        "via": m.via,
        "frequencia": m.frequencia,
        "indicacao": m.indicacao,
        "uso_off_label": getattr(m, "uso_off_label", "NAO_AVALIADO") or "NAO_AVALIADO",
        "justificativa_off_label": getattr(m, "justificativa_off_label", None),
        "evidencia_off_label": getattr(m, "evidencia_off_label", None),
        "uso_continuo": bool(m.uso_continuo),
        "adesao_referida": m.adesao_referida,
        "ativo": bool(m.ativo),
        "criado_em": _dt(m.criado_em),
    }


def serializar_prm(prm: ProblemaFarmacoterapeutico) -> dict:
    subcategoria = getattr(prm, "subcategoria", None) or prm.tipo
    criticidade = getattr(prm, "criticidade", None) or prm.gravidade
    return {
        "id": prm.id,
        "paciente_clinico_id": prm.paciente_clinico_id,
        "medicamento_uso_id": prm.medicamento_uso_id,
        "categoria": prm.categoria,
        "tipo": prm.tipo,
        "subcategoria": subcategoria,
        "natureza": getattr(prm, "natureza", None) or "MANIFESTO",
        "gravidade": prm.gravidade,
        "criticidade": criticidade,
        "descricao": prm.descricao,
        "evidencias": prm.evidencias,
        "causa_fator": getattr(prm, "causa_fator", None),
        "condicao_saude": getattr(prm, "condicao_saude", None),
        "status": prm.status,
        "desfecho": getattr(prm, "desfecho", None) or "NAO_AVALIADO",
        "data_identificacao": _dt(prm.data_identificacao),
        "data_resolucao": _dt(prm.data_resolucao),
        "resolucao": prm.resolucao,
        "origem": prm.origem,
        "sistema_codificacao": getattr(prm, "sistema_codificacao", None) or PRM_SISTEMA_CODIFICACAO,
        "versao_catalogo": getattr(prm, "versao_catalogo", None) or PRM_CATALOGO_VERSAO,
        "codigo_externo": getattr(prm, "codigo_externo", None),
        "criado_por": prm.criado_por,
        "criado_em": _dt(prm.criado_em),
    }



def _normalizar_codigo(valor: Any, padrao: str = "NAO_INFORMADO") -> str:
    texto = _safe_text(valor)
    if not texto:
        return padrao
    return texto.upper().strip()


def _incrementar(contador: dict[str, int], chave: Any, padrao: str = "NAO_INFORMADO") -> None:
    codigo = _normalizar_codigo(chave, padrao)
    contador[codigo] = contador.get(codigo, 0) + 1


def _ordenar_contador(contador: dict[str, int]) -> list[dict]:
    return [
        {"codigo": codigo, "total": total}
        for codigo, total in sorted(contador.items(), key=lambda item: (-item[1], item[0]))
    ]


def _dias_entre(inicio: Any, fim: Any | None = None) -> int | None:
    if not inicio:
        return None
    if isinstance(inicio, date) and not isinstance(inicio, datetime):
        inicio_dt = datetime.combine(inicio, datetime.min.time())
    elif isinstance(inicio, datetime):
        inicio_dt = inicio
    else:
        return None
    fim_dt = fim or datetime.utcnow()
    if isinstance(fim_dt, date) and not isinstance(fim_dt, datetime):
        fim_dt = datetime.combine(fim_dt, datetime.min.time())
    if not isinstance(fim_dt, datetime):
        return None
    return max((fim_dt - inicio_dt).days, 0)


def _calcular_resumo_tempos_prm(registros: list[ProblemaFarmacoterapeutico]) -> dict:
    tempos_resolucao = []
    tempos_aberto = []
    for prm in registros:
        status = _normalizar_codigo(getattr(prm, "status", None))
        inicio = getattr(prm, "data_identificacao", None) or getattr(prm, "criado_em", None)
        if status in ("ABERTO", "EM_ACOMPANHAMENTO"):
            dias = _dias_entre(inicio)
            if dias is not None:
                tempos_aberto.append(dias)
        elif getattr(prm, "data_resolucao", None):
            dias = _dias_entre(inicio, prm.data_resolucao)
            if dias is not None:
                tempos_resolucao.append(dias)
    return {
        "abertos_media_dias": round(sum(tempos_aberto) / len(tempos_aberto), 1) if tempos_aberto else 0,
        "abertos_mediana_dias": median(tempos_aberto) if tempos_aberto else 0,
        "resolucao_media_dias": round(sum(tempos_resolucao) / len(tempos_resolucao), 1) if tempos_resolucao else 0,
        "resolucao_mediana_dias": median(tempos_resolucao) if tempos_resolucao else 0,
    }


def montar_indicadores_prm(db: Session, paciente_id: int | None = None) -> dict:
    """Gera indicadores automáticos a partir dos PRM padronizados.

    Os indicadores contam episódios de PRM, não linhas de evolução. Registros
    legados continuam válidos, mas são sinalizados quando faltam campos
    padronizados para preservar a qualidade analítica.
    """
    query = db.query(ProblemaFarmacoterapeutico)
    if paciente_id is not None:
        query = query.filter(ProblemaFarmacoterapeutico.paciente_clinico_id == paciente_id)
    registros = query.all()

    pacientes_ids = {p.paciente_clinico_id for p in registros if p.paciente_clinico_id}
    pacientes = {}
    if pacientes_ids:
        pacientes = {
            p.id: p
            for p in db.query(PacienteClinico).filter(PacienteClinico.id.in_(pacientes_ids)).all()
        }

    por_categoria: dict[str, int] = {}
    por_subcategoria: dict[str, int] = {}
    por_natureza: dict[str, int] = {}
    por_criticidade: dict[str, int] = {}
    por_status: dict[str, int] = {}
    por_desfecho: dict[str, int] = {}
    por_origem: dict[str, int] = {}
    por_causa: dict[str, int] = {}
    por_categoria_criticidade: dict[str, dict[str, int]] = {}
    pacientes_impactados: dict[int, dict] = {}

    abertos = 0
    em_acompanhamento = 0
    resolvidos = 0
    nao_resolvidos = 0
    invalidos = 0
    sem_desfecho = 0
    potencial = 0
    manifesto = 0
    alta_criticidade = 0
    seguranca_abertos = 0
    adesao_abertos = 0
    legado_nao_padronizado = 0
    abertos_30 = 0
    abertos_60 = 0
    pendencias: list[dict] = []

    for prm in registros:
        categoria = _normalizar_codigo(getattr(prm, "categoria", None))
        subcategoria = _normalizar_codigo(getattr(prm, "subcategoria", None) or getattr(prm, "tipo", None))
        natureza = _normalizar_codigo(getattr(prm, "natureza", None), "MANIFESTO")
        criticidade = _normalizar_codigo(getattr(prm, "criticidade", None) or getattr(prm, "gravidade", None), "MODERADA")
        status = _normalizar_codigo(getattr(prm, "status", None), "ABERTO")
        desfecho = _normalizar_codigo(getattr(prm, "desfecho", None), "NAO_AVALIADO")
        origem = _normalizar_codigo(getattr(prm, "origem", None), "NAO_INFORMADA")
        causa = _normalizar_codigo(getattr(prm, "causa_fator", None), "NAO_INFORMADA")

        _incrementar(por_categoria, categoria)
        _incrementar(por_subcategoria, subcategoria)
        _incrementar(por_natureza, natureza)
        _incrementar(por_criticidade, criticidade)
        _incrementar(por_status, status)
        _incrementar(por_desfecho, desfecho)
        _incrementar(por_origem, origem)
        _incrementar(por_causa, causa)
        por_categoria_criticidade.setdefault(categoria, {})
        _incrementar(por_categoria_criticidade[categoria], criticidade)

        if natureza == "POTENCIAL":
            potencial += 1
        if natureza == "MANIFESTO":
            manifesto += 1
        if criticidade == "ALTA":
            alta_criticidade += 1
        if status == "ABERTO":
            abertos += 1
        if status == "EM_ACOMPANHAMENTO":
            em_acompanhamento += 1
        if status == "RESOLVIDO":
            resolvidos += 1
        if status == "NAO_RESOLVIDO":
            nao_resolvidos += 1
        if status in ("REGISTRO_INVALIDO", "DESCARTADO"):
            invalidos += 1
        if desfecho == "NAO_AVALIADO" and status in ("RESOLVIDO", "NAO_RESOLVIDO"):
            sem_desfecho += 1
        if not getattr(prm, "subcategoria", None) or not getattr(prm, "natureza", None) or not getattr(prm, "criticidade", None):
            legado_nao_padronizado += 1

        ativo = status in ("ABERTO", "EM_ACOMPANHAMENTO")
        if ativo and categoria == "SEGURANCA":
            seguranca_abertos += 1
        if ativo and categoria == "ADESAO":
            adesao_abertos += 1

        inicio = getattr(prm, "data_identificacao", None) or getattr(prm, "criado_em", None)
        dias = _dias_entre(inicio)
        if ativo and dias is not None:
            if dias >= 30:
                abertos_30 += 1
            if dias >= 60:
                abertos_60 += 1
            if dias >= 60 or criticidade == "ALTA" or categoria in ("SEGURANCA", "ADESAO"):
                paciente = pacientes.get(prm.paciente_clinico_id)
                pendencias.append({
                    "prm_id": prm.id,
                    "paciente_id": prm.paciente_clinico_id,
                    "paciente_nome": getattr(paciente, "nome", None),
                    "categoria": categoria,
                    "subcategoria": subcategoria,
                    "natureza": natureza,
                    "criticidade": criticidade,
                    "status": status,
                    "dias_em_aberto": dias,
                    "acao_sugerida": "Revisar PRM, registrar intervenção, meta ou evolução de acompanhamento.",
                })

        if prm.paciente_clinico_id:
            paciente = pacientes.get(prm.paciente_clinico_id)
            item = pacientes_impactados.setdefault(prm.paciente_clinico_id, {
                "paciente_id": prm.paciente_clinico_id,
                "paciente_nome": getattr(paciente, "nome", None),
                "total_prm": 0,
                "abertos": 0,
                "alta_criticidade": 0,
                "seguranca": 0,
                "adesao": 0,
            })
            item["total_prm"] += 1
            if ativo:
                item["abertos"] += 1
            if criticidade == "ALTA":
                item["alta_criticidade"] += 1
            if categoria == "SEGURANCA":
                item["seguranca"] += 1
            if categoria == "ADESAO":
                item["adesao"] += 1

    total = len(registros)
    ativos = abertos + em_acompanhamento
    taxa_resolucao = round((resolvidos / total) * 100, 1) if total else 0
    taxa_padronizacao = round(((total - legado_nao_padronizado) / total) * 100, 1) if total else 0

    top_pacientes = sorted(
        pacientes_impactados.values(),
        key=lambda x: (x["abertos"], x["alta_criticidade"], x["total_prm"]),
        reverse=True,
    )[:10]
    pendencias = sorted(
        pendencias,
        key=lambda x: (
            1 if x["criticidade"] == "ALTA" else 0,
            x["dias_em_aberto"] or 0,
            1 if x["categoria"] == "SEGURANCA" else 0,
        ),
        reverse=True,
    )[:30]

    return {
        "escopo": "paciente" if paciente_id is not None else "global",
        "paciente_id": paciente_id,
        "gerado_em": datetime.utcnow().isoformat(),
        "catalogo": {
            "sistema_codificacao": PRM_SISTEMA_CODIFICACAO,
            "versao": PRM_CATALOGO_VERSAO,
        },
        "resumo": {
            "total_prm": total,
            "ativos": ativos,
            "abertos": abertos,
            "em_acompanhamento": em_acompanhamento,
            "resolvidos": resolvidos,
            "nao_resolvidos": nao_resolvidos,
            "invalidos_ou_descartados": invalidos,
            "alta_criticidade": alta_criticidade,
            "potenciais": potencial,
            "manifestos": manifesto,
            "seguranca_abertos": seguranca_abertos,
            "adesao_abertos": adesao_abertos,
            "abertos_ha_30_dias_ou_mais": abertos_30,
            "abertos_ha_60_dias_ou_mais": abertos_60,
            "sem_desfecho_ao_encerrar": sem_desfecho,
            "registros_legados_nao_padronizados": legado_nao_padronizado,
            "taxa_resolucao_percentual": taxa_resolucao,
            "taxa_padronizacao_percentual": taxa_padronizacao,
        },
        "distribuicoes": {
            "por_categoria": _ordenar_contador(por_categoria),
            "por_subcategoria": _ordenar_contador(por_subcategoria),
            "por_natureza": _ordenar_contador(por_natureza),
            "por_criticidade": _ordenar_contador(por_criticidade),
            "por_status": _ordenar_contador(por_status),
            "por_desfecho": _ordenar_contador(por_desfecho),
            "por_origem": _ordenar_contador(por_origem),
            "por_causa_fator": _ordenar_contador(por_causa),
            "por_categoria_criticidade": {
                categoria: _ordenar_contador(valores)
                for categoria, valores in sorted(por_categoria_criticidade.items())
            },
        },
        "tempos": _calcular_resumo_tempos_prm(registros),
        "pacientes_prioritarios": top_pacientes,
        "pendencias_prm": pendencias,
        "observacoes": [
            "Indicadores contam episódios de PRM e preservam registros legados.",
            "Taxa de padronização considera presença de subcategoria, natureza e criticidade estruturadas.",
        ],
    }

def serializar_meta(meta: MetaTerapeutica) -> dict:
    return {
        "id": meta.id,
        "paciente_clinico_id": meta.paciente_clinico_id,
        "problema_id": meta.problema_id,
        "parametro": meta.parametro,
        "descricao": meta.descricao,
        "valor_alvo": meta.valor_alvo,
        "valor_inicial": meta.valor_inicial,
        "unidade": meta.unidade,
        "prazo": _dt(meta.prazo),
        "status": meta.status,
        "valor_resultado": meta.valor_resultado,
        "resultado_observado": meta.resultado_observado,
        "data_avaliacao": _dt(meta.data_avaliacao),
        "criado_por": meta.criado_por,
        "criado_em": _dt(meta.criado_em),
    }


def serializar_acao(acao: AcaoPlanoCuidado) -> dict:
    return {
        "id": acao.id,
        "paciente_clinico_id": acao.paciente_clinico_id,
        "problema_id": acao.problema_id,
        "meta_id": acao.meta_id,
        "intervencao_farmacoterapia_id": acao.intervencao_farmacoterapia_id,
        "tipo_acao": acao.tipo_acao,
        "descricao": acao.descricao,
        "responsavel": acao.responsavel,
        "prazo": _dt(acao.prazo),
        "prioridade": acao.prioridade,
        "status": acao.status,
        "resultado": acao.resultado,
        "concluido_em": _dt(acao.concluido_em),
        "criado_por": acao.criado_por,
        "criado_em": _dt(acao.criado_em),
    }


def _frequencia_para_doses(frequencia: str | None) -> int:
    if not frequencia:
        return 1
    texto = frequencia.lower()
    if "12" in texto or "2x" in texto or "duas" in texto:
        return 2
    if "8" in texto or "3x" in texto or "três" in texto or "tres" in texto:
        return 3
    if "6" in texto or "4x" in texto or "quatro" in texto:
        return 4
    if "seman" in texto or "mens" in texto or "quando necessário" in texto or "sn" in texto:
        return 0
    return 1


def calcular_complexidade_farmacoterapeutica(paciente_id: int, db: Session, usuario: str | None = None, salvar: bool = False) -> dict:
    medicamentos = db.query(MedicamentoUso).filter(
        MedicamentoUso.paciente_clinico_id == paciente_id,
        MedicamentoUso.ativo == True,
    ).all()
    prms_abertos = db.query(ProblemaFarmacoterapeutico).filter(
        ProblemaFarmacoterapeutico.paciente_clinico_id == paciente_id,
        ProblemaFarmacoterapeutico.status.in_(["ABERTO", "EM_ACOMPANHAMENTO"]),
    ).count()

    total = len(medicamentos)
    uso_continuo = sum(1 for m in medicamentos if m.uso_continuo)
    doses = sum(_frequencia_para_doses(m.frequencia) for m in medicamentos)
    formas = {(_safe_text(m.via) or "NAO_INFORMADA").upper() for m in medicamentos}
    alto_risco = 0
    for m in medicamentos:
        nome = (m.nome_medicamento or "").lower()
        if any(t in nome for t in ALTO_RISCO_TERMO):
            alto_risco += 1

    escore = 0
    escore += total * 2
    escore += max(doses - total, 0)
    escore += len(formas)
    escore += alto_risco * 4
    escore += prms_abertos * 3
    if total >= 5:
        escore += 5
    if total >= 10:
        escore += 5

    if escore < 10:
        classificacao = "BAIXA"
    elif escore < 20:
        classificacao = "MODERADA"
    elif escore < 35:
        classificacao = "ALTA"
    else:
        classificacao = "MUITO_ALTA"

    fatores = []
    if total >= 5:
        fatores.append("Polifarmácia")
    if total >= 10:
        fatores.append("Polifarmácia intensa")
    if doses >= 6:
        fatores.append("Múltiplas tomadas diárias")
    if alto_risco:
        fatores.append("Medicamentos potencialmente de alto risco")
    if prms_abertos:
        fatores.append("PRM pendentes")

    resultado = {
        "paciente_id": paciente_id,
        "total_medicamentos": total,
        "uso_continuo": uso_continuo,
        "doses_diarias_estimadas": doses,
        "formas_farmaceuticas": len(formas),
        "medicamentos_alto_risco": alto_risco,
        "problemas_abertos": prms_abertos,
        "escore": escore,
        "classificacao": classificacao,
        "fatores": fatores,
        "calculado_em": datetime.utcnow().isoformat(),
    }

    if salvar:
        avaliacao = AvaliacaoComplexidadeFarmacoterapeutica(
            paciente_clinico_id=paciente_id,
            total_medicamentos=total,
            uso_continuo=uso_continuo,
            doses_diarias_estimadas=doses,
            formas_farmaceuticas=len(formas),
            medicamentos_alto_risco=alto_risco,
            problemas_abertos=prms_abertos,
            escore=escore,
            classificacao=classificacao,
            fatores="; ".join(fatores),
            calculado_por=usuario,
        )
        db.add(avaliacao)
        db.commit()
        db.refresh(avaliacao)
        resultado["avaliacao_id"] = avaliacao.id

    return resultado


def gerar_sugestoes_cuidado(paciente_id: int, db: Session) -> list[dict]:
    complexidade = calcular_complexidade_farmacoterapeutica(paciente_id, db)
    prms_abertos = db.query(ProblemaFarmacoterapeutico).filter(
        ProblemaFarmacoterapeutico.paciente_clinico_id == paciente_id,
        ProblemaFarmacoterapeutico.status.in_(["ABERTO", "EM_ACOMPANHAMENTO"]),
    ).all()
    medicamentos = db.query(MedicamentoUso).filter(
        MedicamentoUso.paciente_clinico_id == paciente_id,
        MedicamentoUso.ativo == True,
    ).all()

    sugestoes = []
    if complexidade["classificacao"] in ("ALTA", "MUITO_ALTA"):
        sugestoes.append({
            "tipo": "MONITORAMENTO",
            "prioridade": "ALTA",
            "titulo": "Revisar farmacoterapia completa",
            "descricao": "Complexidade farmacoterapêutica elevada; revisar indicação, duplicidades, adesão, segurança e necessidade de seguimento.",
        })
    if len(medicamentos) >= 5:
        sugestoes.append({
            "tipo": "PRM",
            "prioridade": "NORMAL",
            "titulo": "Avaliar polifarmácia",
            "descricao": "Paciente em uso de cinco ou mais medicamentos; investigar interações, duplicidades e dificuldades de uso.",
        })
    if any((m.adesao_referida or "").lower() in ("ruim", "baixa", "irregular") for m in medicamentos):
        sugestoes.append({
            "tipo": "ADESAO",
            "prioridade": "ALTA",
            "titulo": "Construir plano de adesão",
            "descricao": "Há relato de adesão inadequada; registrar PRM de adesão e pactuar meta específica.",
        })
    if prms_abertos:
        sugestoes.append({
            "tipo": "PLANO_CUIDADO",
            "prioridade": "ALTA",
            "titulo": "Vincular PRM a metas e ações",
            "descricao": f"Existem {len(prms_abertos)} PRM abertos/em acompanhamento; cada PRM deve ter ao menos uma meta ou ação de cuidado.",
        })
    return sugestoes



CATEGORIAS_TIMELINE_UNIFICADA = [
    "CEAF",
    "AGENDA",
    "DOCUMENTOS",
    "OCR",
    "CONSULTORIO",
    "FARMACOTERAPIA",
    "PRM",
    "INTERVENCAO",
    "META",
    "PLANO",
    "DESFECHO",
]


def _timeline_data(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    return None


def _timeline_evento(
    *,
    data: Any,
    categoria: str,
    tipo: str,
    titulo: str,
    descricao: Any = None,
    status: Any = None,
    prioridade: Any = None,
    origem: str | None = None,
    referencia_tipo: str | None = None,
    referencia_id: int | None = None,
    detalhes: dict | None = None,
) -> dict | None:
    dt = _timeline_data(data)
    if not dt:
        return None
    categoria_final = (categoria or "OUTROS").upper()
    return {
        "data": dt.isoformat(),
        "data_ordenacao": dt,
        "categoria": categoria_final,
        "tipo": tipo,
        "titulo": titulo,
        "descricao": _safe_text(descricao),
        "status": status,
        "prioridade": prioridade,
        "origem": origem,
        "referencia_tipo": referencia_tipo,
        "referencia_id": referencia_id,
        "detalhes": detalhes or {},
    }


def _adicionar_evento(eventos: list[dict], evento: dict | None) -> None:
    if evento:
        eventos.append(evento)


def montar_timeline_unificada_cuidado(
    paciente_id: int,
    db: Session,
    categorias: list[str] | None = None,
    limite: int = 300,
) -> dict:
    """Monta a timeline única do paciente reunindo CEAF, documentos, agenda e cuidado.

    A função é intencionalmente tolerante: cada bloco consulta apenas tabelas já
    existentes e, se uma relação não tiver dados, simplesmente não gera evento.
    Isso permite reduzir a fragmentação sem remover rotas legadas.
    """
    paciente = db.query(PacienteClinico).filter(PacienteClinico.id == paciente_id).first()
    if not paciente:
        return {"erro": "Paciente clínico não encontrado", "paciente_id": paciente_id}

    eventos: list[dict] = []

    _adicionar_evento(eventos, _timeline_evento(
        data=getattr(paciente, "criado_em", None),
        categoria="CONSULTORIO",
        tipo="PACIENTE_CLINICO",
        titulo="Paciente clínico cadastrado",
        descricao=paciente.nome,
        status="ATIVO" if getattr(paciente, "ativo", True) else "INATIVO",
        origem="pacientes_clinicos",
        referencia_tipo="paciente_clinico",
        referencia_id=paciente.id,
        detalhes={"cid_principal": getattr(paciente, "cid_principal", None), "cns": getattr(paciente, "cns", None)},
    ))

    # Agenda / CEAF
    for ag in db.query(AgendaIntegrada).filter(AgendaIntegrada.paciente_id == paciente_id).all():
        categoria = "CEAF" if str(ag.tipo_evento or "").upper() in {"INCLUSAO", "RENOVACAO", "ADEQUACAO", "ENCERRAMENTO", "RETIRADA"} else "AGENDA"
        _adicionar_evento(eventos, _timeline_evento(
            data=ag.data_evento,
            categoria=categoria,
            tipo=str(ag.tipo_evento or "AGENDA").upper(),
            titulo=ag.titulo or ag.tipo_evento or "Evento de agenda",
            descricao=ag.mensagem_notificacao or ag.observacoes or ag.medicamento,
            status=ag.status,
            prioridade=ag.prioridade,
            origem="agenda_integrada",
            referencia_tipo="agenda_integrada",
            referencia_id=ag.id,
            detalhes={
                "medicamento": ag.medicamento,
                "situacao_laudo": ag.situacao_laudo,
                "vigencia_inicio": _dt(ag.data_inicio_vigencia),
                "vigencia_fim": _dt(ag.data_fim_vigencia),
                "whatsapp": ag.notificar_whatsapp,
            },
        ))

    # Processos documentais e vigências
    processos = db.query(ProcessoDocumental).filter(ProcessoDocumental.paciente_id == paciente_id).all()
    for proc in processos:
        _adicionar_evento(eventos, _timeline_evento(
            data=proc.data_abertura,
            categoria="CEAF",
            tipo=str(proc.tipo_processo or "PROCESSO_DOCUMENTAL").upper(),
            titulo=f"Processo documental: {proc.tipo_processo or 'processo'}",
            descricao=proc.titulo or proc.descricao or proc.pendencias_descricao,
            status=proc.situacao,
            prioridade=proc.prioridade,
            origem="processos_documentais",
            referencia_tipo="processo_documental",
            referencia_id=proc.id,
            detalhes={"vigencia_inicio": _dt(proc.vigencia_inicio), "vigencia_fim": _dt(proc.vigencia_fim), "vigencia_status": proc.vigencia_status},
        ))
        if proc.vigencia_inicio:
            _adicionar_evento(eventos, _timeline_evento(
                data=proc.vigencia_inicio,
                categoria="CEAF",
                tipo="INICIO_VIGENCIA",
                titulo="Início de vigência do laudo",
                descricao=proc.titulo,
                status=proc.vigencia_status,
                origem="processos_documentais",
                referencia_tipo="processo_documental",
                referencia_id=proc.id,
                detalhes={"vigencia_fim": _dt(proc.vigencia_fim)},
            ))
        if proc.vigencia_fim:
            _adicionar_evento(eventos, _timeline_evento(
                data=proc.vigencia_fim,
                categoria="CEAF",
                tipo="FIM_VIGENCIA",
                titulo="Fim de vigência do laudo",
                descricao=proc.titulo,
                status=proc.vigencia_status,
                origem="processos_documentais",
                referencia_tipo="processo_documental",
                referencia_id=proc.id,
            ))

    # Documentos e histórico documental
    documentos = db.query(DocumentoPaciente).filter(DocumentoPaciente.paciente_id == paciente_id).all()
    for doc in documentos:
        _adicionar_evento(eventos, _timeline_evento(
            data=doc.criado_em,
            categoria="DOCUMENTOS",
            tipo="DOCUMENTO_ANEXADO",
            titulo=f"Documento anexado: {doc.tipo_documento}",
            descricao=doc.titulo or doc.nome_arquivo_original,
            status=doc.status_documental or doc.status,
            origem="documentos_pacientes",
            referencia_tipo="documento_paciente",
            referencia_id=doc.id,
            detalhes={"arquivo": doc.nome_arquivo_original, "processo_id": doc.processo_documental_id, "validade": _dt(doc.data_validade)},
        ))
        if doc.status_documental_atualizado_em:
            _adicionar_evento(eventos, _timeline_evento(
                data=doc.status_documental_atualizado_em,
                categoria="DOCUMENTOS",
                tipo="STATUS_DOCUMENTAL",
                titulo=f"Status documental: {doc.status_documental}",
                descricao=doc.status_documental_motivo or doc.titulo or doc.nome_arquivo_original,
                status=doc.status_documental,
                origem="documentos_pacientes",
                referencia_tipo="documento_paciente",
                referencia_id=doc.id,
            ))
        if doc.data_validade:
            _adicionar_evento(eventos, _timeline_evento(
                data=doc.data_validade,
                categoria="DOCUMENTOS",
                tipo="VALIDADE_DOCUMENTO",
                titulo=f"Validade de documento: {doc.tipo_documento}",
                descricao=doc.titulo or doc.nome_arquivo_original,
                status=doc.status_documental or doc.status,
                origem="documentos_pacientes",
                referencia_tipo="documento_paciente",
                referencia_id=doc.id,
            ))

    for hist in db.query(HistoricoStatusDocumento).filter(HistoricoStatusDocumento.paciente_id == paciente_id).all():
        _adicionar_evento(eventos, _timeline_evento(
            data=hist.criado_em,
            categoria="DOCUMENTOS",
            tipo="AUDITORIA_STATUS_DOCUMENTO",
            titulo=f"Documento {hist.status_anterior or '—'} → {hist.status_novo}",
            descricao=hist.motivo,
            status=hist.status_novo,
            origem="historico_status_documentos",
            referencia_tipo="historico_status_documento",
            referencia_id=hist.id,
            detalhes={"documento_id": hist.documento_id, "usuario": hist.usuario, "observacao": hist.observacao},
        ))

    for hist in db.query(HistoricoVigenciaDocumento).filter(HistoricoVigenciaDocumento.paciente_id == paciente_id).all():
        _adicionar_evento(eventos, _timeline_evento(
            data=hist.criado_em,
            categoria="CEAF",
            tipo="AUDITORIA_VIGENCIA",
            titulo="Vigência alterada",
            descricao=hist.motivo,
            status=hist.vigencia_status_nova,
            origem="historico_vigencias_documentos",
            referencia_tipo="historico_vigencia_documento",
            referencia_id=hist.id,
            detalhes={"inicio_anterior": _dt(hist.vigencia_inicio_anterior), "fim_anterior": _dt(hist.vigencia_fim_anterior), "inicio_novo": _dt(hist.vigencia_inicio_nova), "fim_novo": _dt(hist.vigencia_fim_nova)},
        ))

    for ocr in db.query(ExtracaoDocumentoOCR).filter(ExtracaoDocumentoOCR.paciente_id == paciente_id).all():
        _adicionar_evento(eventos, _timeline_evento(
            data=ocr.criado_em,
            categoria="OCR",
            tipo="OCR_EXECUTADO",
            titulo="OCR documental executado",
            descricao=ocr.erro or ("Texto extraído e campos sugeridos gerados" if ocr.texto_extraido else "OCR sem texto extraído"),
            status=ocr.status,
            origem="extracoes_documentos_ocr",
            referencia_tipo="extracao_ocr",
            referencia_id=ocr.id,
            detalhes={"documento_id": ocr.documento_id, "processo_id": ocr.processo_documental_id, "metodo": ocr.metodo},
        ))

    # Consultório e cuidado farmacêutico
    prontuarios = db.query(ProntuarioClinico).filter(ProntuarioClinico.paciente_clinico_id == paciente_id).all()
    prontuario_ids = [p.id for p in prontuarios]
    for p in prontuarios:
        _adicionar_evento(eventos, _timeline_evento(
            data=p.data_abertura,
            categoria="CONSULTORIO",
            tipo="PRONTUARIO_ABERTO",
            titulo="Prontuário farmacêutico aberto",
            descricao=p.observacoes,
            status=p.status,
            origem="prontuarios_clinicos",
            referencia_tipo="prontuario_clinico",
            referencia_id=p.id,
        ))
    if prontuario_ids:
        evolucoes = db.query(EvolucaoClinica).filter(EvolucaoClinica.prontuario_id.in_(prontuario_ids)).all()
        evolucao_ids = [e.id for e in evolucoes]
        for ev in evolucoes:
            _adicionar_evento(eventos, _timeline_evento(
                data=ev.data_evolucao or ev.criado_em,
                categoria="CONSULTORIO",
                tipo="EVOLUCAO_CLINICA",
                titulo=ev.tipo_atendimento or "Evolução clínica",
                descricao=ev.avaliacao_farmaceutica or ev.conduta or ev.queixa_principal,
                status="REGISTRADA",
                origem="evolucoes_clinicas",
                referencia_tipo="evolucao_clinica",
                referencia_id=ev.id,
                detalhes={"necessidade_retorno": ev.necessidade_retorno, "retorno_sugerido": _dt(ev.data_retorno_sugerida)},
            ))
        if evolucao_ids:
            for des in db.query(DesfechoClinico).filter(DesfechoClinico.evolucao_id.in_(evolucao_ids)).all():
                _adicionar_evento(eventos, _timeline_evento(
                    data=des.data_desfecho or des.criado_em,
                    categoria="DESFECHO",
                    tipo="DESFECHO_CLINICO",
                    titulo="Desfecho clínico registrado",
                    descricao=des.resultado_observado or des.observacoes,
                    status="RESOLVIDO" if des.resolucao_problema else des.melhora_clinica,
                    origem="desfechos_clinicos",
                    referencia_tipo="desfecho_clinico",
                    referencia_id=des.id,
                    detalhes={"evolucao_id": des.evolucao_id, "adesao": des.adesao_tratamento, "encaminhamento": des.encaminhamento_realizado},
                ))

    for med in db.query(MedicamentoUso).filter(MedicamentoUso.paciente_clinico_id == paciente_id).all():
        _adicionar_evento(eventos, _timeline_evento(
            data=med.criado_em,
            categoria="FARMACOTERAPIA",
            tipo="MEDICAMENTO_REGISTRADO",
            titulo=med.nome_medicamento,
            descricao=f"{_safe_text(med.dose) or ''} {_safe_text(med.via) or ''} {_safe_text(med.frequencia) or ''}".strip() or med.indicacao,
            status=getattr(med, "status_farmacoterapia", None) or ("ATIVO" if med.ativo else "INATIVO"),
            origem="medicamentos_uso",
            referencia_tipo="medicamento_uso",
            referencia_id=med.id,
            detalhes={
                "indicacao": med.indicacao,
                "uso_continuo": med.uso_continuo,
                "adesao": med.adesao_referida,
                "motivo_status": getattr(med, "motivo_status", None),
                "tipo_suspensao": getattr(med, "tipo_suspensao", None),
                "substituido_por_medicamento_id": getattr(med, "substituido_por_medicamento_id", None),
                "prm_relacionado_id": getattr(med, "prm_relacionado_id", None),
                "intervencao_relacionada_id": getattr(med, "intervencao_relacionada_id", None),
            },
        ))
        if getattr(med, "data_status", None) and (getattr(med, "status_farmacoterapia", None) or "EM_USO") in ("TROCADO", "SUSPENSO", "ENCERRADO"):
            _adicionar_evento(eventos, _timeline_evento(
                data=med.data_status,
                categoria="FARMACOTERAPIA",
                tipo=f"MEDICAMENTO_{med.status_farmacoterapia}",
                titulo=med.nome_medicamento,
                descricao=(getattr(med, "observacao_status", None) or getattr(med, "motivo_status", None)),
                status=med.status_farmacoterapia,
                origem="medicamentos_uso",
                referencia_tipo="medicamento_uso",
                referencia_id=med.id,
                detalhes={
                    "motivo_status": getattr(med, "motivo_status", None),
                    "tipo_suspensao": getattr(med, "tipo_suspensao", None),
                    "substituido_por_medicamento_id": getattr(med, "substituido_por_medicamento_id", None),
                    "prm_relacionado_id": getattr(med, "prm_relacionado_id", None),
                    "intervencao_relacionada_id": getattr(med, "intervencao_relacionada_id", None),
                },
            ))

    for prm in db.query(ProblemaFarmacoterapeutico).filter(ProblemaFarmacoterapeutico.paciente_clinico_id == paciente_id).all():
        _adicionar_evento(eventos, _timeline_evento(
            data=prm.data_identificacao or prm.criado_em,
            categoria="PRM",
            tipo="PRM_IDENTIFICADO",
            titulo=prm.tipo,
            descricao=prm.descricao or prm.evidencias,
            status=prm.status,
            prioridade=prm.gravidade,
            origem="problemas_farmacoterapeuticos",
            referencia_tipo="prm",
            referencia_id=prm.id,
            detalhes={"categoria": prm.categoria, "medicamento_id": prm.medicamento_uso_id, "resolucao": prm.resolucao},
        ))
        if prm.data_resolucao:
            _adicionar_evento(eventos, _timeline_evento(
                data=prm.data_resolucao,
                categoria="DESFECHO",
                tipo="PRM_RESOLVIDO",
                titulo=f"PRM {prm.status.lower()}",
                descricao=prm.resolucao,
                status=prm.status,
                prioridade=prm.gravidade,
                origem="problemas_farmacoterapeuticos",
                referencia_tipo="prm",
                referencia_id=prm.id,
            ))

    intervencoes = db.query(IntervencaoFarmacoterapia).filter(IntervencaoFarmacoterapia.paciente_clinico_id == paciente_id).all()
    intervencao_ids = [i.id for i in intervencoes]
    for i in intervencoes:
        _adicionar_evento(eventos, _timeline_evento(
            data=i.criado_em,
            categoria="INTERVENCAO",
            tipo="INTERVENCAO_FARMACOTERAPEUTICA",
            titulo=i.tipo_intervencao,
            descricao=i.descricao or i.conduta,
            status="ACEITA" if i.aceita_pelo_paciente else "REGISTRADA",
            origem="intervencoes_farmacoterapia",
            referencia_tipo="intervencao_farmacoterapia",
            referencia_id=i.id,
            detalhes={"medicamento_id": i.medicamento_uso_id, "encaminhamento": i.necessidade_encaminhamento, "observacoes": i.observacoes},
        ))
    if intervencao_ids:
        for d in db.query(DesfechoIntervencaoFarmacoterapia).filter(DesfechoIntervencaoFarmacoterapia.intervencao_id.in_(intervencao_ids)).all():
            _adicionar_evento(eventos, _timeline_evento(
                data=d.criado_em,
                categoria="DESFECHO",
                tipo="DESFECHO_INTERVENCAO",
                titulo="Desfecho da intervenção farmacêutica",
                descricao=d.resultado_observado or d.observacoes,
                status=d.status_desfecho,
                origem="desfechos_intervencoes_farmacoterapia",
                referencia_tipo="desfecho_intervencao_farmacoterapia",
                referencia_id=d.id,
                detalhes={"intervencao_id": d.intervencao_id, "necessidade_nova_intervencao": d.necessidade_nova_intervencao},
            ))

    for meta in db.query(MetaTerapeutica).filter(MetaTerapeutica.paciente_clinico_id == paciente_id).all():
        _adicionar_evento(eventos, _timeline_evento(
            data=meta.criado_em,
            categoria="META",
            tipo="META_TERAPEUTICA",
            titulo=meta.parametro,
            descricao=meta.descricao,
            status=meta.status,
            origem="metas_terapeuticas",
            referencia_tipo="meta_terapeutica",
            referencia_id=meta.id,
            detalhes={"valor_inicial": meta.valor_inicial, "valor_alvo": meta.valor_alvo, "unidade": meta.unidade, "prazo": _dt(meta.prazo), "problema_id": meta.problema_id},
        ))
        if meta.data_avaliacao:
            _adicionar_evento(eventos, _timeline_evento(
                data=meta.data_avaliacao,
                categoria="DESFECHO",
                tipo="AVALIACAO_META",
                titulo=f"Avaliação da meta: {meta.parametro}",
                descricao=meta.resultado_observado,
                status=meta.status,
                origem="metas_terapeuticas",
                referencia_tipo="meta_terapeutica",
                referencia_id=meta.id,
                detalhes={"valor_resultado": meta.valor_resultado},
            ))

    for acao in db.query(AcaoPlanoCuidado).filter(AcaoPlanoCuidado.paciente_clinico_id == paciente_id).all():
        _adicionar_evento(eventos, _timeline_evento(
            data=acao.criado_em,
            categoria="PLANO",
            tipo="ACAO_PLANO_CUIDADO",
            titulo=acao.tipo_acao,
            descricao=acao.descricao,
            status=acao.status,
            prioridade=acao.prioridade,
            origem="acoes_plano_cuidado",
            referencia_tipo="acao_plano_cuidado",
            referencia_id=acao.id,
            detalhes={"responsavel": acao.responsavel, "prazo": _dt(acao.prazo), "problema_id": acao.problema_id, "meta_id": acao.meta_id},
        ))
        if acao.concluido_em:
            _adicionar_evento(eventos, _timeline_evento(
                data=acao.concluido_em,
                categoria="DESFECHO",
                tipo="ACAO_CONCLUIDA",
                titulo=f"Ação concluída: {acao.tipo_acao}",
                descricao=acao.resultado or acao.descricao,
                status=acao.status,
                origem="acoes_plano_cuidado",
                referencia_tipo="acao_plano_cuidado",
                referencia_id=acao.id,
            ))

    # Filtros e ordenação
    if categorias:
        categorias_set = {str(c).upper() for c in categorias if str(c).strip()}
        eventos = [e for e in eventos if e.get("categoria") in categorias_set]

    eventos.sort(key=lambda e: e["data_ordenacao"], reverse=True)
    eventos = eventos[: max(1, min(int(limite or 300), 1000))]
    for e in eventos:
        e.pop("data_ordenacao", None)

    resumo_categorias: dict[str, int] = {}
    pendencias = 0
    for e in eventos:
        cat = e.get("categoria") or "OUTROS"
        resumo_categorias[cat] = resumo_categorias.get(cat, 0) + 1
        if str(e.get("status") or "").upper() in {"ABERTO", "EM_ACOMPANHAMENTO", "PENDENTE", "EM_ANDAMENTO", "ATIVA", "REJEITADO", "VENCIDO"}:
            pendencias += 1

    return {
        "paciente": serializar_paciente(paciente),
        "total_eventos": len(eventos),
        "eventos_pendentes_ou_abertos": pendencias,
        "categorias_disponiveis": CATEGORIAS_TIMELINE_UNIFICADA,
        "resumo_por_categoria": resumo_categorias,
        "timeline": eventos,
    }

def montar_timeline_cuidado(paciente_id: int, db: Session) -> list[dict]:
    eventos = []

    for prm in db.query(ProblemaFarmacoterapeutico).filter(ProblemaFarmacoterapeutico.paciente_clinico_id == paciente_id).all():
        eventos.append({"data": _dt(prm.data_identificacao), "tipo": "PRM", "titulo": prm.tipo, "descricao": prm.descricao, "status": prm.status})
    for meta in db.query(MetaTerapeutica).filter(MetaTerapeutica.paciente_clinico_id == paciente_id).all():
        eventos.append({"data": _dt(meta.criado_em), "tipo": "META", "titulo": meta.parametro, "descricao": meta.descricao, "status": meta.status})
    for acao in db.query(AcaoPlanoCuidado).filter(AcaoPlanoCuidado.paciente_clinico_id == paciente_id).all():
        eventos.append({"data": _dt(acao.criado_em), "tipo": "ACAO", "titulo": acao.tipo_acao, "descricao": acao.descricao, "status": acao.status})
    for i in db.query(IntervencaoFarmacoterapia).filter(IntervencaoFarmacoterapia.paciente_clinico_id == paciente_id).all():
        eventos.append({"data": _dt(i.criado_em), "tipo": "INTERVENCAO", "titulo": i.tipo_intervencao, "descricao": i.descricao, "status": "ACEITA" if i.aceita_pelo_paciente else "REGISTRADA"})
    prontuarios = db.query(ProntuarioClinico).filter(ProntuarioClinico.paciente_clinico_id == paciente_id).all()
    prontuario_ids = [p.id for p in prontuarios]
    if prontuario_ids:
        for ev in db.query(EvolucaoClinica).filter(EvolucaoClinica.prontuario_id.in_(prontuario_ids)).all():
            eventos.append({"data": _dt(ev.data_evolucao), "tipo": "EVOLUCAO", "titulo": ev.tipo_atendimento or "Evolução clínica", "descricao": ev.avaliacao_farmaceutica or ev.queixa_principal, "status": "REGISTRADA"})
    for ag in db.query(AgendaIntegrada).filter(AgendaIntegrada.paciente_id == paciente_id).all():
        eventos.append({"data": _dt(ag.data_evento), "tipo": "AGENDA", "titulo": ag.tipo_evento, "descricao": ag.titulo or ag.medicamento, "status": ag.status})
    for proc in db.query(ProcessoDocumental).filter(ProcessoDocumental.paciente_id == paciente_id).all():
        eventos.append({"data": _dt(proc.data_abertura), "tipo": "PROCESSO_DOCUMENTAL", "titulo": proc.tipo_processo, "descricao": proc.titulo, "status": proc.situacao})

    eventos = [e for e in eventos if e.get("data")]
    eventos.sort(key=lambda e: e["data"], reverse=True)
    return eventos[:100]


def montar_resumo_cuidado(paciente_id: int, db: Session) -> dict:
    paciente = db.query(PacienteClinico).filter(PacienteClinico.id == paciente_id).first()
    if not paciente:
        return {"erro": "Paciente clínico não encontrado", "paciente_id": paciente_id}

    medicamentos = db.query(MedicamentoUso).filter(MedicamentoUso.paciente_clinico_id == paciente_id, MedicamentoUso.ativo == True).order_by(MedicamentoUso.nome_medicamento.asc()).all()
    prms = db.query(ProblemaFarmacoterapeutico).filter(ProblemaFarmacoterapeutico.paciente_clinico_id == paciente_id).order_by(ProblemaFarmacoterapeutico.data_identificacao.desc()).all()
    metas = db.query(MetaTerapeutica).filter(MetaTerapeutica.paciente_clinico_id == paciente_id).order_by(MetaTerapeutica.criado_em.desc()).all()
    acoes = db.query(AcaoPlanoCuidado).filter(AcaoPlanoCuidado.paciente_clinico_id == paciente_id).order_by(AcaoPlanoCuidado.criado_em.desc()).all()
    intervencoes = db.query(IntervencaoFarmacoterapia).filter(IntervencaoFarmacoterapia.paciente_clinico_id == paciente_id).order_by(IntervencaoFarmacoterapia.criado_em.desc()).all()
    planos = db.query(PlanoCuidado).filter(PlanoCuidado.paciente_id == paciente_id).order_by(PlanoCuidado.criado_em.desc()).all()

    complexidade = calcular_complexidade_farmacoterapeutica(paciente_id, db)
    sugestoes = gerar_sugestoes_cuidado(paciente_id, db)
    timeline_unificada = montar_timeline_unificada_cuidado(paciente_id, db)

    return {
        "paciente": serializar_paciente(paciente),
        "farmacoterapia": {
            "medicamentos": [serializar_medicamento(m) for m in medicamentos],
            "total_medicamentos": len(medicamentos),
            "complexidade": complexidade,
        },
        "problemas_farmacoterapeuticos": [serializar_prm(p) for p in prms],
        "metas_terapeuticas": [serializar_meta(m) for m in metas],
        "acoes_plano_cuidado": [serializar_acao(a) for a in acoes],
        "intervencoes_farmacoterapia": [
            {"id": i.id, "tipo_intervencao": i.tipo_intervencao, "descricao": i.descricao, "conduta": i.conduta, "aceita_pelo_paciente": i.aceita_pelo_paciente, "criado_em": _dt(i.criado_em)}
            for i in intervencoes
        ],
        "planos_cuidado_legados": [
            {"id": p.id, "problema_identificado": p.problema_identificado, "objetivo_terapeutico": p.objetivo_terapeutico, "status": p.status, "criado_em": _dt(p.criado_em), "prazo_reavaliacao": _dt(p.prazo_reavaliacao)}
            for p in planos
        ],
        "sugestoes": sugestoes,
        "timeline": timeline_unificada.get("timeline", []),
        "timeline_unificada": timeline_unificada,
    }


def montar_dashboard_cuidado(db: Session) -> dict:
    total_pacientes = db.query(PacienteClinico).count()
    prms_abertos = db.query(ProblemaFarmacoterapeutico).filter(ProblemaFarmacoterapeutico.status.in_(["ABERTO", "EM_ACOMPANHAMENTO"])).count()
    metas_ativas = db.query(MetaTerapeutica).filter(MetaTerapeutica.status == "ATIVA").count()
    acoes_pendentes = db.query(AcaoPlanoCuidado).filter(AcaoPlanoCuidado.status.in_(["PENDENTE", "EM_ANDAMENTO"])).count()

    por_categoria = dict(db.query(ProblemaFarmacoterapeutico.categoria, func.count(ProblemaFarmacoterapeutico.id)).group_by(ProblemaFarmacoterapeutico.categoria).all())
    por_gravidade = dict(db.query(ProblemaFarmacoterapeutico.gravidade, func.count(ProblemaFarmacoterapeutico.id)).group_by(ProblemaFarmacoterapeutico.gravidade).all())
    metas_por_status = dict(db.query(MetaTerapeutica.status, func.count(MetaTerapeutica.id)).group_by(MetaTerapeutica.status).all())

    return {
        "total_pacientes_clinicos": total_pacientes,
        "prms_abertos": prms_abertos,
        "metas_ativas": metas_ativas,
        "acoes_pendentes": acoes_pendentes,
        "prm_por_categoria": por_categoria,
        "prm_por_gravidade": por_gravidade,
        "metas_por_status": metas_por_status,
    }
