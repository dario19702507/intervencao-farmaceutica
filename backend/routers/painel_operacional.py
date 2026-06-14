"""Painel operacional da Farmácia Escola.

Passo 13A: consolida em um único endpoint os principais sinais da rotina
operacional: agenda, retiradas, vencimentos de vigência, processos
incompletos, documentos rejeitados, notificações e fila WhatsApp.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from database import engine
from models.consultorio_models import (
    AgendaIntegrada,
    BaseConsultorio,
    DocumentoPaciente,
    NotificacaoInterna,
    PacienteClinico,
    ProcessoDocumental,
    WhatsAppEnvio,
)
from routers.consultorio import get_current_user_consultorio, get_db_consultorio

BaseConsultorio.metadata.create_all(bind=engine)

router = APIRouter(prefix="/consultorio", tags=["Painel Operacional"])

STATUS_FINALIZADOS_AGENDA = {"REALIZADO", "CANCELADO", "CANCELADA", "CONCLUIDO", "CONCLUÍDO"}
STATUS_PROCESSO_FINAL = {"ENCERRADO", "DEFERIDO", "INDEFERIDO"}
DOCUMENTOS_RECOMENDADOS = {
    "INCLUSAO": ["LAUDO", "RECEITA", "EXAME", "DOCUMENTO_PESSOAL", "TERMO"],
    "RENOVACAO": ["LAUDO", "RECEITA", "EXAME", "TERMO"],
    "ADEQUACAO": ["LAUDO", "RECEITA", "EXAME", "TERMO"],
    "ENCERRAMENTO": ["OUTRO"],
}
DOCUMENTOS_EQUIVALENTES = {
    "LAUDO": {"LAUDO"},
    "RECEITA": {"RECEITA"},
    "EXAME": {"EXAME", "EXAME_LABORATORIAL", "ESPIROMETRIA"},
    "DOCUMENTO_PESSOAL": {"DOCUMENTO_PESSOAL"},
    "TERMO": {"TERMO", "TERMO_ESCLARECIMENTO"},
    "OUTRO": {"OUTRO", "OUTROS"},
}


def _iso_data(valor: Any) -> str | None:
    if not valor:
        return None
    return valor.isoformat() if hasattr(valor, "isoformat") else str(valor)


def _status_agenda_pendente():
    return ~func.upper(func.coalesce(AgendaIntegrada.status, "")).in_(STATUS_FINALIZADOS_AGENDA)


def _status_processo_aberto():
    return ~func.upper(func.coalesce(ProcessoDocumental.situacao, "")).in_(STATUS_PROCESSO_FINAL)


def _nome_paciente(db: Session, paciente_id: int | None, fallback: str | None = None) -> str | None:
    if not paciente_id:
        return fallback
    paciente = db.query(PacienteClinico).filter(PacienteClinico.id == paciente_id).first()
    return getattr(paciente, "nome", None) or fallback


def _serializar_evento(evento: AgendaIntegrada) -> dict:
    return {
        "id": evento.id,
        "tipo_evento": evento.tipo_evento,
        "titulo": evento.titulo,
        "paciente_id": evento.paciente_id,
        "paciente_nome": evento.paciente_nome,
        "medicamento": evento.medicamento,
        "data_evento": _iso_data(evento.data_evento),
        "prioridade": evento.prioridade,
        "status": evento.status,
        "referencia_tipo": evento.referencia_tipo,
        "referencia_id": evento.referencia_id,
    }


def _serializar_processo(db: Session, processo: ProcessoDocumental) -> dict:
    return {
        "id": processo.id,
        "paciente_id": processo.paciente_id,
        "paciente_nome": _nome_paciente(db, processo.paciente_id),
        "tipo_processo": processo.tipo_processo,
        "titulo": processo.titulo,
        "situacao": processo.situacao,
        "prioridade": processo.prioridade,
        "data_abertura": _iso_data(processo.data_abertura),
        "vigencia_inicio": _iso_data(processo.vigencia_inicio),
        "vigencia_fim": _iso_data(processo.vigencia_fim),
        "pendencias_descricao": processo.pendencias_descricao,
    }


def _serializar_documento(db: Session, doc: DocumentoPaciente) -> dict:
    return {
        "id": doc.id,
        "paciente_id": doc.paciente_id,
        "paciente_nome": _nome_paciente(db, doc.paciente_id),
        "processo_documental_id": getattr(doc, "processo_documental_id", None),
        "tipo_documento": doc.tipo_documento,
        "titulo": doc.titulo,
        "nome_arquivo_original": doc.nome_arquivo_original,
        "status_documental": getattr(doc, "status_documental", None),
        "status_documental_motivo": getattr(doc, "status_documental_motivo", None),
        "data_validade": _iso_data(doc.data_validade),
        "criado_em": _iso_data(doc.criado_em),
    }


def _processo_incompleto(db: Session, processo: ProcessoDocumental) -> tuple[bool, list[str]]:
    obrigatorios = DOCUMENTOS_RECOMENDADOS.get((processo.tipo_processo or "").upper(), [])
    if not obrigatorios:
        return False, []

    documentos = db.query(DocumentoPaciente).filter(
        DocumentoPaciente.processo_documental_id == processo.id,
        DocumentoPaciente.ativo == True,  # noqa: E712
        func.upper(func.coalesce(DocumentoPaciente.status_documental, "RECEBIDO")) == "VALIDADO",
    ).all()
    tipos_validos = {(doc.tipo_documento or "").upper().strip() for doc in documentos if doc.tipo_documento}

    pendentes: list[str] = []
    for tipo in obrigatorios:
        equivalentes = DOCUMENTOS_EQUIVALENTES.get(tipo, {tipo})
        if not (equivalentes & tipos_validos):
            pendentes.append(tipo)
    return bool(pendentes), pendentes


def _coletar_processos_incompletos(db: Session, limite: int = 10) -> list[dict]:
    processos = db.query(ProcessoDocumental).filter(_status_processo_aberto()).order_by(ProcessoDocumental.atualizado_em.desc()).all()
    resultado: list[dict] = []
    for processo in processos:
        incompleto, pendentes = _processo_incompleto(db, processo)
        if incompleto:
            item = _serializar_processo(db, processo)
            item["documentos_pendentes"] = pendentes
            resultado.append(item)
        if len(resultado) >= limite:
            break
    return resultado


@router.get("/painel-operacional")
def painel_operacional(
    db: Session = Depends(get_db_consultorio),
    current_user=Depends(get_current_user_consultorio),
):
    hoje = date.today()
    amanha = hoje + timedelta(days=1)
    em_60_dias = hoje + timedelta(days=60)

    eventos_hoje_q = db.query(AgendaIntegrada).filter(AgendaIntegrada.data_evento == hoje, _status_agenda_pendente())
    eventos_amanha_q = db.query(AgendaIntegrada).filter(AgendaIntegrada.data_evento == amanha, _status_agenda_pendente())
    retiradas_hoje_q = eventos_hoje_q.filter(func.upper(func.coalesce(AgendaIntegrada.tipo_evento, "")) == "RETIRADA")
    retiradas_atrasadas_q = db.query(AgendaIntegrada).filter(
        AgendaIntegrada.data_evento < hoje,
        func.upper(func.coalesce(AgendaIntegrada.tipo_evento, "")) == "RETIRADA",
        _status_agenda_pendente(),
    )

    laudos_vencendo_q = db.query(ProcessoDocumental).filter(
        ProcessoDocumental.vigencia_fim != None,  # noqa: E711
        ProcessoDocumental.vigencia_fim >= hoje,
        ProcessoDocumental.vigencia_fim <= em_60_dias,
        _status_processo_aberto(),
    )
    laudos_vencidos_q = db.query(ProcessoDocumental).filter(
        ProcessoDocumental.vigencia_fim != None,  # noqa: E711
        ProcessoDocumental.vigencia_fim < hoje,
        _status_processo_aberto(),
    )

    docs_rejeitados_q = db.query(DocumentoPaciente).filter(
        DocumentoPaciente.ativo == True,  # noqa: E712
        func.upper(func.coalesce(DocumentoPaciente.status_documental, "")) == "REJEITADO",
    )

    notificacoes_nao_lidas_q = db.query(NotificacaoInterna).filter(NotificacaoInterna.lida == False)  # noqa: E712
    notificacoes_urgentes_q = notificacoes_nao_lidas_q.filter(func.upper(func.coalesce(NotificacaoInterna.prioridade, "")) == "URGENTE")
    whatsapp_pendente_q = db.query(WhatsAppEnvio).filter(func.upper(func.coalesce(WhatsAppEnvio.status, "")) == "PENDENTE")

    processos_incompletos = _coletar_processos_incompletos(db, limite=10)

    return {
        "data_referencia": hoje.isoformat(),
        "resumo": {
            "eventos_hoje": eventos_hoje_q.count(),
            "eventos_amanha": eventos_amanha_q.count(),
            "retiradas_hoje": retiradas_hoje_q.count(),
            "retiradas_atrasadas": retiradas_atrasadas_q.count(),
            "laudos_vencendo_60_dias": laudos_vencendo_q.count(),
            "laudos_vencidos": laudos_vencidos_q.count(),
            "processos_incompletos": len(processos_incompletos),
            "documentos_rejeitados": docs_rejeitados_q.count(),
            "notificacoes_nao_lidas": notificacoes_nao_lidas_q.count(),
            "notificacoes_urgentes": notificacoes_urgentes_q.count(),
            "whatsapp_pendentes": whatsapp_pendente_q.count(),
        },
        "listas": {
            "eventos_hoje": [_serializar_evento(e) for e in eventos_hoje_q.order_by(AgendaIntegrada.prioridade.desc(), AgendaIntegrada.id.desc()).limit(10).all()],
            "eventos_amanha": [_serializar_evento(e) for e in eventos_amanha_q.order_by(AgendaIntegrada.prioridade.desc(), AgendaIntegrada.id.desc()).limit(10).all()],
            "retiradas_atrasadas": [_serializar_evento(e) for e in retiradas_atrasadas_q.order_by(AgendaIntegrada.data_evento.asc()).limit(10).all()],
            "laudos_vencendo": [_serializar_processo(db, p) for p in laudos_vencendo_q.order_by(ProcessoDocumental.vigencia_fim.asc()).limit(10).all()],
            "laudos_vencidos": [_serializar_processo(db, p) for p in laudos_vencidos_q.order_by(ProcessoDocumental.vigencia_fim.asc()).limit(10).all()],
            "processos_incompletos": processos_incompletos,
            "documentos_rejeitados": [_serializar_documento(db, d) for d in docs_rejeitados_q.order_by(DocumentoPaciente.status_documental_atualizado_em.desc()).limit(10).all()],
        },
        "regras": {
            "documentos": "Processos documentais contam como completos apenas com documentos obrigatórios VALIDADOS.",
            "whatsapp_documental": "Pendências documentais não geram WhatsApp automático; envio documental permanece manual.",
            "agenda": "Retiradas e vencimentos respeitam a agenda inteligente e os dias de atendimento da Farmácia Escola.",
        },
    }
