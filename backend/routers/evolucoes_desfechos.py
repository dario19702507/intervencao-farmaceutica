from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from routers.consultorio import (
    get_db_consultorio,
    get_current_user_consultorio,
    exigir_farmaceutico_ou_admin,
)
from models.consultorio_models import (
    ProntuarioClinico,
    EvolucaoClinica,
    DesfechoClinico,
    UserConsultorio,
)
from schemas.consultorio_schemas import (
    EvolucaoClinicaCreate,
    DesfechoClinicoCreate,
)

router = APIRouter(
    prefix="/consultorio",
    tags=["Consultório - Evoluções e Desfechos"],
)


@router.post("/prontuario/{prontuario_id}/evolucao")
def criar_evolucao_clinica(
    prontuario_id: int,
    dados: EvolucaoClinicaCreate,
    db: Session = Depends(get_db_consultorio),
    current: UserConsultorio = Depends(get_current_user_consultorio)
):
    exigir_farmaceutico_ou_admin(current)
    prontuario = db.query(ProntuarioClinico).filter(
        ProntuarioClinico.id == prontuario_id
    ).first()

    if not prontuario:
        raise HTTPException(status_code=404, detail="Prontuário não encontrado")

    nova_evolucao = EvolucaoClinica(
        prontuario_id=prontuario_id,
        **dados.model_dump()
    )

    db.add(nova_evolucao)
    db.commit()
    db.refresh(nova_evolucao)

    return {
        "mensagem": "Evolução clínica registrada com sucesso.",
        "evolucao": nova_evolucao
    }


@router.get("/prontuario/{prontuario_id}/evolucoes")
def listar_evolucoes_clinicas(
    prontuario_id: int,
    db: Session = Depends(get_db_consultorio),
    current: UserConsultorio = Depends(get_current_user_consultorio)
):
    prontuario = db.query(ProntuarioClinico).filter(
        ProntuarioClinico.id == prontuario_id
    ).first()

    if not prontuario:
        raise HTTPException(status_code=404, detail="Prontuário não encontrado")

    evolucoes = db.query(EvolucaoClinica).filter(
        EvolucaoClinica.prontuario_id == prontuario_id
    ).order_by(EvolucaoClinica.data_evolucao.desc()).all()

    return {
        "prontuario_id": prontuario_id,
        "total_evolucoes": len(evolucoes),
        "evolucoes": evolucoes
    }


@router.post("/evolucao/{evolucao_id}/vincular-intervencao")
def vincular_intervencao(
    evolucao_id: int,
    intervencao_id: int,
    db: Session = Depends(get_db_consultorio),
    current: UserConsultorio = Depends(get_current_user_consultorio),
):
    exigir_farmaceutico_ou_admin(current)
    evolucao = db.query(EvolucaoClinica).filter(
        EvolucaoClinica.id == evolucao_id
    ).first()

    if not evolucao:
        raise HTTPException(status_code=404, detail="Evolução não encontrada")

    intervencao = db.execute(
        text("SELECT id FROM intervencoes WHERE id = :id"),
        {"id": intervencao_id}
    ).fetchone()

    if not intervencao:
        raise HTTPException(
            status_code=404,
            detail="Intervenção não encontrada no sistema"
        )

    evolucao.intervencao_id = intervencao_id

    db.commit()
    db.refresh(evolucao)

    return {
        "mensagem": "Intervenção validada e vinculada com sucesso.",
        "evolucao_id": evolucao_id,
        "intervencao_id": intervencao_id
    }


@router.post("/evolucao/{evolucao_id}/desfecho")
def criar_desfecho_clinico(
    evolucao_id: int,
    dados: DesfechoClinicoCreate,
    db: Session = Depends(get_db_consultorio),
):
    evolucao = db.query(EvolucaoClinica).filter(
        EvolucaoClinica.id == evolucao_id
    ).first()

    if not evolucao:
        raise HTTPException(status_code=404, detail="Evolução não encontrada")

    novo_desfecho = DesfechoClinico(
        evolucao_id=evolucao_id,
        **dados.model_dump()
    )

    db.add(novo_desfecho)
    db.commit()
    db.refresh(novo_desfecho)

    return {
        "mensagem": "Desfecho clínico registrado com sucesso.",
        "desfecho": novo_desfecho
    }
