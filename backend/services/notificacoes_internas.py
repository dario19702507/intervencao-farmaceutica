"""Central de notificações internas da Agenda.

Passo 10D: cria notificações operacionais reutilizáveis pelo sistema e, futuramente,
pelo envio via WhatsApp.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Dict, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.consultorio_models import AgendaIntegrada, NotificacaoInterna
from services.agenda_inteligente import calcular_data_alerta_renovacao, calcular_data_risco_pos_vencimento

TIPOS_NOTIFICACAO = [
    "AGENDA",
    "RETIRADA",
    "RENOVACAO",
    "ADEQUACAO",
    "INCLUSAO",
    "ENCERRAMENTO",
    "SISTEMA",
]

PRIORIDADES_NOTIFICACAO = ["NORMAL", "IMPORTANTE", "URGENTE"]
ORIGENS_NOTIFICACAO = ["MANUAL", "AUTOMATICA", "SISTEMA", "WHATSAPP"]

STATUS_ATIVOS_AGENDA = ["AGENDADO", "agendado", "notificado", "reagendado"]


def _normalizar(valor: Optional[str], padrao: str) -> str:
    return (valor or padrao).strip().upper()


def criar_notificacao(
    db: Session,
    *,
    tipo: str,
    prioridade: str,
    titulo: str,
    mensagem: str,
    paciente_id: Optional[int] = None,
    evento_agenda_id: Optional[int] = None,
    origem: str = "AUTOMATICA",
    necessita_acao: bool = False,
    evitar_duplicidade: bool = True,
) -> Optional[NotificacaoInterna]:
    tipo = _normalizar(tipo, "SISTEMA")
    prioridade = _normalizar(prioridade, "NORMAL")
    origem = _normalizar(origem, "AUTOMATICA")

    if evitar_duplicidade and evento_agenda_id:
        existente = db.query(NotificacaoInterna).filter(
            NotificacaoInterna.evento_agenda_id == evento_agenda_id,
            NotificacaoInterna.tipo == tipo,
            NotificacaoInterna.prioridade == prioridade,
            NotificacaoInterna.lida == False,  # noqa: E712
        ).first()
        if existente:
            return None

    notificacao = NotificacaoInterna(
        paciente_id=paciente_id,
        evento_agenda_id=evento_agenda_id,
        tipo=tipo,
        prioridade=prioridade,
        origem=origem,
        titulo=titulo,
        mensagem=mensagem,
        lida=False,
        necessita_acao=necessita_acao,
    )
    db.add(notificacao)
    return notificacao


def gerar_notificacoes_automaticas(db: Session, data_referencia: Optional[date] = None) -> Dict[str, int]:
    """Gera notificações internas a partir da Agenda.

    Regras oficiais:
    - Evento de hoje: NORMAL.
    - Retirada atrasada: IMPORTANTE.
    - Renovação: IMPORTANTE a partir do segundo mês anterior ao vencimento.
    - Laudo não renovado: URGENTE no primeiro dia útil após o vencimento.
    """

    hoje = data_referencia or date.today()
    amanha = hoje + timedelta(days=1)
    fim_semana = hoje + timedelta(days=7)
    criadas = 0
    ignoradas = 0

    eventos = db.query(AgendaIntegrada).all()

    for evento in eventos:
        status = _normalizar(evento.status, "AGENDADO")
        tipo_evento = _normalizar(evento.tipo_evento, "AGENDA")
        if status in {"REALIZADO", "CANCELADO"}:
            continue

        antes = criadas

        if evento.data_evento == hoje:
            if criar_notificacao(
                db,
                tipo="AGENDA",
                prioridade="NORMAL",
                titulo=f"Evento de hoje: {evento.titulo or tipo_evento}",
                mensagem=f"Há evento agendado para hoje para {evento.paciente_nome}.",
                paciente_id=evento.paciente_id,
                evento_agenda_id=evento.id,
                necessita_acao=False,
            ):
                criadas += 1

        if evento.data_evento == amanha:
            if criar_notificacao(
                db,
                tipo="AGENDA",
                prioridade="NORMAL",
                titulo=f"Evento amanhã: {evento.titulo or tipo_evento}",
                mensagem=f"Há evento agendado para amanhã para {evento.paciente_nome}.",
                paciente_id=evento.paciente_id,
                evento_agenda_id=evento.id,
                necessita_acao=False,
            ):
                criadas += 1

        if hoje < evento.data_evento <= fim_semana:
            if criar_notificacao(
                db,
                tipo="AGENDA",
                prioridade="NORMAL",
                titulo=f"Evento na semana: {evento.titulo or tipo_evento}",
                mensagem=f"Há evento agendado nesta semana para {evento.paciente_nome}.",
                paciente_id=evento.paciente_id,
                evento_agenda_id=evento.id,
                necessita_acao=False,
            ):
                criadas += 1

        if tipo_evento == "RETIRADA" and evento.data_evento < hoje:
            if criar_notificacao(
                db,
                tipo="RETIRADA",
                prioridade="IMPORTANTE",
                titulo="Retirada atrasada",
                mensagem=f"Retirada de {evento.medicamento or 'medicamento'} em atraso para {evento.paciente_nome}.",
                paciente_id=evento.paciente_id,
                evento_agenda_id=evento.id,
                necessita_acao=True,
            ):
                criadas += 1

        if tipo_evento == "RENOVACAO" and evento.data_fim_vigencia and not evento.renovado:
            data_importante = calcular_data_alerta_renovacao(evento.data_fim_vigencia)
            data_urgente = calcular_data_risco_pos_vencimento(evento.data_fim_vigencia)

            if hoje >= data_importante and hoje < data_urgente:
                if criar_notificacao(
                    db,
                    tipo="RENOVACAO",
                    prioridade="IMPORTANTE",
                    titulo="Renovação pendente",
                    mensagem=(
                        f"Laudo de {evento.paciente_nome} vence em {evento.data_fim_vigencia.strftime('%d/%m/%Y')}. "
                        "Iniciar/acompanhar renovação."
                    ),
                    paciente_id=evento.paciente_id,
                    evento_agenda_id=evento.id,
                    necessita_acao=True,
                ):
                    criadas += 1

            if hoje >= data_urgente:
                if criar_notificacao(
                    db,
                    tipo="RENOVACAO",
                    prioridade="URGENTE",
                    titulo="Laudo vencido sem renovação",
                    mensagem=(
                        f"Laudo de {evento.paciente_nome} venceu em {evento.data_fim_vigencia.strftime('%d/%m/%Y')} "
                        "e não há renovação registrada. Ação imediata recomendada."
                    ),
                    paciente_id=evento.paciente_id,
                    evento_agenda_id=evento.id,
                    necessita_acao=True,
                ):
                    criadas += 1

        if criadas == antes:
            ignoradas += 1

    db.commit()
    return {"criadas": criadas, "ignoradas": ignoradas}


def dashboard_notificacoes(db: Session) -> Dict[str, int]:
    total = db.query(NotificacaoInterna).count()
    nao_lidas = db.query(NotificacaoInterna).filter(NotificacaoInterna.lida == False).count()  # noqa: E712
    normais = db.query(NotificacaoInterna).filter(NotificacaoInterna.prioridade == "NORMAL").count()
    importantes = db.query(NotificacaoInterna).filter(NotificacaoInterna.prioridade == "IMPORTANTE").count()
    urgentes = db.query(NotificacaoInterna).filter(NotificacaoInterna.prioridade == "URGENTE").count()
    retiradas_atrasadas = db.query(NotificacaoInterna).filter(NotificacaoInterna.tipo == "RETIRADA", NotificacaoInterna.lida == False).count()  # noqa: E712
    renovacoes_pendentes = db.query(NotificacaoInterna).filter(NotificacaoInterna.tipo == "RENOVACAO", NotificacaoInterna.lida == False).count()  # noqa: E712
    necessita_acao = db.query(NotificacaoInterna).filter(NotificacaoInterna.necessita_acao == True, NotificacaoInterna.lida == False).count()  # noqa: E712

    return {
        "total": total,
        "nao_lidas": nao_lidas,
        "normais": normais,
        "importantes": importantes,
        "urgentes": urgentes,
        "retiradas_atrasadas": retiradas_atrasadas,
        "renovacoes_pendentes": renovacoes_pendentes,
        "necessita_acao": necessita_acao,
    }
