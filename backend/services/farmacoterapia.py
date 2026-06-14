from datetime import datetime
from fastapi import HTTPException

from models.consultorio_models import (
    PacienteClinico,
    MedicamentoUso,
    IntervencaoFarmacoterapia,
    DesfechoIntervencaoFarmacoterapia,
)


def montar_avaliacao_polifarmacia(paciente_id: int, db):
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
            "frequencia_uso": getattr(m, "frequencia_uso", None),
            "horarios_uso": getattr(m, "horarios_uso", None),
            "uso_se_necessario": bool(getattr(m, "uso_se_necessario", False)),
            "catalogo_medicamento_id": getattr(m, "catalogo_medicamento_id", None),
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
        alertas.append("Paciente em polifarmácia (≥5 medicamentos).")
        recomendacoes.append("Realizar revisão farmacoterapêutica periódica.")

    if total_medicamentos >= 8:
        risco = "alto"
        score += 2
        alertas.append("Elevado número de medicamentos em uso.")

    medicamentos_sem_horario = [m.nome_medicamento for m in medicamentos if not getattr(m, "horarios_uso", None) and not getattr(m, "uso_se_necessario", False)]
    if medicamentos_sem_horario and total_medicamentos >= 3:
        score += 1
        if risco == "baixo":
            risco = "moderado"
        alertas.append("Há medicamentos sem horário de uso estruturado.")
        recomendacoes.append("Padronizar horários de uso para apoiar adesão e avaliação da complexidade terapêutica.")

    uso_sn = [m.nome_medicamento for m in medicamentos if getattr(m, "uso_se_necessario", False)]
    if uso_sn:
        recomendacoes.append("Revisar medicamentos de uso se necessário e orientar critérios claros de utilização.")

    nomes = [(m.nome_medicamento or "").lower() for m in medicamentos]

    duplicidades = []
    for nome in nomes:
        if nomes.count(nome) > 1 and nome not in duplicidades:
            duplicidades.append(nome)

    if duplicidades:
        risco = "alto"
        score += 2
        alertas.append(f"Possível duplicidade terapêutica: {', '.join(duplicidades)}")
        recomendacoes.append("Avaliar duplicidade terapêutica.")

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
        alertas.append(f"Possíveis interações relevantes: {', '.join(interacoes)}")
        recomendacoes.append("Avaliar risco de interação medicamentosa.")

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
        alertas.append("Medicamentos potencialmente inapropriados para uso prolongado.")
        recomendacoes.append(
            "Avaliar necessidade e segurança dos medicamentos potencialmente inapropriados."
        )

    if not alertas:
        alertas.append("Nenhum risco farmacoterapêutico relevante identificado automaticamente.")

    if not recomendacoes:
        recomendacoes.append("Manter acompanhamento farmacoterapêutico.")

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


def montar_evolucao_farmacoterapeutica(paciente_id: int, db):
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
    ).order_by(MedicamentoUso.criado_em.asc()).all()

    intervencoes = db.query(IntervencaoFarmacoterapia).filter(
        IntervencaoFarmacoterapia.paciente_clinico_id == paciente.id
    ).order_by(IntervencaoFarmacoterapia.criado_em.asc()).all()

    eventos = []

    for m in medicamentos:
        eventos.append({
            "data": m.criado_em,
            "tipo": "medicamento",
            "titulo": m.nome_medicamento,
            "descricao": f"{m.dose or ''} {m.via or ''} {getattr(m, 'frequencia_uso', None) or m.frequencia or ''}",
            "horarios_uso": getattr(m, "horarios_uso", None),
            "uso_se_necessario": bool(getattr(m, "uso_se_necessario", False)),
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
        ).order_by(DesfechoIntervencaoFarmacoterapia.criado_em.asc()).all()

        for d in desfechos:
            eventos.append({
                "data": d.criado_em,
                "tipo": "desfecho_intervencao",
                "titulo": d.status_desfecho,
                "descricao": d.resultado_observado or d.observacoes,
                "nova_intervencao": d.necessidade_nova_intervencao,
            })

    eventos = sorted(eventos, key=lambda x: x.get("data") or datetime.min)

    total_medicamentos = len([m for m in medicamentos if m.ativo])
    total_intervencoes = len(intervencoes)
    intervencoes_aceitas = len([i for i in intervencoes if i.aceita_pelo_paciente])
    encaminhamentos = len([i for i in intervencoes if i.necessidade_encaminhamento])

    adesoes = [(m.adesao_referida or "").lower() for m in medicamentos if m.adesao_referida]
    baixa_adesao = sum(1 for a in adesoes if a in ["baixa", "ruim", "irregular"])
    boa_adesao = sum(1 for a in adesoes if a in ["boa", "regular", "adequada"])

    avaliacao_atual = montar_avaliacao_polifarmacia(paciente_id=paciente.id, db=db)

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
        "risco_farmacoterapeutico_atual": avaliacao_atual.get("risco"),
        "score_farmacoterapeutico_atual": avaliacao_atual.get("score"),
        "polifarmacia": avaliacao_atual.get("polifarmacia"),
        "tendencia": tendencia,
        "interpretacao": interpretacao,
        "eventos": eventos,
    }


def montar_sugestoes_plano_cuidado(paciente_id: int, db):
    paciente = db.query(PacienteClinico).filter(PacienteClinico.id == paciente_id).first()

    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente clínico não encontrado")

    achados = []
    pontos_atencao = []
    prioridade = "baixa"

    avaliacao = montar_avaliacao_polifarmacia(paciente_id=paciente.id, db=db)
    evolucao = montar_evolucao_farmacoterapeutica(paciente_id=paciente.id, db=db)

    if avaliacao.get("polifarmacia"):
        achados.append(f"Polifarmácia ({avaliacao.get('total_medicamentos')} medicamentos ativos)")
        pontos_atencao.append("Avaliar necessidade de revisão farmacoterapêutica.")
        prioridade = "moderada"

    if avaliacao.get("risco") == "alto":
        achados.append("Risco farmacoterapêutico alto.")
        pontos_atencao.append("Priorizar revisão de segurança da farmacoterapia.")
        prioridade = "alta"

    if avaliacao.get("interacoes"):
        achados.append("Possíveis interações relevantes: " + ", ".join(avaliacao.get("interacoes")))
        pontos_atencao.append("Avaliar clinicamente possíveis interações medicamentosas.")
        prioridade = "alta"

    if avaliacao.get("duplicidades"):
        achados.append("Possíveis duplicidades terapêuticas: " + ", ".join(avaliacao.get("duplicidades")))
        pontos_atencao.append("Avaliar duplicidade terapêutica.")
        prioridade = "alta"

    if evolucao.get("baixa_adesao", 0) > 0:
        achados.append("Baixa adesão registrada.")
        pontos_atencao.append("Investigar barreiras de adesão e pactuar estratégias com o paciente.")
        prioridade = "alta"

    if evolucao.get("total_intervencoes", 0) >= 3:
        achados.append(f"{evolucao.get('total_intervencoes')} intervenções farmacoterapêuticas registradas.")
        pontos_atencao.append("Reavaliar efetividade das intervenções anteriores.")

    if evolucao.get("encaminhamentos", 0) > 0:
        achados.append("Há necessidade prévia de encaminhamento registrada.")
        pontos_atencao.append("Verificar se o encaminhamento foi realizado e acompanhado.")

    if not achados:
        achados.append("Nenhum achado crítico automático identificado.")
        pontos_atencao.append("Manter avaliação clínica individualizada.")

    return {
        "paciente_id": paciente.id,
        "paciente": paciente.nome,
        "prioridade": prioridade,
        "achados": achados,
        "pontos_atencao": pontos_atencao,
        "observacao": (
            "As sugestões não substituem o julgamento clínico. "
            "Devem ser interpretadas e validadas pelo farmacêutico."
        )
    }


def montar_dashboard_farmacoterapeutico(db):
    pacientes = db.query(PacienteClinico).all()

    total_pacientes = len(pacientes)
    total_medicamentos_ativos = 0
    pacientes_polifarmacia = 0
    risco = {"baixo": 0, "moderado": 0, "alto": 0}
    tendencias = {}
    baixa_adesao = 0
    boa_adesao = 0
    total_intervencoes = 0
    intervencoes_aceitas = 0
    encaminhamentos = 0

    for paciente in pacientes:
        avaliacao = montar_avaliacao_polifarmacia(paciente_id=paciente.id, db=db)
        evolucao = montar_evolucao_farmacoterapeutica(paciente_id=paciente.id, db=db)

        total_medicamentos_ativos += avaliacao.get("total_medicamentos", 0)
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

    media_medicamentos = round(total_medicamentos_ativos / total_pacientes, 2) if total_pacientes > 0 else 0
    taxa_polifarmacia = round((pacientes_polifarmacia / total_pacientes) * 100, 2) if total_pacientes > 0 else 0
    taxa_aceitacao = round((intervencoes_aceitas / total_intervencoes) * 100, 2) if total_intervencoes > 0 else 0
    taxa_encaminhamento = round((encaminhamentos / total_intervencoes) * 100, 2) if total_intervencoes > 0 else 0

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
