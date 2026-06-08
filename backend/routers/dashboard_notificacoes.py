from datetime import date, datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from datetime import timedelta

from routers.consultorio import (
    NotificacaoAgenda,
    AgendaIntegrada,
    PacienteAgenda,
    get_db_consultorio,
    get_current_user_consultorio,
)

from routers.utils_prioridade import (
    classificar_prioridade,
    prioridade_visual,
    peso_prioridade,
)

router = APIRouter(
    prefix="/consultorio/dashboard-notificacoes",
    tags=["Dashboard Notificações"]
)

@router.get("")
def dashboard_notificacoes(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    hoje = date.today()

    return {
        "retiradas_hoje": db.query(AgendaIntegrada)
            .filter(
                AgendaIntegrada.data_evento == hoje,
                AgendaIntegrada.servico_origem == "dispensacao"
            ).count(),

        "notificacoes_pendentes": db.query(NotificacaoAgenda)
            .filter(NotificacaoAgenda.status == "pendente")
            .count(),

        "notificacoes_enviadas": db.query(NotificacaoAgenda)
            .filter(NotificacaoAgenda.status == "enviada")
            .count(),

        "notificacoes_erro": db.query(NotificacaoAgenda)
            .filter(NotificacaoAgenda.status == "erro")
            .count(),

        "renovacoes_urgentes": db.query(AgendaIntegrada)
            .filter(
                AgendaIntegrada.status == "renovacao_urgente"
            ).count(),

        "risco_interrupcao": db.query(AgendaIntegrada)
            .filter(
                AgendaIntegrada.status == "risco_interrupcao_tratamento"
            ).count(),
    }

def montar_item_priorizado(item):

    risco = (
        getattr(item, "status", None)
        == "risco_interrupcao_tratamento"
    )

    prioridade = classificar_prioridade(
        data_retirada=getattr(item, "data_evento", None),
        data_fim_vigencia=getattr(item, "data_fim_vigencia", None),
        risco_interrupcao=risco,
    )

    return {
        "id": item.id,
        "paciente_nome": getattr(item, "paciente_nome", ""),
        "medicamento": getattr(item, "medicamento", None),
        "data_evento": getattr(item, "data_evento", None),
        "data_fim_vigencia": getattr(item, "data_fim_vigencia", None),
        "status": getattr(item, "status", None),
        "prioridade": prioridade,
        "prioridade_visual": prioridade_visual(prioridade),
        "peso_prioridade": peso_prioridade(prioridade),
    }

def ordenar_por_prioridade(lista):
    return sorted(
        lista,
        key=lambda x: (
            x.get("peso_prioridade", 99),
            x.get("paciente_nome") or "",
        )
    )

@router.get("/painel-operacional")
def painel_operacional_notificacoes(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    hoje = date.today()
    amanha = hoje + timedelta(days=1)
    limite_30_dias = hoje + timedelta(days=30)

    retiradas_hoje = db.query(AgendaIntegrada).filter(
        AgendaIntegrada.servico_origem == "dispensacao",
        AgendaIntegrada.data_evento == hoje,
        AgendaIntegrada.status == "agendado",
    ).order_by(AgendaIntegrada.paciente_nome.asc()).all()

    retiradas_amanha = db.query(AgendaIntegrada).filter(
        AgendaIntegrada.servico_origem == "dispensacao",
        AgendaIntegrada.data_evento == amanha,
        AgendaIntegrada.status == "agendado",
    ).order_by(AgendaIntegrada.paciente_nome.asc()).all()

    renovacoes_30_dias = db.query(AgendaIntegrada).filter(
        AgendaIntegrada.data_fim_vigencia.isnot(None),
        AgendaIntegrada.data_fim_vigencia >= hoje,
        AgendaIntegrada.data_fim_vigencia <= limite_30_dias,
    ).order_by(AgendaIntegrada.data_fim_vigencia.asc()).all()

    risco_interrupcao = db.query(AgendaIntegrada).filter(
        AgendaIntegrada.status == "risco_interrupcao_tratamento",
    ).order_by(AgendaIntegrada.data_evento.asc()).all()

    notificacoes_pendentes = db.query(NotificacaoAgenda).filter(
        NotificacaoAgenda.status == "pendente",
    ).order_by(
        NotificacaoAgenda.data_programada.asc(),
        NotificacaoAgenda.paciente_nome.asc(),
    ).all()

    return {
        "data_referencia": hoje,
        "resumo": {
            "retiradas_hoje": len(retiradas_hoje),
            "retiradas_amanha": len(retiradas_amanha),
            "renovacoes_30_dias": len(renovacoes_30_dias),
            "risco_interrupcao": len(risco_interrupcao),
            "notificacoes_pendentes": len(notificacoes_pendentes),
        },
        "retiradas_hoje": ordenar_por_prioridade([
            montar_item_priorizado(x)
            for x in retiradas_hoje
        ]),

        "retiradas_amanha": ordenar_por_prioridade([
            montar_item_priorizado(x)
            for x in retiradas_amanha
        ]),

        "renovacoes_30_dias": ordenar_por_prioridade([
            montar_item_priorizado(x)
            for x in renovacoes_30_dias
        ]),

        "risco_interrupcao": ordenar_por_prioridade([
            montar_item_priorizado(x)
            for x in risco_interrupcao
        ]),
    }

@router.get("/painel-gerencial")
def painel_gerencial_notificacoes(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    hoje = date.today()

    inicio_mes = hoje.replace(day=1)

    total_pacientes = db.query(PacienteAgenda).count()

    retiradas_mes = db.query(AgendaIntegrada).filter(
        AgendaIntegrada.tipo_evento == "retirada_medicamento",
        AgendaIntegrada.data_evento >= inicio_mes,
    ).count()

    renovacoes_mes = db.query(AgendaIntegrada).filter(
        AgendaIntegrada.tipo_evento == "renovacao",
        AgendaIntegrada.data_evento >= inicio_mes,
    ).count()

    adequacoes_mes = db.query(AgendaIntegrada).filter(
        AgendaIntegrada.tipo_evento == "adequacao",
        AgendaIntegrada.data_evento >= inicio_mes,
    ).count()

    notificacoes_geradas = db.query(NotificacaoAgenda).count()

    notificacoes_enviadas = db.query(NotificacaoAgenda).filter(
        NotificacaoAgenda.status == "enviada"
    ).count()

    notificacoes_pendentes = db.query(NotificacaoAgenda).filter(
        NotificacaoAgenda.status == "pendente"
    ).count()

    notificacoes_erro = db.query(NotificacaoAgenda).filter(
        NotificacaoAgenda.status == "erro"
    ).count()

    taxa_envio = 0

    if notificacoes_geradas > 0:
        taxa_envio = round(
            (notificacoes_enviadas / notificacoes_geradas) * 100,
            2
        )

    criticos = 0
    altos = 0
    moderados = 0
    baixos = 0

    agenda = db.query(AgendaIntegrada).all()

    for item in agenda:

        prioridade = classificar_prioridade(
            data_retirada=item.data_evento,
            data_fim_vigencia=getattr(
                item,
                "data_fim_vigencia",
                None
            ),
            risco_interrupcao=(
                item.status == "risco_interrupcao_tratamento"
            )
        )

        if prioridade == "CRITICO":
            criticos += 1
        elif prioridade == "ALTO":
            altos += 1
        elif prioridade == "MODERADO":
            moderados += 1
        else:
            baixos += 1

    return {
        "data_referencia": hoje,

        "pacientes": {
            "total": total_pacientes
        },

        "movimentacao_mes": {
            "retiradas": retiradas_mes,
            "renovacoes": renovacoes_mes,
            "adequacoes": adequacoes_mes,
        },

        "notificacoes": {
            "geradas": notificacoes_geradas,
            "enviadas": notificacoes_enviadas,
            "pendentes": notificacoes_pendentes,
            "erro": notificacoes_erro,
            "taxa_envio": taxa_envio,
        },

        "prioridades": {
            "criticos": criticos,
            "altos": altos,
            "moderados": moderados,
            "baixos": baixos,
        }
    }
