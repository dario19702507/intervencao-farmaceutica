"""Rotas do Centro de Atenção Farmacêutica.

Contrato canônico para pendências assistenciais, documentais, CEAF e
farmacoterapêuticas. Não executa ações automáticas; apenas identifica e prioriza.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from routers.consultorio import get_db_consultorio, get_current_user_consultorio
from services.atencao_farmaceutica import (
    CATEGORIAS,
    CRITICIDADE,
    MEDICAMENTOS_ALTO_RISCO,
    REGRAS,
    gerar_pendencias_paciente,
    listar_pendencias,
    montar_dashboard_atencao,
)

router = APIRouter(prefix="/consultorio", tags=["Centro de Atenção Farmacêutica"])


@router.get("/atencao-farmaceutica/opcoes")
def opcoes_atencao_farmaceutica(current=Depends(get_current_user_consultorio)):
    return {
        "criticidades": CRITICIDADE,
        "categorias": CATEGORIAS,
        "regras": REGRAS,
        "medicamentos_alto_risco": MEDICAMENTOS_ALTO_RISCO,
        "matriz": [
            {"categoria": "ASSISTENCIAL", "tipo": "PRM_ABERTO", "criticidade": "CRITICA/MODERADA/INFORMATIVA"},
            {"categoria": "ASSISTENCIAL", "tipo": "INTERVENCAO_SEM_DESFECHO", "criticidade": "MODERADA"},
            {"categoria": "ASSISTENCIAL", "tipo": "META_VENCIDA", "criticidade": "CRITICA/MODERADA"},
            {"categoria": "ASSISTENCIAL", "tipo": "ACAO_PLANO_ATRASADA", "criticidade": "CRITICA/MODERADA"},
            {"categoria": "CEAF", "tipo": "LAUDO_VENCIDO", "criticidade": "CRITICA"},
            {"categoria": "CEAF", "tipo": "LAUDO_A_VENCER_30_DIAS", "criticidade": "MODERADA"},
            {"categoria": "DOCUMENTAL", "tipo": "PACOTE_DOCUMENTAL_INCOMPLETO", "criticidade": "MODERADA"},
            {"categoria": "FARMACOTERAPEUTICA", "tipo": "POLIFARMACIA", "criticidade": "MODERADA"},
            {"categoria": "FARMACOTERAPEUTICA", "tipo": "COMPLEXIDADE_MUITO_ALTA", "criticidade": "CRITICA"},
            {"categoria": "FARMACOTERAPEUTICA", "tipo": "ADESAO_BAIXA", "criticidade": "CRITICA"},
        ],
        "observacao": "A primeira versão identifica e prioriza pendências; nenhuma ação é executada automaticamente.",
    }


@router.get("/atencao-farmaceutica/dashboard")
def dashboard_atencao_farmaceutica(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    return montar_dashboard_atencao(db)


@router.get("/atencao-farmaceutica/pendencias")
def pendencias_atencao_farmaceutica(
    criticidade: str | None = Query(None),
    categoria: str | None = Query(None),
    paciente_id: int | None = Query(None),
    limite: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    return {
        "pendencias": listar_pendencias(db, criticidade=criticidade, categoria=categoria, paciente_id=paciente_id, limite=limite),
        "filtros": {"criticidade": criticidade, "categoria": categoria, "paciente_id": paciente_id, "limite": limite},
    }


@router.get("/atencao-farmaceutica/paciente/{paciente_id}/pendencias")
def pendencias_paciente_atencao_farmaceutica(
    paciente_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    pendencias = gerar_pendencias_paciente(paciente_id, db)
    return {"paciente_id": paciente_id, "total": len(pendencias), "pendencias": pendencias}
