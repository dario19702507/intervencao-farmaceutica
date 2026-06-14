"""Rotas para catálogo e mapeamento de intervenções farmacêuticas padronizadas."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from routers.consultorio import get_current_user_consultorio
from services.intervencoes_padronizadas import (
    dashboard_intervencoes_padronizadas,
    garantir_estrutura_intervencoes_padronizadas,
    mapeamento_intervencoes_legado,
    opcoes_intervencoes_padronizadas,
)

router = APIRouter(prefix="/consultorio/intervencoes-padronizadas", tags=["Intervenções Padronizadas"])


@router.get("/opcoes")
def obter_opcoes_intervencoes_padronizadas(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_consultorio),
):
    return opcoes_intervencoes_padronizadas(db)


@router.post("/preparar-estrutura")
def preparar_estrutura_intervencoes_padronizadas(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_consultorio),
):
    garantir_estrutura_intervencoes_padronizadas(db)
    return {"ok": True, "mensagem": "Catálogo de intervenções padronizadas verificado/criado com sucesso."}


@router.get("/mapeamento-legado")
def obter_mapeamento_legado(
    limite: int = Query(default=500, ge=1, le=2000),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_consultorio),
):
    return mapeamento_intervencoes_legado(db, limite=limite)


@router.get("/dashboard")
def obter_dashboard_intervencoes_padronizadas(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_consultorio),
):
    return dashboard_intervencoes_padronizadas(db)
