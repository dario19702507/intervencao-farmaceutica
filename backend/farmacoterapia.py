from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from routers.consultorio import (
    get_db_consultorio,
    get_current_user_consultorio,
    UserConsultorio,
    PacienteClinico,
    MedicamentoUso,
    IntervencaoFarmacoterapia,
    DesfechoIntervencaoFarmacoterapia,
    MedicamentoUsoCreate,
    IntervencaoFarmacoterapiaCreate,
    DesfechoIntervencaoFarmacoterapiaCreate,
    registrar_auditoria,
)

router = APIRouter(
    prefix="/consultorio",
    tags=["Farmacoterapia"]
)

@router.get("/paciente-clinico/{paciente_id}/evolucao-farmacoterapeutica")
def evolucao_farmacoterapeutica(
    paciente_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    paciente = db.query(PacienteClinico).filter(
        PacienteClinico.id == paciente_id
    ).first()

    if not paciente:
        raise HTTPException(
            status_code=404,
            detail="Paciente clínico não encontrado"
        )

    medicamentos = db.query(MedicamentoUso).filter(
        MedicamentoUso.paciente_clinico_id == paciente.id
    ).order_by(
        MedicamentoUso.criado_em.asc()
    ).all()

    intervencoes = db.query(IntervencaoFarmacoterapia).filter(
        IntervencaoFarmacoterapia.paciente_clinico_id == paciente.id
    ).order_by(
        IntervencaoFarmacoterapia.criado_em.asc()
    ).all()

    eventos = []

    for m in medicamentos:
        eventos.append({
            "data": m.criado_em,
            "tipo": "medicamento",
            "titulo": m.nome_medicamento,
            "descricao": f"{m.dose or ''} {m.via or ''} {m.frequencia or ''}",
            "adesao": m.adesao_referida,
            "ativo": m.ativo,
        })

    for i in intervencoes:
        eventos.append({
            "data": i.criado_em,
            "tipo": "intervencao",
            "titulo": i.tipo_intervencao,
            "descricao": i.descricao or i.conduta,
            "aceita": i.aceita_pelo_paciente,
            "encaminhamento": i.necessidade_encaminhamento,
        })

        desfechos = db.query(DesfechoIntervencaoFarmacoterapia).filter(
            DesfechoIntervencaoFarmacoterapia.intervencao_id == i.id
        ).order_by(
            DesfechoIntervencaoFarmacoterapia.criado_em.asc()
        ).all()

        for d in desfechos:
            eventos.append({
                "data": d.criado_em,
                "tipo": "desfecho_intervencao",
                "titulo": d.status_desfecho,
                "descricao": d.resultado_observado or d.observacoes,
                "nova_intervencao": d.necessidade_nova_intervencao,
            })

    eventos = sorted(
        eventos,
        key=lambda x: x.get("data") or datetime.min
    )

    total_medicamentos = len([
        m for m in medicamentos
        if m.ativo
    ])

    total_intervencoes = len(intervencoes)

    intervencoes_aceitas = len([
        i for i in intervencoes
        if i.aceita_pelo_paciente
    ])

    encaminhamentos = len([
        i for i in intervencoes
        if i.necessidade_encaminhamento
    ])

    adesoes = [
        (m.adesao_referida or "").lower()
        for m in medicamentos
        if m.adesao_referida
    ]

    baixa_adesao = sum(
        1 for a in adesoes
        if a in ["baixa", "ruim", "irregular"]
    )

    boa_adesao = sum(
        1 for a in adesoes
        if a in ["boa", "regular", "adequada"]
    )

    avaliacao_atual = avaliar_polifarmacia(
        paciente_id=paciente.id,
        db=db,
        current=current
    )

    tendencia = "estável"

    if total_medicamentos >= 8:
        tendencia = "maior_complexidade"

    elif total_medicamentos >= 5:
        tendencia = "polifarmacia"

    if baixa_adesao > 0:
        tendencia = "risco_por_adesao"

    if total_intervencoes > 0 and intervencoes_aceitas >= total_intervencoes:
        tendencia = "resposta_favoravel"

    interpretacao = (
        f"Paciente em uso de {total_medicamentos} medicamento(s) ativo(s), "
        f"com {total_intervencoes} intervenção(ões) farmacoterapêutica(s) registrada(s). "
        f"Tendência farmacoterapêutica atual: {tendencia}."
    )

    return {
        "paciente_id": paciente.id,
        "paciente": paciente.nome,

        "total_medicamentos_ativos": total_medicamentos,
        "total_intervencoes": total_intervencoes,
        "intervencoes_aceitas": intervencoes_aceitas,
        "encaminhamentos": encaminhamentos,

        "baixa_adesao": baixa_adesao,
        "boa_adesao": boa_adesao,

        "risco_farmacoterapeutico_atual":
            avaliacao_atual.get("risco"),

        "score_farmacoterapeutico_atual":
            avaliacao_atual.get("score"),

        "polifarmacia":
            avaliacao_atual.get("polifarmacia"),

        "tendencia": tendencia,
        "interpretacao": interpretacao,

        "eventos": eventos,
    }

@router.get("/dashboard-farmacoterapeutico")
def dashboard_farmacoterapeutico(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    pacientes = db.query(PacienteClinico).all()

    total_pacientes = len(pacientes)
    total_medicamentos_ativos = 0
    pacientes_polifarmacia = 0

    risco = {
        "baixo": 0,
        "moderado": 0,
        "alto": 0,
    }

    tendencias = {}
    baixa_adesao = 0
    boa_adesao = 0
    total_intervencoes = 0
    intervencoes_aceitas = 0
    encaminhamentos = 0

    for paciente in pacientes:
        avaliacao = avaliar_polifarmacia(
            paciente_id=paciente.id,
            db=db,
            current=current
        )

        evolucao = evolucao_farmacoterapeutica(
            paciente_id=paciente.id,
            db=db,
            current=current
        )

        total_medicamentos_ativos += avaliacao.get(
            "total_medicamentos",
            0
        )

        if avaliacao.get("polifarmacia"):
            pacientes_polifarmacia += 1

        risco_atual = avaliacao.get("risco") or "baixo"
        risco[risco_atual] = risco.get(risco_atual, 0) + 1

        tendencia = evolucao.get("tendencia") or "estável"
        tendencias[tendencia] = tendencias.get(tendencia, 0) + 1

        baixa_adesao += evolucao.get("baixa_adesao", 0)
        boa_adesao += evolucao.get("boa_adesao", 0)

        total_intervencoes += evolucao.get("total_intervencoes", 0)
        intervencoes_aceitas += evolucao.get("intervencoes_aceitas", 0)
        encaminhamentos += evolucao.get("encaminhamentos", 0)

    media_medicamentos = (
        round(total_medicamentos_ativos / total_pacientes, 2)
        if total_pacientes > 0
        else 0
    )

    taxa_polifarmacia = (
        round((pacientes_polifarmacia / total_pacientes) * 100, 2)
        if total_pacientes > 0
        else 0
    )

    taxa_aceitacao = (
        round((intervencoes_aceitas / total_intervencoes) * 100, 2)
        if total_intervencoes > 0
        else 0
    )

    taxa_encaminhamento = (
        round((encaminhamentos / total_intervencoes) * 100, 2)
        if total_intervencoes > 0
        else 0
    )

    return {
        "total_pacientes": total_pacientes,
        "total_medicamentos_ativos": total_medicamentos_ativos,
        "media_medicamentos_por_paciente": media_medicamentos,

        "pacientes_polifarmacia": pacientes_polifarmacia,
        "taxa_polifarmacia": taxa_polifarmacia,

        "risco_farmacoterapeutico": risco,
        "tendencias": tendencias,

        "adesao": {
            "baixa_adesao": baixa_adesao,
            "boa_adesao": boa_adesao,
        },

        "intervencoes": {
            "total": total_intervencoes,
            "aceitas": intervencoes_aceitas,
            "encaminhamentos": encaminhamentos,
            "taxa_aceitacao": taxa_aceitacao,
            "taxa_encaminhamento": taxa_encaminhamento,
        }
    }

@router.post("/paciente-clinico/{paciente_id}/medicamento")
def adicionar_medicamento_uso(
    paciente_id: int,
    dados: MedicamentoUsoCreate,
    db: Session = Depends(get_db_consultorio),
    current = Depends(get_current_user_consultorio)):
    exigir_farmaceutico_ou_admin(current)

    paciente = db.query(PacienteClinico).filter(
        PacienteClinico.id == paciente_id
    ).first()

    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente clínico não encontrado")

    novo = MedicamentoUso(
        paciente_clinico_id=paciente_id,
        **dados.model_dump()
    )

    db.add(novo)
    db.commit()
    db.refresh(novo)

    return novo

@router.get("/paciente-clinico/{paciente_id}/avaliacao-polifarmacia")
def avaliar_polifarmacia(
    paciente_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    paciente = db.query(PacienteClinico).filter(
        PacienteClinico.id == paciente_id
    ).first()

    if not paciente:
        raise HTTPException(
            status_code=404,
            detail="Paciente clínico não encontrado"
        )

    medicamentos = db.query(MedicamentoUso).filter(
        MedicamentoUso.paciente_clinico_id == paciente.id,
        MedicamentoUso.ativo == True
    ).all()

    total_medicamentos = len(medicamentos)

    polifarmacia = total_medicamentos >= 5

    lista_medicamentos = []

    for m in medicamentos:
        lista_medicamentos.append({
            "id": m.id,
            "medicamento": m.nome_medicamento,
            "dose": m.dose,
            "via": m.via,
            "frequencia": m.frequencia,
            "indicacao": m.indicacao,
            "adesao": m.adesao_referida,
        })

    risco = "baixo"
    score = 0
    alertas = []
    recomendacoes = []

    if total_medicamentos >= 5:
        risco = "moderado"
        score += 2

        alertas.append(
            "Paciente em polifarmácia (≥5 medicamentos)."
        )

        recomendacoes.append(
            "Realizar revisão farmacoterapêutica periódica."
        )

    if total_medicamentos >= 8:
        risco = "alto"
        score += 2

        alertas.append(
            "Elevado número de medicamentos em uso."
        )

    nomes = [
        (m.nome_medicamento or "").lower()
        for m in medicamentos
    ]

    duplicidades = []

    for nome in nomes:
        if nomes.count(nome) > 1 and nome not in duplicidades:
            duplicidades.append(nome)

    if duplicidades:
        risco = "alto"
        score += 2

        alertas.append(
            f"Possível duplicidade terapêutica: {', '.join(duplicidades)}"
        )

        recomendacoes.append(
            "Avaliar duplicidade terapêutica."
        )

    pares_risco = [
        ("diclofenaco", "losartana"),
        ("ibuprofeno", "enalapril"),
        ("sinvastatina", "claritromicina"),
        ("varfarina", "amoxicilina"),
        ("metformina", "alcool"),
    ]

    interacoes = []

    for a, b in pares_risco:
        if a in nomes and b in nomes:
            interacoes.append(f"{a} + {b}")

    if interacoes:
        risco = "alto"
        score += 3

        alertas.append(
            f"Possíveis interações relevantes: {', '.join(interacoes)}"
        )

        recomendacoes.append(
            "Avaliar risco de interação medicamentosa."
        )

    medicamentos_pim = [
        "diazepam",
        "clonazepam",
        "amitriptilina",
        "carisoprodol",
        "prometazina",
    ]

    potencialmente_inapropriados = []

    for nome in nomes:
        if nome in medicamentos_pim:
            potencialmente_inapropriados.append(nome)

    if potencialmente_inapropriados:
        score += 2

        if risco != "alto":
            risco = "moderado"

        alertas.append(
            "Medicamentos potencialmente inapropriados para uso prolongado."
        )

        recomendacoes.append(
            "Avaliar necessidade e segurança dos medicamentos potencialmente inapropriados."
        )

    if not alertas:
        alertas.append(
            "Nenhum risco farmacoterapêutico relevante identificado automaticamente."
        )

    if not recomendacoes:
        recomendacoes.append(
            "Manter acompanhamento farmacoterapêutico."
        )

    interpretacao = (
        f"Paciente em uso de {total_medicamentos} medicamento(s) ativos. "
        f"Classificação automatizada de risco farmacoterapêutico: {risco}."
    )

    return {
        "paciente_id": paciente.id,
        "paciente": paciente.nome,

        "total_medicamentos": total_medicamentos,

        "polifarmacia": polifarmacia,

        "risco": risco,
        "score": score,

        "medicamentos": lista_medicamentos,

        "alertas": alertas,
        "recomendacoes": recomendacoes,

        "duplicidades": duplicidades,
        "interacoes": interacoes,

        "potencialmente_inapropriados":
            potencialmente_inapropriados,

        "interpretacao":
            interpretacao,
    }

@router.get("/intervencao-farmacoterapia/{intervencao_id}/desfechos")
def listar_desfechos_intervencao_farmacoterapia(
    intervencao_id: int,
    db: Session = Depends(get_db_consultorio),
    current = Depends(get_current_user_consultorio)):
    desfechos = db.query(DesfechoIntervencaoFarmacoterapia).filter(
        DesfechoIntervencaoFarmacoterapia.intervencao_id == intervencao_id
    ).order_by(DesfechoIntervencaoFarmacoterapia.criado_em.desc()).all()

    return desfechos

