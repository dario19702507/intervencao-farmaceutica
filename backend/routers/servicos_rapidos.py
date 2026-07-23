from datetime import datetime, timedelta

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
    AtendimentoRapidoCreate,
    AfericaoPACreate,
    GlicemiaCapilarCreate,
    BioimpedanciaCreate,
    PicoFluxoCreate,
)
from services.consultorio_helpers import (
    classificar_pa,
    classificar_glicemia,
    classificar_pico_fluxo,
    calcular_bioimpedancia,
)

# Dependencias mantidas no router legado nesta etapa para reduzir risco.
# Em etapa posterior, serao movidas para um modulo comum de dependencias/permissoes.
from routers.consultorio import (
    get_db_consultorio,
    get_current_user_consultorio,
    exigir_pode_registrar,
)


router = APIRouter(
    prefix="/consultorio",
    tags=["Serviços rápidos"],
)


@router.post("/atendimento-rapido")
def criar_atendimento_rapido(
    atendimento: AtendimentoRapidoCreate,
    db: Session = Depends(get_db_consultorio),
    current: UserConsultorio = Depends(get_current_user_consultorio),
):
    paciente = db.query(PacienteSimplificado).filter(
        PacienteSimplificado.id == atendimento.paciente_simplificado_id
    ).first()

    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente simplificado não encontrado")

    exigir_pode_registrar(current)
    payload = atendimento.model_dump()
    data_atendimento = payload.get("data_atendimento") or datetime.now()
    if data_atendimento > datetime.now() + timedelta(minutes=5):
        raise HTTPException(status_code=400, detail="A data do atendimento não pode estar no futuro")
    payload["data_atendimento"] = data_atendimento

    novo = AtendimentoRapido(**payload)
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


@router.post("/afericao-pa")
def registrar_afericao_pa(
    dados: AfericaoPACreate,
    db: Session = Depends(get_db_consultorio),
    current: UserConsultorio = Depends(get_current_user_consultorio)    
):
    exigir_pode_registrar(current)
    atendimento = db.query(AtendimentoRapido).filter(
        AtendimentoRapido.id == dados.atendimento_rapido_id
    ).first()

    if not atendimento:
        raise HTTPException(status_code=404, detail="Atendimento rápido não encontrado")

    novo = AfericaoPA(
        **dados.model_dump(),
        classificacao=classificar_pa(dados.pressao_sistolica, dados.pressao_diastolica)
    )

    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


@router.post("/glicemia")
def registrar_glicemia(
    dados: GlicemiaCapilarCreate,
    db: Session = Depends(get_db_consultorio),
    current: UserConsultorio = Depends(get_current_user_consultorio)
):
    exigir_pode_registrar(current)
    atendimento = db.query(AtendimentoRapido).filter(
    AtendimentoRapido.id == dados.atendimento_rapido_id
    ).first()

    if not atendimento:
        raise HTTPException(status_code=404, detail="Atendimento rápido não encontrado")

    novo = GlicemiaCapilar(
        **dados.model_dump(),
        classificacao=classificar_glicemia(dados.valor_glicemia, dados.tipo_jejum)
    )

    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


@router.post("/bioimpedancia")
def registrar_bioimpedancia(
    dados: BioimpedanciaCreate,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    atendimento = db.query(AtendimentoRapido).filter(
        AtendimentoRapido.id == dados.atendimento_rapido_id
    ).first()

    if not atendimento:
        raise HTTPException(
            status_code=404,
            detail="Atendimento não encontrado"
        )

    paciente = db.query(PacienteSimplificado).filter(
        PacienteSimplificado.id == atendimento.paciente_simplificado_id
    ).first()

    calculos = calcular_bioimpedancia(
        dados=dados,
        paciente=paciente
    )

    bio = Bioimpedancia(
        atendimento_rapido_id=dados.atendimento_rapido_id,

        peso=dados.peso,
        altura=dados.altura,

        imc=calculos["imc"],
        classificacao_imc=calculos["classificacao_imc"],

        percentual_gordura=dados.percentual_gordura,
        massa_gordura_kg=calculos["massa_gordura_kg"],

        percentual_massa_muscular=dados.percentual_massa_muscular,
        massa_muscular_kg=calculos["massa_muscular_kg"],

        massa_magra_kg=calculos["massa_magra_kg"],

        gordura_visceral=dados.gordura_visceral,
        classificacao_gordura_visceral=calculos["classificacao_gordura_visceral"],

        metabolismo_basal=dados.metabolismo_basal,
        fator_atividade=dados.fator_atividade,
        gasto_energetico_total=calculos["gasto_energetico_total"],

        idade_corporal=dados.idade_corporal,
        diferenca_idade_corporal=calculos["diferenca_idade_corporal"],

        fmi=calculos["fmi"],
        ffmi=calculos["ffmi"],
        relacao_gordura_musculo=calculos["relacao_gordura_musculo"],

        risco_cardiometabolico=calculos["risco_cardiometabolico"],
        alertas=calculos["alertas"],

        classificacao=calculos["classificacao_imc"],
        observacoes=dados.observacoes
    )

    db.add(bio)
    db.commit()
    db.refresh(bio)

    return {
        "mensagem": "Bioimpedância registrada com sucesso",
        "bioimpedancia_id": bio.id,
        "dados_calculados": {
            "imc": bio.imc,
            "classificacao_imc": bio.classificacao_imc,
            "massa_gordura_kg": bio.massa_gordura_kg,
            "massa_muscular_kg": bio.massa_muscular_kg,
            "massa_magra_kg": bio.massa_magra_kg,
            "classificacao_gordura_visceral": bio.classificacao_gordura_visceral,
            "gasto_energetico_total": bio.gasto_energetico_total,
            "fmi": bio.fmi,
            "ffmi": bio.ffmi,
            "risco_cardiometabolico": bio.risco_cardiometabolico,
            "alertas": bio.alertas
        }
    }

@router.post("/pico-fluxo")
def registrar_pico_fluxo(
    dados: PicoFluxoCreate,
    db: Session = Depends(get_db_consultorio),
    current: UserConsultorio = Depends(get_current_user_consultorio)
):
    exigir_pode_registrar(current)
    atendimento = db.query(AtendimentoRapido).filter(
        AtendimentoRapido.id == dados.atendimento_rapido_id
    ).first()

    if not atendimento:
        raise HTTPException(status_code=404, detail="Atendimento rápido não encontrado")

    percentual_previsto = None
    classificacao = None

    if dados.valor_previsto and dados.valor_previsto > 0:
        percentual_previsto = round((dados.valor_medido / dados.valor_previsto) * 100, 2)
        classificacao = classificar_pico_fluxo(percentual_previsto)

    novo = PicoFluxo(
        **dados.model_dump(),
        percentual_previsto=percentual_previsto,
        classificacao=classificacao
    )

    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


@router.get("/atendimentos-rapidos")
def listar_atendimentos_rapidos(
    db: Session = Depends(get_db_consultorio)
):
    return db.query(AtendimentoRapido).order_by(
        AtendimentoRapido.data_atendimento.desc()
    ).limit(100).all()

@router.get("/atendimento-rapido/{atendimento_id}/detalhes")
def detalhe_atendimento_rapido(
    atendimento_id: int,
    db: Session = Depends(get_db_consultorio)
):
    atendimento = db.query(AtendimentoRapido).filter(
        AtendimentoRapido.id == atendimento_id
    ).first()

    if not atendimento:
        raise HTTPException(status_code=404, detail="Atendimento rápido não encontrado")

    paciente = db.query(PacienteSimplificado).filter(
        PacienteSimplificado.id == atendimento.paciente_simplificado_id
    ).first()

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

    return {
        "atendimento": atendimento,
        "paciente": paciente,
        "procedimentos": {
            "pressao_arterial": pa,
            "glicemia": glicemia,
            "bioimpedancia": bioimpedancia,
            "pico_fluxo": pico_fluxo
        }
    }

