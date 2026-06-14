from datetime import datetime


def avaliar_polifarmacia(
    paciente_id: int,
    db,
    current=None
):
    """
    Avaliação farmacoterapêutica reutilizável.

    Esta função é utilitária e, por isso, não deve usar Depends(),
    APIRouter, get_db_consultorio ou get_current_user_consultorio.
    O banco (db) deve ser recebido já aberto pela rota que chamou a função.
    """

    # Import local para evitar importação circular:
    # consultorio.py -> utils_farmacoterapia.py -> consultorio.py
    from routers.consultorio import PacienteClinico, MedicamentoUso

    paciente = db.query(PacienteClinico).filter(
        PacienteClinico.id == paciente_id
    ).first()

    if not paciente:
        return {
            "erro": "Paciente clínico não encontrado",
            "paciente_id": paciente_id,
            "paciente": None,
            "total_medicamentos": 0,
            "polifarmacia": False,
            "risco": "baixo",
            "score": 0,
            "medicamentos": [],
            "alertas": ["Paciente clínico não encontrado."],
            "recomendacoes": [],
            "duplicidades": [],
            "interacoes": [],
            "potencialmente_inapropriados": [],
            "interpretacao": "Paciente clínico não encontrado.",
        }

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
        "potencialmente_inapropriados": potencialmente_inapropriados,
        "interpretacao": interpretacao,
    }
