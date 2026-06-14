"""Rotas da Central de Notificações Internas.

Passo 10D: fornece caixa de entrada operacional para Agenda, Renovações,
Retiradas e demais eventos antes da integração com WhatsApp.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models.consultorio_models import BaseConsultorio, NotificacaoInterna
from database import engine
from routers.consultorio import get_db_consultorio, get_current_user_consultorio, exigir_farmaceutico_ou_admin
from schemas.consultorio_schemas import NotificacaoInternaCreate
from services.notificacoes_internas import (
    TIPOS_NOTIFICACAO,
    PRIORIDADES_NOTIFICACAO,
    ORIGENS_NOTIFICACAO,
    criar_notificacao,
    dashboard_notificacoes,
    gerar_notificacoes_automaticas,
)

BaseConsultorio.metadata.create_all(bind=engine)

router = APIRouter(prefix="/consultorio", tags=["Notificações Internas"])


def _serializar(n: NotificacaoInterna) -> dict:
    return {
        "id": n.id,
        "paciente_id": n.paciente_id,
        "evento_agenda_id": n.evento_agenda_id,
        "tipo": n.tipo,
        "prioridade": n.prioridade,
        "origem": n.origem,
        "titulo": n.titulo,
        "mensagem": n.mensagem,
        "lida": n.lida,
        "necessita_acao": n.necessita_acao,
        "enviada_whatsapp": n.enviada_whatsapp,
        "status_envio_whatsapp": n.status_envio_whatsapp,
        "data_criacao": n.data_criacao,
        "data_leitura": n.data_leitura,
    }


@router.get("/notificacoes/opcoes")
def opcoes_notificacoes(current=Depends(get_current_user_consultorio)):
    return {
        "tipos": TIPOS_NOTIFICACAO,
        "prioridades": PRIORIDADES_NOTIFICACAO,
        "origens": ORIGENS_NOTIFICACAO,
    }


@router.post("/notificacoes/gerar-automaticas")
def gerar_automaticas(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    exigir_farmaceutico_ou_admin(current)
    return gerar_notificacoes_automaticas(db)


@router.get("/notificacoes/dashboard")
def dashboard(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    return dashboard_notificacoes(db)


@router.get("/notificacoes/nao-lidas")
def listar_nao_lidas(
    limite: int = 100,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    itens = db.query(NotificacaoInterna).filter(
        NotificacaoInterna.lida == False  # noqa: E712
    ).order_by(
        NotificacaoInterna.prioridade.desc(),
        NotificacaoInterna.data_criacao.desc(),
    ).limit(max(1, min(limite, 500))).all()
    return {"total": len(itens), "notificacoes": [_serializar(n) for n in itens]}


@router.get("/notificacoes")
def listar_notificacoes(
    lida: Optional[bool] = None,
    prioridade: Optional[str] = None,
    tipo: Optional[str] = None,
    necessita_acao: Optional[bool] = None,
    limite: int = 100,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    query = db.query(NotificacaoInterna)
    if lida is not None:
        query = query.filter(NotificacaoInterna.lida == lida)
    if prioridade:
        query = query.filter(NotificacaoInterna.prioridade == prioridade.upper())
    if tipo:
        query = query.filter(NotificacaoInterna.tipo == tipo.upper())
    if necessita_acao is not None:
        query = query.filter(NotificacaoInterna.necessita_acao == necessita_acao)

    itens = query.order_by(NotificacaoInterna.data_criacao.desc()).limit(max(1, min(limite, 500))).all()
    return {"total": len(itens), "notificacoes": [_serializar(n) for n in itens]}


@router.post("/notificacoes")
def criar_manual(
    dados: NotificacaoInternaCreate,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    exigir_farmaceutico_ou_admin(current)
    notificacao = criar_notificacao(
        db,
        tipo=dados.tipo,
        prioridade=dados.prioridade or "NORMAL",
        origem=dados.origem or "MANUAL",
        titulo=dados.titulo,
        mensagem=dados.mensagem,
        paciente_id=dados.paciente_id,
        evento_agenda_id=dados.evento_agenda_id,
        necessita_acao=bool(dados.necessita_acao),
        evitar_duplicidade=False,
    )
    db.commit()
    db.refresh(notificacao)
    return {"mensagem": "Notificação criada", "notificacao": _serializar(notificacao)}


@router.put("/notificacoes/{notificacao_id}/marcar-lida")
def marcar_lida(
    notificacao_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    notificacao = db.query(NotificacaoInterna).filter(NotificacaoInterna.id == notificacao_id).first()
    if not notificacao:
        raise HTTPException(status_code=404, detail="Notificação não encontrada")
    notificacao.lida = True
    notificacao.data_leitura = datetime.utcnow()
    db.commit()
    db.refresh(notificacao)
    return {"mensagem": "Notificação marcada como lida", "notificacao": _serializar(notificacao)}


@router.put("/notificacoes/marcar-todas-lidas")
def marcar_todas_lidas(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    agora = datetime.utcnow()
    notificacoes = db.query(NotificacaoInterna).filter(NotificacaoInterna.lida == False).all()  # noqa: E712
    for notificacao in notificacoes:
        notificacao.lida = True
        notificacao.data_leitura = agora
    db.commit()
    return {"mensagem": "Notificações marcadas como lidas", "total": len(notificacoes)}
