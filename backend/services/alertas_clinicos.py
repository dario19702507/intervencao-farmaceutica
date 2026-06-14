from collections import defaultdict
from datetime import datetime, date
import io

from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from models.consultorio_models import (
    PacienteSimplificado,
    AtendimentoRapido,
    AfericaoPA,
    GlicemiaCapilar,
    Bioimpedancia,
    PicoFluxo,
    PacienteClinico,
    ProntuarioClinico,
    EvolucaoClinica,
    DesfechoClinico,
    EvolucaoFarmaceutica,
    ResolucaoAlertaClinico,
)

from services.consultorio_helpers import calcular_risco_populacional
from services.indicadores_consultorio import montar_triagem_risco
from services.farmacoterapia import (
    montar_avaliacao_polifarmacia,
    montar_evolucao_farmacoterapeutica,
)


def svc_alertas_pendentes(db):
    hoje = date.today()
    alertas = []

    evolucoes_retorno = db.query(EvolucaoClinica).filter(
        EvolucaoClinica.necessidade_retorno == True,
        EvolucaoClinica.data_retorno_sugerida.isnot(None)
    ).all()

    for evolucao in evolucoes_retorno:
        desfecho = db.query(DesfechoClinico).filter(
            DesfechoClinico.evolucao_id == evolucao.id
        ).first()

        if desfecho:
            continue

        prontuario = db.query(ProntuarioClinico).filter(
            ProntuarioClinico.id == evolucao.prontuario_id
        ).first()

        paciente = None
        if prontuario:
            paciente = db.query(PacienteClinico).filter(
                PacienteClinico.id == prontuario.paciente_clinico_id
            ).first()

        dias = (evolucao.data_retorno_sugerida - hoje).days

        if dias < 0:
            tipo_alerta = "retorno_atrasado"
            prioridade = "alta"
            mensagem = f"Retorno atrasado há {abs(dias)} dia(s)."
        elif dias <= 7:
            tipo_alerta = "retorno_proximo"
            prioridade = "moderada"
            mensagem = f"Retorno previsto em {dias} dia(s)."
        else:
            continue

        alertas.append({
            "tipo_alerta": tipo_alerta,
            "prioridade": prioridade,
            "mensagem": mensagem,
            "paciente_id": paciente.id if paciente else None,
            "paciente_nome": paciente.nome if paciente else "Não informado",
            "telefone": paciente.telefone if paciente else None,
            "evolucao_id": evolucao.id,
            "prontuario_id": evolucao.prontuario_id,
            "data_retorno_sugerida": evolucao.data_retorno_sugerida,
        })

    evolucoes_sem_desfecho = db.query(EvolucaoClinica).all()

    for evolucao in evolucoes_sem_desfecho:
        desfecho = db.query(DesfechoClinico).filter(
            DesfechoClinico.evolucao_id == evolucao.id
        ).first()

        if desfecho:
            continue

        prontuario = db.query(ProntuarioClinico).filter(
            ProntuarioClinico.id == evolucao.prontuario_id
        ).first()

        paciente = None
        if prontuario:
            paciente = db.query(PacienteClinico).filter(
                PacienteClinico.id == prontuario.paciente_clinico_id
            ).first()

        alertas.append({
            "tipo_alerta": "evolucao_sem_desfecho",
            "prioridade": "baixa",
            "mensagem": "Evolução clínica ainda sem desfecho registrado.",
            "paciente_id": paciente.id if paciente else None,
            "paciente_nome": paciente.nome if paciente else "Não informado",
            "telefone": paciente.telefone if paciente else None,
            "evolucao_id": evolucao.id,
            "prontuario_id": evolucao.prontuario_id,
            "data_retorno_sugerida": evolucao.data_retorno_sugerida,
        })

    atendimentos_risco = db.query(AtendimentoRapido).filter(
        AtendimentoRapido.convertido_para_consultorio == False
    ).all()

    for atendimento in atendimentos_risco:
        riscos = []

        pa = db.query(AfericaoPA).filter(
            AfericaoPA.atendimento_rapido_id == atendimento.id
        ).first()

        if pa and pa.classificacao in ["pa_elevada", "hipertensao", "crise_hipertensiva"]:
            riscos.append("PA alterada")

        glicemia = db.query(GlicemiaCapilar).filter(
            GlicemiaCapilar.atendimento_rapido_id == atendimento.id
        ).first()

        if glicemia and glicemia.classificacao in ["alterada", "possivel_diabetes"]:
            riscos.append("Glicemia alterada")

        bio = db.query(Bioimpedancia).filter(
            Bioimpedancia.atendimento_rapido_id == atendimento.id
        ).first()

        if bio and bio.classificacao in [
            "sobrepeso",
            "obesidade_grau_1",
            "obesidade_grau_2",
            "obesidade_grau_3",
        ]:
            riscos.append("Bioimpedância/IMC em risco")

        pico = db.query(PicoFluxo).filter(
            PicoFluxo.atendimento_rapido_id == atendimento.id
        ).first()

        if pico and pico.classificacao in ["zona_amarela", "zona_vermelha"]:
            riscos.append("Pico de fluxo em risco")

        if not riscos:
            continue

        paciente = db.query(PacienteSimplificado).filter(
            PacienteSimplificado.id == atendimento.paciente_simplificado_id
        ).first()

        alertas.append({
            "tipo_alerta": "risco_nao_convertido",
            "prioridade": "moderada" if len(riscos) < 3 else "alta",
            "mensagem": "Paciente com risco identificado em serviço rápido ainda não convertido para acompanhamento clínico.",
            "paciente_simplificado_id": paciente.id if paciente else None,
            "paciente_nome": paciente.nome if paciente else "Não informado",
            "telefone": paciente.telefone if paciente else None,
            "atendimento_id": atendimento.id,
            "riscos": riscos,
        })

    resumo = {
        "total_alertas": len(alertas),
        "alta": sum(1 for a in alertas if a["prioridade"] == "alta"),
        "moderada": sum(1 for a in alertas if a["prioridade"] == "moderada"),
        "baixa": sum(1 for a in alertas if a["prioridade"] == "baixa"),
    }

    return {"resumo": resumo, "alertas": alertas}


def svc_alertas_clinicos_consolidados(db, current=None):
    alertas = []

    alertas_pendentes_response = svc_alertas_pendentes(db=db)

    for alerta in alertas_pendentes_response.get("alertas", []):
        alertas.append({
            "origem": "alertas_pendentes",
            "tipo": alerta.get("tipo_alerta"),
            "prioridade": alerta.get("prioridade"),
            "mensagem": alerta.get("mensagem"),
            "paciente_id": alerta.get("paciente_id") or alerta.get("paciente_simplificado_id"),
            "paciente_nome": alerta.get("paciente_nome"),
            "telefone": alerta.get("telefone"),
            "data": alerta.get("data_retorno_sugerida"),
            "referencia": alerta,
        })

    triagem_response = montar_triagem_risco(db=db)

    for paciente in triagem_response.get("pacientes", []):
        alertas.append({
            "origem": "triagem_risco",
            "tipo": "risco_servico_rapido",
            "prioridade": paciente.get("prioridade"),
            "mensagem": paciente.get("sugestao"),
            "paciente_id": paciente.get("paciente_id"),
            "paciente_nome": paciente.get("nome"),
            "telefone": None,
            "data": paciente.get("data_atendimento"),
            "referencia": paciente,
        })

    bio_registros = db.query(Bioimpedancia).all()

    for bio in bio_registros:
        if bio.risco_cardiometabolico in ["moderado", "alto"]:
            atendimento = db.query(AtendimentoRapido).filter(
                AtendimentoRapido.id == bio.atendimento_rapido_id
            ).first()

            paciente = None
            if atendimento:
                paciente = db.query(PacienteSimplificado).filter(
                    PacienteSimplificado.id == atendimento.paciente_simplificado_id
                ).first()

            prioridade = "alta" if bio.risco_cardiometabolico == "alto" else "moderada"

            alertas.append({
                "origem": "bioimpedancia",
                "tipo": "risco_cardiometabolico",
                "prioridade": prioridade,
                "mensagem": f"Bioimpedância com risco cardiometabólico {bio.risco_cardiometabolico}.",
                "paciente_id": paciente.id if paciente else None,
                "paciente_nome": paciente.nome if paciente else "Não informado",
                "telefone": paciente.telefone if paciente else None,
                "data": atendimento.data_atendimento if atendimento else None,
                "referencia": {
                    "bioimpedancia_id": bio.id,
                    "imc": bio.imc,
                    "classificacao_imc": bio.classificacao_imc,
                    "gordura_visceral": bio.gordura_visceral,
                    "classificacao_gordura_visceral": bio.classificacao_gordura_visceral,
                    "alertas": bio.alertas,
                },
            })

    evolucoes = db.query(EvolucaoFarmaceutica).all()

    for evolucao in evolucoes:
        paciente = db.query(PacienteSimplificado).filter(
            PacienteSimplificado.id == evolucao.paciente_simplificado_id
        ).first()

        if evolucao.risco_clinico == "alto":
            alertas.append({
                "origem": "evolucao_farmaceutica",
                "tipo": "risco_clinico_alto",
                "prioridade": "alta",
                "mensagem": "Evolução farmacêutica com risco clínico alto.",
                "paciente_id": paciente.id if paciente else None,
                "paciente_nome": paciente.nome if paciente else "Não informado",
                "telefone": paciente.telefone if paciente else None,
                "data": evolucao.criado_em,
                "referencia": {"evolucao_id": evolucao.id, "avaliacao": evolucao.avaliacao, "plano": evolucao.plano},
            })

        if evolucao.adesao == "ruim":
            alertas.append({
                "origem": "evolucao_farmaceutica",
                "tipo": "baixa_adesao",
                "prioridade": "moderada",
                "mensagem": "Baixa adesão registrada em evolução farmacêutica.",
                "paciente_id": paciente.id if paciente else None,
                "paciente_nome": paciente.nome if paciente else "Não informado",
                "telefone": paciente.telefone if paciente else None,
                "data": evolucao.criado_em,
                "referencia": {"evolucao_id": evolucao.id, "adesao": evolucao.adesao},
            })

        if evolucao.prm:
            alertas.append({
                "origem": "evolucao_farmaceutica",
                "tipo": "prm_rnm",
                "prioridade": "moderada",
                "mensagem": f"PRM/RNM registrado: {evolucao.prm}",
                "paciente_id": paciente.id if paciente else None,
                "paciente_nome": paciente.nome if paciente else "Não informado",
                "telefone": paciente.telefone if paciente else None,
                "data": evolucao.criado_em,
                "referencia": {"evolucao_id": evolucao.id, "prm": evolucao.prm},
            })

    pacientes_clinicos = db.query(PacienteClinico).all()

    for paciente_clinico in pacientes_clinicos:
        avaliacao = montar_avaliacao_polifarmacia(paciente_id=paciente_clinico.id, db=db)

        if (
            avaliacao.get("polifarmacia")
            or avaliacao.get("risco") in ["moderado", "alto"]
            or avaliacao.get("interacoes")
            or avaliacao.get("duplicidades")
        ):
            prioridade = "alta" if avaliacao.get("risco") == "alto" else "moderada"

            alertas.append({
                "origem": "polifarmacia",
                "tipo": "risco_farmacoterapeutico",
                "prioridade": prioridade,
                "mensagem": avaliacao.get("interpretacao"),
                "paciente_id": paciente_clinico.paciente_simplificado_origem_id or paciente_clinico.id,
                "paciente_nome": paciente_clinico.nome,
                "telefone": paciente_clinico.telefone,
                "data": datetime.utcnow(),
                "referencia": avaliacao,
            })

    pacientes_clinicos = db.query(PacienteClinico).all()

    for paciente_clinico in pacientes_clinicos:
        evolucao = montar_evolucao_farmacoterapeutica(paciente_id=paciente_clinico.id, db=db)

        tendencia = evolucao.get("tendencia")
        risco = evolucao.get("risco_farmacoterapeutico_atual")
        baixa_adesao = evolucao.get("baixa_adesao", 0)
        total_intervencoes = evolucao.get("total_intervencoes", 0)
        encaminhamentos = evolucao.get("encaminhamentos", 0)

        gerar_alerta = False
        prioridade = "moderada"
        motivos = []

        if risco == "alto":
            gerar_alerta = True
            prioridade = "alta"
            motivos.append("risco farmacoterapêutico alto")

        if tendencia in ["maior_complexidade", "risco_por_adesao"]:
            gerar_alerta = True
            prioridade = "alta"
            motivos.append(f"tendência farmacoterapêutica: {tendencia}")

        if baixa_adesao > 0:
            gerar_alerta = True
            motivos.append("baixa adesão registrada")

        if total_intervencoes >= 3:
            gerar_alerta = True
            motivos.append("múltiplas intervenções farmacoterapêuticas")

        if encaminhamentos > 0:
            gerar_alerta = True
            motivos.append("encaminhamento farmacoterapêutico necessário")

        if not gerar_alerta:
            continue

        alertas.append({
            "origem": "evolucao_farmacoterapeutica",
            "tipo": "tendencia_farmacoterapeutica",
            "prioridade": prioridade,
            "mensagem": "Paciente com necessidade de revisão farmacoterapêutica: " + "; ".join(motivos) + ".",
            "paciente_id": paciente_clinico.paciente_simplificado_origem_id or paciente_clinico.id,
            "paciente_nome": paciente_clinico.nome,
            "telefone": paciente_clinico.telefone,
            "data": datetime.utcnow(),
            "referencia": evolucao,
        })

    def normalizar_data_para_comparacao(valor):
        if valor is None:
            return datetime.min
        if isinstance(valor, datetime):
            return valor
        if isinstance(valor, date):
            return datetime.combine(valor, datetime.min.time())
        return datetime.min

    alertas_por_paciente = {}

    for alerta in alertas:
        paciente_id = alerta.get("paciente_id")
        chave = paciente_id or alerta.get("paciente_nome")

        if not chave:
            continue

        if chave not in alertas_por_paciente:
            alertas_por_paciente[chave] = {
                "origem": "consolidado",
                "tipo": "alerta_consolidado_paciente",
                "alerta_chave": f"consolidado-{chave}",
                "prioridade": alerta.get("prioridade"),
                "mensagem": "Paciente com múltiplos alertas clínicos/farmacoterapêuticos.",
                "paciente_id": alerta.get("paciente_id"),
                "paciente_nome": alerta.get("paciente_nome"),
                "telefone": alerta.get("telefone"),
                "data": alerta.get("data"),
                "referencia": {"motivos": [], "alertas_originais": []},
            }

        item = alertas_por_paciente[chave]
        prioridade_atual = item.get("prioridade")
        nova_prioridade = alerta.get("prioridade")

        pesos = {"muito_alta": 4, "alta": 3, "moderada": 2, "baixa": 1, None: 0}

        if pesos.get(nova_prioridade, 0) > pesos.get(prioridade_atual, 0):
            item["prioridade"] = nova_prioridade

        data_alerta = normalizar_data_para_comparacao(alerta.get("data"))
        data_item = normalizar_data_para_comparacao(item.get("data"))

        if alerta.get("data") and data_alerta > data_item:
            item["data"] = alerta.get("data")

        motivo = alerta.get("mensagem") or alerta.get("tipo")
        if motivo and motivo not in item["referencia"]["motivos"]:
            item["referencia"]["motivos"].append(motivo)

        item["referencia"]["alertas_originais"].append(alerta)

    alertas = list(alertas_por_paciente.values())

    for alerta in alertas:
        motivos = alerta["referencia"].get("motivos", [])
        alerta["mensagem"] = "Paciente com " + f"{len(motivos)} alerta(s) consolidado(s): " + "; ".join(motivos[:4])
        if len(motivos) > 4:
            alerta["mensagem"] += f"; e mais {len(motivos) - 4}."

    ordem_prioridade = {"muito_alta": 4, "alta": 3, "moderada": 2, "baixa": 1, None: 0}

    alertas = sorted(
        alertas,
        key=lambda a: (ordem_prioridade.get(a.get("prioridade"), 0), normalizar_data_para_comparacao(a.get("data"))),
        reverse=True,
    )

    resumo = {
        "total": len(alertas),
        "muito_alta": sum(1 for a in alertas if a.get("prioridade") == "muito_alta"),
        "alta": sum(1 for a in alertas if a.get("prioridade") == "alta"),
        "moderada": sum(1 for a in alertas if a.get("prioridade") == "moderada"),
        "baixa": sum(1 for a in alertas if a.get("prioridade") == "baixa"),
    }

    for alerta in alertas:
        if not alerta.get("alerta_chave"):
            alerta["alerta_chave"] = f"{alerta.get('origem')}-{alerta.get('tipo')}-{alerta.get('paciente_id') or alerta.get('paciente_nome')}"

    return {"resumo": resumo, "alertas": alertas}


def svc_resolver_alerta_clinico(dados, db, current=None):
    resolucao_existente = db.query(ResolucaoAlertaClinico).filter(
        ResolucaoAlertaClinico.alerta_chave == dados.alerta_chave
    ).first()

    if resolucao_existente:
        resolucao_existente.desfecho = dados.desfecho
        resolucao_existente.observacoes = dados.observacoes
        resolucao_existente.evolucao_id = dados.evolucao_id
        resolucao_existente.intervencao_id = dados.intervencao_id
        resolucao_existente.resolvido_por = getattr(current, "nome", None)
        resolucao_existente.resolvido_em = datetime.utcnow()

        db.commit()
        db.refresh(resolucao_existente)

        return {"mensagem": "Resolução do alerta atualizada com sucesso.", "resolucao_id": resolucao_existente.id}

    nova = ResolucaoAlertaClinico(
        **dados.model_dump(),
        resolvido_por=getattr(current, "nome", None),
        resolvido_em=datetime.utcnow(),
    )

    db.add(nova)
    db.commit()
    db.refresh(nova)

    return {"mensagem": "Alerta clínico resolvido com sucesso.", "resolucao_id": nova.id}


def svc_listar_resolucoes_alertas_clinicos(db, current=None):
    resolucoes = db.query(ResolucaoAlertaClinico).order_by(
        ResolucaoAlertaClinico.resolvido_em.desc()
    ).all()

    return {
        "total": len(resolucoes),
        "resolucoes": [
            {
                "id": r.id,
                "alerta_origem": r.alerta_origem,
                "alerta_tipo": r.alerta_tipo,
                "alerta_chave": r.alerta_chave,
                "paciente_id": r.paciente_id,
                "paciente_nome": r.paciente_nome,
                "prioridade": r.prioridade,
                "mensagem_alerta": r.mensagem_alerta,
                "desfecho": r.desfecho,
                "observacoes": r.observacoes,
                "evolucao_id": r.evolucao_id,
                "intervencao_id": r.intervencao_id,
                "resolvido_por": r.resolvido_por,
                "resolvido_em": r.resolvido_em,
            }
            for r in resolucoes
        ],
    }


def svc_dashboard_resolucao_alertas(db, current=None):
    alertas_response = svc_alertas_clinicos_consolidados(db=db, current=current)
    resolucoes_response = svc_listar_resolucoes_alertas_clinicos(db=db, current=current)

    alertas = alertas_response.get("alertas", [])
    resolucoes = resolucoes_response.get("resolucoes", [])

    total_alertas_gerados = len(alertas) + len(resolucoes)
    total_resolvidos = len(resolucoes)
    total_ativos = len(alertas)

    por_desfecho = {}
    por_prioridade = {}
    por_profissional = {}
    resolucoes_recentes = []

    for r in resolucoes:
        desfecho = r.get("desfecho") or "não_informado"
        prioridade = r.get("prioridade") or "sem_prioridade"
        profissional = r.get("resolvido_por") or "não_informado"

        por_desfecho[desfecho] = por_desfecho.get(desfecho, 0) + 1
        por_prioridade[prioridade] = por_prioridade.get(prioridade, 0) + 1
        por_profissional[profissional] = por_profissional.get(profissional, 0) + 1

        resolucoes_recentes.append({
            "paciente_nome": r.get("paciente_nome"),
            "desfecho": r.get("desfecho"),
            "prioridade": r.get("prioridade"),
            "mensagem_alerta": r.get("mensagem_alerta"),
            "resolvido_por": r.get("resolvido_por"),
            "resolvido_em": r.get("resolvido_em"),
        })

    resolucoes_recentes = sorted(
        resolucoes_recentes,
        key=lambda x: x.get("resolvido_em") or datetime.min,
        reverse=True,
    )[:10]

    taxa_resolucao = round((total_resolvidos / total_alertas_gerados) * 100, 2) if total_alertas_gerados > 0 else 0

    return {
        "total_alertas_gerados": total_alertas_gerados,
        "total_ativos": total_ativos,
        "total_resolvidos": total_resolvidos,
        "taxa_resolucao": taxa_resolucao,
        "por_desfecho": por_desfecho,
        "por_prioridade": por_prioridade,
        "por_profissional": por_profissional,
        "resolucoes_recentes": resolucoes_recentes,
    }


def svc_relatorio_resolucao_alertas_pdf(db, current=None):
    dashboard = svc_dashboard_resolucao_alertas(db=db, current=current)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30,
    )

    styles = getSampleStyleSheet()
    elementos = []

    elementos.append(Paragraph("Relatório de Resolutividade Clínica", styles["Title"]))
    elementos.append(Spacer(1, 20))

    resumo_data = [
        ["Indicador", "Valor"],
        ["Alertas gerados", dashboard["total_alertas_gerados"]],
        ["Alertas ativos", dashboard["total_ativos"]],
        ["Alertas resolvidos", dashboard["total_resolvidos"]],
        ["Taxa de resolução (%)", dashboard["taxa_resolucao"]],
    ]

    tabela_resumo = Table(resumo_data, colWidths=[260, 180])
    tabela_resumo.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
    ]))

    elementos.append(tabela_resumo)
    elementos.append(Spacer(1, 24))
    elementos.append(Paragraph("Resoluções recentes", styles["Heading2"]))

    recentes = dashboard.get("resolucoes_recentes", [])

    if recentes:
        tabela_recentes = [["Paciente", "Desfecho", "Prioridade", "Profissional"]]

        for r in recentes:
            tabela_recentes.append([
                r.get("paciente_nome") or "-",
                r.get("desfecho") or "-",
                r.get("prioridade") or "-",
                r.get("resolvido_por") or "-",
            ])

        tabela = Table(tabela_recentes, colWidths=[160, 120, 100, 120])
        tabela.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
        ]))
        elementos.append(tabela)

    elementos.append(Spacer(1, 30))
    elementos.append(Paragraph(f"Relatório gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles["Italic"]))

    doc.build(elementos)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=relatorio_resolucao_alertas.pdf"},
    )


def svc_dashboard_serie_temporal(db, current=None):
    series = defaultdict(lambda: {
        "atendimentos": 0,
        "pa_alterada": 0,
        "glicemia_alterada": 0,
        "bioimpedancia_risco": 0,
        "pico_fluxo_risco": 0,
        "alertas_resolvidos": 0,
    })

    atendimentos = db.query(AtendimentoRapido).all()

    for a in atendimentos:
        if not a.data_atendimento:
            continue

        mes = a.data_atendimento.strftime("%Y-%m")
        series[mes]["atendimentos"] += 1

        pa = db.query(AfericaoPA).filter(AfericaoPA.atendimento_rapido_id == a.id).first()
        if pa and pa.classificacao in ["pa_elevada", "hipertensao", "crise_hipertensiva"]:
            series[mes]["pa_alterada"] += 1

        glicemia = db.query(GlicemiaCapilar).filter(GlicemiaCapilar.atendimento_rapido_id == a.id).first()
        if glicemia and glicemia.classificacao in ["alterada", "possivel_diabetes"]:
            series[mes]["glicemia_alterada"] += 1

        bio = db.query(Bioimpedancia).filter(Bioimpedancia.atendimento_rapido_id == a.id).first()
        if bio and (bio.risco_cardiometabolico in ["moderado", "alto"] or bio.classificacao in ["sobrepeso", "obesidade_grau_1", "obesidade_grau_2", "obesidade_grau_3"]):
            series[mes]["bioimpedancia_risco"] += 1

        pico = db.query(PicoFluxo).filter(PicoFluxo.atendimento_rapido_id == a.id).first()
        if pico and pico.classificacao in ["zona_amarela", "zona_vermelha"]:
            series[mes]["pico_fluxo_risco"] += 1

    resolucoes = db.query(ResolucaoAlertaClinico).all()

    for r in resolucoes:
        if not r.resolvido_em:
            continue
        mes = r.resolvido_em.strftime("%Y-%m")
        series[mes]["alertas_resolvidos"] += 1

    resultado = []

    for mes in sorted(series.keys()):
        item = series[mes]
        total_alteracoes = item["pa_alterada"] + item["glicemia_alterada"] + item["bioimpedancia_risco"] + item["pico_fluxo_risco"]
        taxa_resolucao = round((item["alertas_resolvidos"] / total_alteracoes) * 100, 2) if total_alteracoes > 0 else 0

        resultado.append({
            "mes": mes,
            "atendimentos": item["atendimentos"],
            "pa_alterada": item["pa_alterada"],
            "glicemia_alterada": item["glicemia_alterada"],
            "bioimpedancia_risco": item["bioimpedancia_risco"],
            "pico_fluxo_risco": item["pico_fluxo_risco"],
            "total_alteracoes": total_alteracoes,
            "alertas_resolvidos": item["alertas_resolvidos"],
            "taxa_resolucao": taxa_resolucao,
        })

    return resultado


def svc_classificacao_risco_populacional(db, current=None):
    pacientes = db.query(PacienteSimplificado).all()
    resultado = []

    for paciente in pacientes:
        atendimentos = db.query(AtendimentoRapido).filter(
            AtendimentoRapido.paciente_simplificado_id == paciente.id
        ).order_by(AtendimentoRapido.data_atendimento.desc()).all()

        if not atendimentos:
            continue

        ultimo = atendimentos[0]

        pa = db.query(AfericaoPA).filter(AfericaoPA.atendimento_rapido_id == ultimo.id).first()
        glicemia = db.query(GlicemiaCapilar).filter(GlicemiaCapilar.atendimento_rapido_id == ultimo.id).first()
        bio = db.query(Bioimpedancia).filter(Bioimpedancia.atendimento_rapido_id == ultimo.id).first()
        pico = db.query(PicoFluxo).filter(PicoFluxo.atendimento_rapido_id == ultimo.id).first()

        reincidencia = max(len(atendimentos) - 1, 0)
        classificacao = calcular_risco_populacional(pa=pa, glicemia=glicemia, bio=bio, pico=pico, reincidencia_alertas=reincidencia)

        resultado.append({
            "paciente_id": paciente.id,
            "nome": paciente.nome,
            "idade": paciente.idade,
            "sexo": paciente.sexo,
            "risco": classificacao["risco"],
            "score": classificacao["score"],
            "fatores": classificacao["fatores"],
            "ultimo_atendimento": ultimo.data_atendimento,
            "reincidencia_alertas": reincidencia,
        })

    ordem = {"muito_alto": 4, "alto": 3, "moderado": 2, "baixo": 1}

    resultado = sorted(resultado, key=lambda x: (ordem.get(x["risco"], 0), x["score"]), reverse=True)

    resumo = {"baixo": 0, "moderado": 0, "alto": 0, "muito_alto": 0}

    for r in resultado:
        resumo[r["risco"]] += 1

    return {"total_pacientes": len(resultado), "resumo": resumo, "pacientes": resultado}
