from typing import Optional
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

# Importacao provisoria a partir do modulo legado.
# No pacote de models definitivo, esses imports devem migrar para models.consultorio_models.
from routers.consultorio import (
    get_db_consultorio,
    get_current_user_consultorio,
    exigir_pode_registrar,
    calcular_idade,
    classificar_pa,
    classificar_glicemia,
    classificar_pico_fluxo,
    calcular_bioimpedancia,
    obter_ou_criar_paciente_agenda,
    PacienteSimplificado,
    AtendimentoRapido,
    AfericaoPA,
    GlicemiaCapilar,
    Bioimpedancia,
    PicoFluxo,
    PacienteSimplificadoCreate,
    AtendimentoRapidoCreate,
    AfericaoPACreate,
    GlicemiaCapilarCreate,
    BioimpedanciaCreate,
    PicoFluxoCreate,
    UserConsultorio,
)

router = APIRouter(
    prefix="/consultorio",
    tags=["Servicos Rapidos"]
)


@router.post("/paciente-simplificado")
def criar_paciente_simplificado(
    paciente: PacienteSimplificadoCreate,
    db: Session = Depends(get_db_consultorio),
    current: UserConsultorio = Depends(get_current_user_consultorio)
):
    exigir_pode_registrar(current)

    paciente_agenda = obter_ou_criar_paciente_agenda(
        db=db,
        nome=paciente.nome,
        telefone=paciente.telefone,
        origem="atendimento_rapido"
    )

    novo = PacienteSimplificado(
        **paciente.model_dump(),
        paciente_agenda_id=paciente_agenda.id if paciente_agenda else None
    )

    db.add(novo)
    db.commit()
    db.refresh(novo)

    return novo


@router.post("/atendimento-rapido")
def criar_atendimento_rapido(
    atendimento: AtendimentoRapidoCreate,
    db: Session = Depends(get_db_consultorio),
    current: UserConsultorio = Depends(get_current_user_consultorio)
):
    exigir_pode_registrar(current)

    paciente = db.query(PacienteSimplificado).filter(
        PacienteSimplificado.id == atendimento.paciente_simplificado_id
    ).first()

    if not paciente:
        raise HTTPException(
            status_code=404,
            detail="Paciente simplificado nao encontrado"
        )

    novo = AtendimentoRapido(**atendimento.model_dump())

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
        raise HTTPException(
            status_code=404,
            detail="Atendimento rapido nao encontrado"
        )

    novo = AfericaoPA(
        **dados.model_dump(),
        classificacao=classificar_pa(
            dados.pressao_sistolica,
            dados.pressao_diastolica
        )
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
        raise HTTPException(
            status_code=404,
            detail="Atendimento rapido nao encontrado"
        )

    novo = GlicemiaCapilar(
        **dados.model_dump(),
        classificacao=classificar_glicemia(
            dados.valor_glicemia,
            dados.tipo_jejum
        )
    )

    db.add(novo)
    db.commit()
    db.refresh(novo)

    return novo


@router.post("/bioimpedancia")
def registrar_bioimpedancia(
    dados: BioimpedanciaCreate,
    db: Session = Depends(get_db_consultorio),
    current: UserConsultorio = Depends(get_current_user_consultorio)
):
    exigir_pode_registrar(current)

    atendimento = db.query(AtendimentoRapido).filter(
        AtendimentoRapido.id == dados.atendimento_rapido_id
    ).first()

    if not atendimento:
        raise HTTPException(
            status_code=404,
            detail="Atendimento nao encontrado"
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
        observacoes=dados.observacoes,
    )

    db.add(bio)
    db.commit()
    db.refresh(bio)

    return {
        "mensagem": "Bioimpedancia registrada com sucesso",
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
            "alertas": bio.alertas,
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
        raise HTTPException(
            status_code=404,
            detail="Atendimento rapido nao encontrado"
        )

    percentual_previsto = None
    classificacao = None

    if dados.valor_previsto and dados.valor_previsto > 0:
        percentual_previsto = round(
            (dados.valor_medido / dados.valor_previsto) * 100,
            2
        )
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


@router.get("/pacientes-simplificados")
def listar_pacientes_simplificados(
    db: Session = Depends(get_db_consultorio),
    current: UserConsultorio = Depends(get_current_user_consultorio)
):
    pacientes = db.query(PacienteSimplificado).order_by(
        PacienteSimplificado.criado_em.desc()
    ).limit(100).all()

    return pacientes


@router.get("/atendimentos-rapidos")
def listar_atendimentos_rapidos(
    db: Session = Depends(get_db_consultorio),
    current: UserConsultorio = Depends(get_current_user_consultorio)
):
    atendimentos = db.query(AtendimentoRapido).order_by(
        AtendimentoRapido.data_atendimento.desc()
    ).limit(100).all()

    return atendimentos


@router.get("/atendimento-rapido/{atendimento_id}/detalhes")
def detalhe_atendimento_rapido(
    atendimento_id: int,
    db: Session = Depends(get_db_consultorio),
    current: UserConsultorio = Depends(get_current_user_consultorio)
):
    atendimento = db.query(AtendimentoRapido).filter(
        AtendimentoRapido.id == atendimento_id
    ).first()

    if not atendimento:
        raise HTTPException(
            status_code=404,
            detail="Atendimento rapido nao encontrado"
        )

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
            "pico_fluxo": pico_fluxo,
        }
    }


@router.get("/paciente-simplificado/{paciente_id}")
def detalhe_paciente_simplificado(
    paciente_id: int,
    db: Session = Depends(get_db_consultorio),
    current: UserConsultorio = Depends(get_current_user_consultorio)
):
    paciente = db.query(PacienteSimplificado).filter(
        PacienteSimplificado.id == paciente_id
    ).first()

    if not paciente:
        raise HTTPException(
            status_code=404,
            detail="Paciente simplificado nao encontrado"
        )

    atendimentos = db.query(AtendimentoRapido).filter(
        AtendimentoRapido.paciente_simplificado_id == paciente.id
    ).order_by(
        AtendimentoRapido.data_atendimento.desc()
    ).all()

    return {
        "paciente": paciente,
        "total_atendimentos": len(atendimentos),
        "atendimentos": atendimentos,
    }
