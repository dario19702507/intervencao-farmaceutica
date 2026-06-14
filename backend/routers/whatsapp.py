"""Rotas da camada preparatória de WhatsApp.

Passo 10E: fila, dashboard e simulação de envio. Não realiza envio externo ainda.
"""

from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import engine
from models.consultorio_models import BaseConsultorio, WhatsAppEnvio
from routers.consultorio import get_db_consultorio, get_current_user_consultorio, exigir_farmaceutico_ou_admin
from schemas.consultorio_schemas import WhatsAppEnvioManualCreate
from services.whatsapp_service import (
    STATUS_WHATSAPP,
    PROVEDORES_WHATSAPP,
    ORIGENS_WHATSAPP,
    criar_envio_manual,
    dashboard_whatsapp,
    enfileirar_notificacoes_pendentes,
    serializar_envio,
    simular_envios_pendentes,
)

BaseConsultorio.metadata.create_all(bind=engine)

router = APIRouter(prefix="/consultorio", tags=["WhatsApp"])


@router.get("/whatsapp/opcoes")
def opcoes_whatsapp(current=Depends(get_current_user_consultorio)):
    return {"status": STATUS_WHATSAPP, "provedores": PROVEDORES_WHATSAPP, "origens": ORIGENS_WHATSAPP}


@router.get("/whatsapp/dashboard")
def dashboard(db: Session = Depends(get_db_consultorio), current=Depends(get_current_user_consultorio)):
    return dashboard_whatsapp(db)


@router.get("/whatsapp/fila")
def listar_fila(
    status: Optional[str] = None,
    prioridade: Optional[str] = None,
    limite: int = 100,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    query = db.query(WhatsAppEnvio)
    if status:
        query = query.filter(WhatsAppEnvio.status == status.upper())
    if prioridade:
        query = query.filter(WhatsAppEnvio.prioridade == prioridade.upper())
    itens = query.order_by(WhatsAppEnvio.criado_em.desc()).limit(max(1, min(limite, 500))).all()
    return {"total": len(itens), "envios": [serializar_envio(e) for e in itens]}


@router.post("/whatsapp/enfileirar-notificacoes")
def enfileirar_notificacoes(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    exigir_farmaceutico_ou_admin(current)
    usuario = getattr(current, "email", None) or getattr(current, "nome", None)
    return enfileirar_notificacoes_pendentes(db, criado_por=usuario)


@router.post("/whatsapp/envio-manual")
def criar_envio_manual_rota(
    dados: WhatsAppEnvioManualCreate,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    exigir_farmaceutico_ou_admin(current)
    usuario = getattr(current, "email", None) or getattr(current, "nome", None)
    envio = criar_envio_manual(
        db,
        telefone=dados.telefone,
        mensagem=dados.mensagem,
        paciente_id=dados.paciente_id,
        prioridade=dados.prioridade or "NORMAL",
        data_programada=dados.data_programada,
        criado_por=usuario,
    )
    db.commit()
    db.refresh(envio)
    return {"mensagem": "Envio manual criado", "envio": serializar_envio(envio)}


@router.post("/whatsapp/simular-envio")
def simular_envio(
    limite: int = 50,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    exigir_farmaceutico_ou_admin(current)
    return simular_envios_pendentes(db, limite=limite)


@router.put("/whatsapp/fila/{envio_id}/cancelar")
def cancelar_envio(
    envio_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    exigir_farmaceutico_ou_admin(current)
    envio = db.query(WhatsAppEnvio).filter(WhatsAppEnvio.id == envio_id).first()
    if not envio:
        raise HTTPException(status_code=404, detail="Envio não encontrado")
    if envio.status in {"SIMULADO", "ENVIADO"}:
        raise HTTPException(status_code=400, detail="Envio já processado não pode ser cancelado")
    envio.status = "CANCELADO"
    envio.atualizado_em = datetime.utcnow()
    db.commit()
    db.refresh(envio)
    return {"mensagem": "Envio cancelado", "envio": serializar_envio(envio)}


@router.put("/whatsapp/fila/{envio_id}/reenfileirar")
def reenfileirar_envio(
    envio_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    exigir_farmaceutico_ou_admin(current)
    envio = db.query(WhatsAppEnvio).filter(WhatsAppEnvio.id == envio_id).first()
    if not envio:
        raise HTTPException(status_code=404, detail="Envio não encontrado")
    if not envio.telefone:
        raise HTTPException(status_code=400, detail="Envio não possui telefone válido")
    envio.status = "PENDENTE"
    envio.ultimo_erro = None
    envio.atualizado_em = datetime.utcnow()
    db.commit()
    db.refresh(envio)
    return {"mensagem": "Envio reenfileirado", "envio": serializar_envio(envio)}
