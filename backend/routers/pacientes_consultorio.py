from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models.consultorio_models import (
    PacienteSimplificado,
    AtendimentoRapido,
    AfericaoPA,
    GlicemiaCapilar,
    Bioimpedancia,
    PicoFluxo,
    UserConsultorio,
)
from schemas.consultorio_schemas import (
    PacienteSimplificadoCreate,
)
from routers.consultorio import (
    get_db_consultorio,
    get_current_user_consultorio,
    exigir_pode_registrar,
)

router = APIRouter(
    prefix="/consultorio",
    tags=["Consultório - Pacientes"]
)


@router.post("/paciente-simplificado")
def criar_paciente_simplificado(
    paciente: PacienteSimplificadoCreate,
    db: Session = Depends(get_db_consultorio),
    current: UserConsultorio = Depends(get_current_user_consultorio)
):
    exigir_pode_registrar(current)

    novo = PacienteSimplificado(**paciente.model_dump())
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


@router.get("/pacientes-simplificados")
def listar_pacientes_simplificados(
    db: Session = Depends(get_db_consultorio)
):
    return db.query(PacienteSimplificado).order_by(
        PacienteSimplificado.criado_em.desc()
    ).limit(100).all()


@router.get("/paciente-simplificado/{paciente_id}")
def detalhe_paciente_simplificado(
    paciente_id: int,
    db: Session = Depends(get_db_consultorio)
):
    paciente = db.query(PacienteSimplificado).filter(
        PacienteSimplificado.id == paciente_id
    ).first()

    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente simplificado não encontrado")

    atendimentos = db.query(AtendimentoRapido).filter(
        AtendimentoRapido.paciente_simplificado_id == paciente.id
    ).order_by(AtendimentoRapido.data_atendimento.desc()).all()

    return {
        "paciente": paciente,
        "total_atendimentos": len(atendimentos),
        "atendimentos": atendimentos
    }




@router.get("/paciente-simplificado/{paciente_id}/historico")
def historico_paciente_simplificado(
    paciente_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    paciente = db.query(PacienteSimplificado).filter(
        PacienteSimplificado.id == paciente_id
    ).first()

    if not paciente:
        raise HTTPException(
            status_code=404,
            detail="Paciente simplificado não encontrado"
        )

    atendimentos = db.query(AtendimentoRapido).filter(
        AtendimentoRapido.paciente_simplificado_id == paciente_id
    ).order_by(
        AtendimentoRapido.data_atendimento.desc()
    ).all()

    historico = []

    for atendimento in atendimentos:
        pa = db.query(AfericaoPA).filter(
            AfericaoPA.atendimento_rapido_id == atendimento.id
        ).first()

        glicemia = db.query(GlicemiaCapilar).filter(
            GlicemiaCapilar.atendimento_rapido_id == atendimento.id
        ).first()

        bioimpedancia = db.query(Bioimpedancia).filter(
            Bioimpedancia.atendimento_rapido_id == atendimento.id
        ).first()

        pico_fluxo = db.query(PicoFluxo).filter(
            PicoFluxo.atendimento_rapido_id == atendimento.id
        ).first()

        historico.append({
            "atendimento_id": atendimento.id,
            "data_atendimento": atendimento.data_atendimento,
            "tipo_servico": atendimento.tipo_servico,
            "observacoes": atendimento.observacoes,
            "procedimentos": {
                "pressao_arterial": {
                    "id": pa.id,
                    "pressao_sistolica": pa.pressao_sistolica,
                    "pressao_diastolica": pa.pressao_diastolica,
                    "frequencia_cardiaca": pa.frequencia_cardiaca,
                    "classificacao": pa.classificacao,
                    "observacoes": pa.observacoes,
                } if pa else None,

                "glicemia": {
                    "id": glicemia.id,
                    "valor_glicemia": glicemia.valor_glicemia,
                    "tipo_jejum": glicemia.tipo_jejum,
                    "classificacao": glicemia.classificacao,
                    "observacoes": glicemia.observacoes,
                } if glicemia else None,

                "bioimpedancia": {
                    "id": bioimpedancia.id,
                    "peso": bioimpedancia.peso,
                    "altura": bioimpedancia.altura,
                    "imc": bioimpedancia.imc,
                    "classificacao_imc": bioimpedancia.classificacao_imc,
                    "percentual_gordura": bioimpedancia.percentual_gordura,
                    "massa_gordura_kg": bioimpedancia.massa_gordura_kg,
                    "percentual_massa_muscular": bioimpedancia.percentual_massa_muscular,
                    "massa_muscular_kg": bioimpedancia.massa_muscular_kg,
                    "massa_magra_kg": bioimpedancia.massa_magra_kg,
                    "gordura_visceral": bioimpedancia.gordura_visceral,
                    "classificacao_gordura_visceral": bioimpedancia.classificacao_gordura_visceral,
                    "metabolismo_basal": bioimpedancia.metabolismo_basal,
                    "fator_atividade": bioimpedancia.fator_atividade,
                    "gasto_energetico_total": bioimpedancia.gasto_energetico_total,
                    "idade_corporal": bioimpedancia.idade_corporal,
                    "diferenca_idade_corporal": bioimpedancia.diferenca_idade_corporal,
                    "fmi": bioimpedancia.fmi,
                    "ffmi": bioimpedancia.ffmi,
                    "relacao_gordura_musculo": bioimpedancia.relacao_gordura_musculo,
                    "risco_cardiometabolico": bioimpedancia.risco_cardiometabolico,
                    "alertas": bioimpedancia.alertas,
                    "classificacao": bioimpedancia.classificacao,
                    "observacoes": bioimpedancia.observacoes,
                } if bioimpedancia else None,

                "pico_fluxo": {
                    "id": pico_fluxo.id,
                    "valor_medido": pico_fluxo.valor_medido,
                    "valor_previsto": pico_fluxo.valor_previsto,
                    "percentual_previsto": pico_fluxo.percentual_previsto,
                    "classificacao": pico_fluxo.classificacao,
                    "observacoes": pico_fluxo.observacoes,
                } if pico_fluxo else None,
            }
        })

    return {
        "paciente": {
            "id": paciente.id,
            "nome": paciente.nome,
            "idade": paciente.idade,
            "sexo": paciente.sexo,
            "telefone": paciente.telefone,
            "bairro": paciente.bairro,
        },
        "total_atendimentos": len(historico),
        "historico": historico
    }
