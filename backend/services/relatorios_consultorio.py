from io import BytesIO
from datetime import datetime, date
from sqlalchemy.orm import Session
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

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
    MedicamentoUso,
    IntervencaoFarmacoterapia,
    MetaTerapeutica,
    AcaoPlanoCuidado,
    PlanoCuidado,
)
from services.consultorio_helpers import calcular_idade, calcular_percentual
from services.documentos_institucionais import (
    cabecalho_institucional,
    rodape_institucional,
    assinatura_profissional,
    tabela_resultados_servico,
)


def svc_gerar_declaracao_pdf(
    atendimento_id: int,
    db: Session = None,
    current=None
):
    atendimento = db.query(AtendimentoRapido).filter(
        AtendimentoRapido.id == atendimento_id
    ).first()

    if not atendimento:
        raise HTTPException(
            status_code=404,
            detail="Atendimento não encontrado"
        )

    paciente = db.query(PacienteSimplificado).filter(
        PacienteSimplificado.id == atendimento.paciente_simplificado_id
    ).first()

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    elementos = []

    elementos.extend(cabecalho_institucional(styles, "DECLARAÇÃO DE SERVIÇO FARMACÊUTICO"))

    nome_paciente = getattr(paciente, "nome", "Paciente")
    data_atendimento = (
        atendimento.data_atendimento.strftime("%d/%m/%Y")
        if atendimento.data_atendimento
        else "Não informada"
    )

    texto = f"""
    Declaramos para os devidos fins que o(a) paciente
    <b>{nome_paciente}</b>
    compareceu à Farmácia Escola Profª Ana Maria Cervantes Baraza,
    em {data_atendimento},
    e realizou o serviço farmacêutico de
    <b>{atendimento.tipo_servico}</b>.
    """

    elementos.append(Paragraph(texto, styles["BodyText"]))
    elementos.append(Spacer(1, 16))
    elementos.extend(tabela_resultados_servico(atendimento, db, styles))

    elementos.append(Spacer(1, 24))

    if atendimento.observacoes:
        elementos.append(
            Paragraph(
                "<b>Observações:</b>",
                styles["Heading3"]
            )
        )

        elementos.append(
            Paragraph(
                atendimento.observacoes,
                styles["BodyText"]
            )
        )

        elementos.append(Spacer(1, 30))

    elementos.extend(assinatura_profissional(current, styles))

    doc.build(elementos, onFirstPage=lambda canvas, doc: rodape_institucional(canvas, doc, current), onLaterPages=lambda canvas, doc: rodape_institucional(canvas, doc, current))

    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition":
            "inline; filename=declaracao_atendimento.pdf"
        }
    )

def svc_laudo_bioimpedancia_pdf(
    bioimpedancia_id: int,
    db: Session = None,
    current=None
):
    bio = db.query(Bioimpedancia).filter(
        Bioimpedancia.id == bioimpedancia_id
    ).first()

    if not bio:
        raise HTTPException(
            status_code=404,
            detail="Registro de bioimpedância não encontrado"
        )

    atendimento = db.query(AtendimentoRapido).filter(
        AtendimentoRapido.id == bio.atendimento_rapido_id
    ).first()

    paciente = None

    if atendimento:
        paciente = db.query(PacienteSimplificado).filter(
            PacienteSimplificado.id == atendimento.paciente_simplificado_id
        ).first()

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    elementos = []

    elementos.extend(cabecalho_institucional(styles, "Laudo de Avaliação por Bioimpedância"))

    dados_paciente = [
        ["Campo", "Informação"],
        ["Paciente", getattr(paciente, "nome", "Não informado")],
        ["Idade", getattr(paciente, "idade", "Não informada")],
        ["Sexo", getattr(paciente, "sexo", "Não informado")],
        ["Data do atendimento", atendimento.data_atendimento.strftime("%d/%m/%Y") if atendimento and atendimento.data_atendimento else "Não informada"],
    ]

    tabela_paciente = Table(dados_paciente, colWidths=[180, 320])
    tabela_paciente.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0f2f1")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("PADDING", (0, 0), (-1, -1), 7),
    ]))

    elementos.append(tabela_paciente)
    elementos.append(Spacer(1, 16))

    dados_bio = [
        ["Indicador", "Resultado"],
        ["Peso", f"{bio.peso or '—'} kg"],
        ["Altura", f"{bio.altura or '—'} m"],
        ["IMC", f"{bio.imc or '—'}"],
        ["Classificação IMC", bio.classificacao_imc or bio.classificacao or "Sem classificação"],
        ["Gordura corporal", f"{bio.percentual_gordura or '—'} %"],
        ["Massa de gordura", f"{bio.massa_gordura_kg or '—'} kg"],
        ["Massa muscular", f"{bio.percentual_massa_muscular or '—'} %"],
        ["Massa muscular estimada", f"{bio.massa_muscular_kg or '—'} kg"],
        ["Massa magra estimada", f"{bio.massa_magra_kg or '—'} kg"],
        ["Gordura visceral", bio.gordura_visceral or "—"],
        ["Classificação gordura visceral", bio.classificacao_gordura_visceral or "Sem classificação"],
        ["Metabolismo basal", f"{bio.metabolismo_basal or '—'} kcal"],
        ["Fator de atividade", bio.fator_atividade or "—"],
        ["Gasto energético total estimado", f"{bio.gasto_energetico_total or '—'} kcal/dia"],
        ["Idade corporal", bio.idade_corporal or "—"],
        ["Diferença idade corporal", bio.diferenca_idade_corporal or "—"],
        ["FMI", bio.fmi or "—"],
        ["FFMI", bio.ffmi or "—"],
        ["Relação gordura/músculo", bio.relacao_gordura_musculo or "—"],
        ["Risco cardiometabólico", bio.risco_cardiometabolico or "Não classificado"],
    ]

    tabela_bio = Table(dados_bio, colWidths=[240, 260])
    tabela_bio.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#fef3c7")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("PADDING", (0, 0), (-1, -1), 7),
    ]))

    elementos.append(Paragraph("Resultados da Bioimpedância", styles["Heading2"]))
    elementos.append(tabela_bio)
    elementos.append(Spacer(1, 16))

    elementos.append(Paragraph("Interpretação automática", styles["Heading2"]))

    interpretacao = []

    if bio.classificacao_imc:
        interpretacao.append(f"O IMC foi classificado como {bio.classificacao_imc}.")

    if bio.classificacao_gordura_visceral:
        interpretacao.append(
            f"A gordura visceral foi classificada como {bio.classificacao_gordura_visceral}."
        )

    if bio.risco_cardiometabolico:
        interpretacao.append(
            f"O risco cardiometabólico estimado foi classificado como {bio.risco_cardiometabolico}."
        )

    if bio.alertas:
        interpretacao.append(f"Alertas clínicos: {bio.alertas}.")

    if not interpretacao:
        interpretacao.append(
            "Não foram gerados alertas automáticos para este registro."
        )

    for texto in interpretacao:
        elementos.append(Paragraph(texto, styles["Normal"]))
        elementos.append(Spacer(1, 6))

    elementos.append(Spacer(1, 20))

    elementos.append(Paragraph("Observações", styles["Heading2"]))
    elementos.append(Paragraph(bio.observacoes or "Sem observações registradas.", styles["Normal"]))

    elementos.append(Spacer(1, 46))

    nome_profissional = getattr(current, "nome", "Farmacêutico responsável")
    categoria = getattr(current, "categoria_profissional", "Farmacêutico")
    crf = getattr(current, "crf", None) or "CRF: __________________"

    assinatura = [
        ["________________________________________"],
        [nome_profissional],
        [categoria],
        [crf],
    ]

    tabela_assinatura = Table(assinatura, colWidths=[420])
    tabela_assinatura.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 1), (0, 1), "Helvetica-Bold"),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))

    elementos.append(tabela_assinatura)

    doc.build(elementos, onFirstPage=lambda canvas, doc: rodape_institucional(canvas, doc, current), onLaterPages=lambda canvas, doc: rodape_institucional(canvas, doc, current))
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "inline; filename=laudo_bioimpedancia.pdf"
        }
    )

def svc_relatorio_mensal_consultorio(
    ano: int,
    mes: int,
    db: Session = None
):
    inicio = date(ano, mes, 1)

    if mes == 12:
        fim = date(ano + 1, 1, 1)
    else:
        fim = date(ano, mes + 1, 1)

    atendimentos_rapidos = db.query(AtendimentoRapido).filter(
        AtendimentoRapido.data_atendimento >= inicio,
        AtendimentoRapido.data_atendimento < fim
    ).all()

    ids_atendimentos = [a.id for a in atendimentos_rapidos]

    por_tipo_servico = {}
    for atendimento in atendimentos_rapidos:
        tipo = atendimento.tipo_servico or "nao_informado"
        por_tipo_servico[tipo] = por_tipo_servico.get(tipo, 0) + 1

    pa_total = db.query(AfericaoPA).filter(
        AfericaoPA.atendimento_rapido_id.in_(ids_atendimentos)
    ).count() if ids_atendimentos else 0

    pa_alterada = db.query(AfericaoPA).filter(
        AfericaoPA.atendimento_rapido_id.in_(ids_atendimentos),
        AfericaoPA.classificacao.in_(["pa_elevada", "hipertensao", "crise_hipertensiva"])
    ).count() if ids_atendimentos else 0

    glicemia_total = db.query(GlicemiaCapilar).filter(
        GlicemiaCapilar.atendimento_rapido_id.in_(ids_atendimentos)
    ).count() if ids_atendimentos else 0

    glicemia_alterada = db.query(GlicemiaCapilar).filter(
        GlicemiaCapilar.atendimento_rapido_id.in_(ids_atendimentos),
        GlicemiaCapilar.classificacao.in_(["alterada", "possivel_diabetes"])
    ).count() if ids_atendimentos else 0

    bio_total = db.query(Bioimpedancia).filter(
        Bioimpedancia.atendimento_rapido_id.in_(ids_atendimentos)
    ).count() if ids_atendimentos else 0

    bio_risco = db.query(Bioimpedancia).filter(
        Bioimpedancia.atendimento_rapido_id.in_(ids_atendimentos),
        Bioimpedancia.classificacao.in_([
            "sobrepeso",
            "obesidade_grau_1",
            "obesidade_grau_2",
            "obesidade_grau_3"
        ])
    ).count() if ids_atendimentos else 0

    pico_total = db.query(PicoFluxo).filter(
        PicoFluxo.atendimento_rapido_id.in_(ids_atendimentos)
    ).count() if ids_atendimentos else 0

    pico_risco = db.query(PicoFluxo).filter(
        PicoFluxo.atendimento_rapido_id.in_(ids_atendimentos),
        PicoFluxo.classificacao.in_(["zona_amarela", "zona_vermelha"])
    ).count() if ids_atendimentos else 0

    pacientes_convertidos = db.query(PacienteClinico).filter(
        PacienteClinico.criado_em >= inicio,
        PacienteClinico.criado_em < fim
    ).count()

    evolucoes = db.query(EvolucaoClinica).filter(
        EvolucaoClinica.data_evolucao >= inicio,
        EvolucaoClinica.data_evolucao < fim
    ).count()

    desfechos = db.query(DesfechoClinico).filter(
        DesfechoClinico.data_desfecho >= inicio,
        DesfechoClinico.data_desfecho < fim
    ).all()

    melhora_clinica = {}
    adesao_tratamento = {}

    resolvidos = 0
    encaminhamentos = 0

    for d in desfechos:
        melhora = d.melhora_clinica or "nao_informado"
        adesao = d.adesao_tratamento or "nao_informado"

        melhora_clinica[melhora] = melhora_clinica.get(melhora, 0) + 1
        adesao_tratamento[adesao] = adesao_tratamento.get(adesao, 0) + 1

        if d.resolucao_problema:
            resolvidos += 1

        if d.necessidade_encaminhamento:
            encaminhamentos += 1

    total_procedimentos = pa_total + glicemia_total + bio_total + pico_total
    total_alertas_clinicos = pa_alterada + glicemia_alterada + bio_risco + pico_risco

    return {
        "periodo": {
            "ano": ano,
            "mes": mes,
            "inicio": inicio,
            "fim": fim
        },
        "servicos_rapidos": {
            "total_atendimentos": len(atendimentos_rapidos),
            "total_procedimentos": total_procedimentos,
            "por_tipo_servico": por_tipo_servico,
            "pressao_arterial": {
                "total": pa_total,
                "alteradas": pa_alterada,
                "percentual_alteradas": calcular_percentual(pa_alterada, pa_total)
            },
            "glicemia": {
                "total": glicemia_total,
                "alteradas": glicemia_alterada,
                "percentual_alteradas": calcular_percentual(glicemia_alterada, glicemia_total)
            },
            "bioimpedancia": {
                "total": bio_total,
                "risco": bio_risco,
                "percentual_risco": calcular_percentual(bio_risco, bio_total)
            },
            "pico_fluxo": {
                "total": pico_total,
                "risco": pico_risco,
                "percentual_risco": calcular_percentual(pico_risco, pico_total)
            },
            "total_alertas_clinicos": total_alertas_clinicos
        },
        "consultorio_farmaceutico": {
            "pacientes_convertidos_no_mes": pacientes_convertidos,
            "evolucoes_registradas": evolucoes,
            "desfechos_registrados": len(desfechos),
            "melhora_clinica": melhora_clinica,
            "adesao_tratamento": adesao_tratamento,
            "problemas_resolvidos": resolvidos,
            "percentual_resolucao": calcular_percentual(resolvidos, len(desfechos)),
            "encaminhamentos": encaminhamentos,
            "percentual_encaminhamento": calcular_percentual(encaminhamentos, len(desfechos))
        }
    }

def svc_gerar_pdf_prontuario(
    paciente_clinico_id: int,
    db: Session = None,
    current=None
):
    paciente = db.query(PacienteClinico).filter(
        PacienteClinico.id == paciente_clinico_id
    ).first()

    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente clínico não encontrado")

    prontuario = db.query(ProntuarioClinico).filter(
        ProntuarioClinico.paciente_clinico_id == paciente.id
    ).first()

    evolucoes = []
    if prontuario:
        evolucoes = db.query(EvolucaoClinica).filter(
            EvolucaoClinica.prontuario_id == prontuario.id
        ).order_by(EvolucaoClinica.data_evolucao.desc()).all()

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    elementos = []

    elementos.extend(cabecalho_institucional(styles, "Prontuário Clínico Farmacêutico"))

    dados_paciente = [
        ["Nome", paciente.nome or ""],
        ["Idade", str(calcular_idade(paciente.data_nascimento) or "")],
        ["Sexo", paciente.sexo or ""],
        ["Telefone", paciente.telefone or ""],
        ["Bairro", paciente.bairro or ""],
        ["CPF", paciente.cpf or ""],
        ["CNS", paciente.cns or ""],
        ["Origem", paciente.origem or ""],
    ]

    tabela_paciente = Table(dados_paciente, colWidths=[120, 360])
    tabela_paciente.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e0f2f1")),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#064e3b")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))

    elementos.append(tabela_paciente)
    elementos.append(Spacer(1, 18))

    if prontuario:
        elementos.append(Paragraph("Dados do prontuário", styles["Heading2"]))
        elementos.append(Paragraph(f"Status: {prontuario.status or 'Não informado'}", styles["Normal"]))
        elementos.append(Paragraph(f"Abertura: {prontuario.data_abertura}", styles["Normal"]))
        elementos.append(Spacer(1, 14))

    elementos.append(Paragraph("Evoluções clínicas", styles["Heading2"]))
    elementos.append(Spacer(1, 8))

    if not evolucoes:
        elementos.append(Paragraph("Nenhuma evolução registrada.", styles["Normal"]))
    else:
        for evolucao in evolucoes:
            elementos.append(Paragraph(
                f"<b>{evolucao.tipo_atendimento or 'Evolução clínica'}</b>",
                styles["Heading3"]
            ))
            elementos.append(Paragraph(f"Data: {evolucao.data_evolucao}", styles["Normal"]))

            if evolucao.queixa_principal:
                elementos.append(Paragraph(f"<b>Queixa principal:</b> {evolucao.queixa_principal}", styles["Normal"]))

            if evolucao.avaliacao_farmaceutica:
                elementos.append(Paragraph(f"<b>Avaliação farmacêutica:</b> {evolucao.avaliacao_farmaceutica}", styles["Normal"]))

            if evolucao.problemas_identificados:
                elementos.append(Paragraph(f"<b>Problemas identificados:</b> {evolucao.problemas_identificados}", styles["Normal"]))

            if evolucao.conduta:
                elementos.append(Paragraph(f"<b>Conduta:</b> {evolucao.conduta}", styles["Normal"]))

            if evolucao.plano_acompanhamento:
                elementos.append(Paragraph(f"<b>Plano:</b> {evolucao.plano_acompanhamento}", styles["Normal"]))

            desfechos = db.query(DesfechoClinico).filter(
                DesfechoClinico.evolucao_id == evolucao.id
            ).order_by(DesfechoClinico.data_desfecho.desc()).all()

            if desfechos:
                elementos.append(Spacer(1, 6))
                elementos.append(Paragraph("<b>Desfechos:</b>", styles["Normal"]))

                for desfecho in desfechos:
                    texto = (
                        f"Melhora: {desfecho.melhora_clinica or 'não informado'} | "
                        f"Adesão: {desfecho.adesao_tratamento or 'não informado'} | "
                        f"Resolvido: {'Sim' if desfecho.resolucao_problema else 'Não'}"
                    )
                    elementos.append(Paragraph(texto, styles["Normal"]))

                    if desfecho.resultado_observado:
                        elementos.append(Paragraph(
                            f"Resultado observado: {desfecho.resultado_observado}",
                            styles["Normal"]
                        ))

            elementos.append(Spacer(1, 14))

    doc.build(elementos, onFirstPage=lambda canvas, doc: rodape_institucional(canvas, doc, current), onLaterPages=lambda canvas, doc: rodape_institucional(canvas, doc, current))

    buffer.seek(0)

    nome_arquivo = f"prontuario_paciente_{paciente.id}.pdf"

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename={nome_arquivo}"
        }
    )

def svc_evolucao_farmaceutica_pdf(
    evolucao_id: int,
    db: Session = None,
    current=None
):
    evolucao = db.query(EvolucaoFarmaceutica).filter(
        EvolucaoFarmaceutica.id == evolucao_id
    ).first()

    if not evolucao:
        raise HTTPException(status_code=404, detail="Evolução não encontrada")

    paciente = db.query(PacienteSimplificado).filter(
        PacienteSimplificado.id == evolucao.paciente_simplificado_id
    ).first()

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    elementos = []

    elementos.extend(cabecalho_institucional(styles, "Evolução Farmacêutica - Modelo SOAP"))

    dados_paciente = [
        ["Paciente", getattr(paciente, "nome", "Não informado")],
        ["Idade", getattr(paciente, "idade", "Não informada")],
        ["Sexo", getattr(paciente, "sexo", "Não informado")],
        ["Data", evolucao.criado_em.strftime("%d/%m/%Y %H:%M") if evolucao.criado_em else "Não informada"],
    ]

    tabela_paciente = Table(dados_paciente, colWidths=[150, 350])
    tabela_paciente.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("PADDING", (0, 0), (-1, -1), 7),
    ]))

    elementos.append(tabela_paciente)
    elementos.append(Spacer(1, 16))

    secoes = [
        ("S - Subjetivo", evolucao.subjetivo),
        ("O - Objetivo", evolucao.objetivo),
        ("A - Avaliação farmacêutica", evolucao.avaliacao),
        ("P - Plano de cuidado", evolucao.plano),
        ("PRM/RNM", evolucao.prm),
        ("Adesão", evolucao.adesao),
        ("Metas clínicas", evolucao.metas_clinicas),
        ("Orientações", evolucao.orientacoes),
        ("Encaminhamento", evolucao.encaminhamento),
        ("Risco clínico", evolucao.risco_clinico),
        ("Observações", evolucao.observacoes),
    ]

    for titulo, texto in secoes:
        if texto:
            elementos.append(Paragraph(titulo, styles["Heading2"]))
            elementos.append(Paragraph(str(texto), styles["Normal"]))
            elementos.append(Spacer(1, 8))

    elementos.append(Spacer(1, 42))

    nome_profissional = getattr(current, "nome", "Farmacêutico responsável")
    categoria = getattr(current, "categoria_profissional", "Farmacêutico")
    crf = getattr(current, "crf", None) or "CRF: __________________"

    assinatura = [
        ["________________________________________"],
        [nome_profissional],
        [categoria],
        [crf],
    ]

    tabela_assinatura = Table(assinatura, colWidths=[420])
    tabela_assinatura.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 1), (0, 1), "Helvetica-Bold"),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))

    elementos.append(tabela_assinatura)

    doc.build(elementos, onFirstPage=lambda canvas, doc: rodape_institucional(canvas, doc, current), onLaterPages=lambda canvas, doc: rodape_institucional(canvas, doc, current))
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "inline; filename=evolucao_farmaceutica.pdf"
        }
    )



def _formatar_data(valor):
    if not valor:
        return "—"
    try:
        return valor.strftime("%d/%m/%Y")
    except Exception:
        return str(valor)


def _tabela_simples(linhas, col_widths=None):
    tabela = Table(linhas, colWidths=col_widths or [160, 340])
    tabela.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E0F2F1")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    return tabela


def _dados_paciente_clinico(paciente):
    return [
        ["Campo", "Informação"],
        ["Paciente", paciente.nome or "—"],
        ["Idade", str(calcular_idade(paciente.data_nascimento) or paciente.idade or "—")],
        ["Sexo", paciente.sexo or "—"],
        ["CPF", paciente.cpf or "—"],
        ["CNS", paciente.cns or "—"],
        ["Telefone", paciente.telefone or "—"],
    ]


def svc_plano_cuidado_pdf(paciente_clinico_id: int, db: Session = None, current=None):
    paciente = db.query(PacienteClinico).filter(PacienteClinico.id == paciente_clinico_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente clínico não encontrado")

    metas = db.query(MetaTerapeutica).filter(MetaTerapeutica.paciente_clinico_id == paciente.id).order_by(MetaTerapeutica.criado_em.desc()).all()
    acoes = db.query(AcaoPlanoCuidado).filter(AcaoPlanoCuidado.paciente_clinico_id == paciente.id).order_by(AcaoPlanoCuidado.criado_em.desc()).all()
    planos = db.query(PlanoCuidado).filter(PlanoCuidado.paciente_id == paciente.id).order_by(PlanoCuidado.criado_em.desc()).all()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    elementos = cabecalho_institucional(styles, "Plano de Cuidado Farmacêutico")
    elementos.append(_tabela_simples(_dados_paciente_clinico(paciente)))
    elementos.append(Spacer(1, 14))

    elementos.append(Paragraph("Metas terapêuticas", styles["Heading2"]))
    if metas:
        linhas = [["Meta", "Alvo", "Prazo", "Status"]]
        for m in metas:
            linhas.append([m.descricao or m.parametro or "—", f"{m.valor_alvo or '—'} {m.unidade or ''}", _formatar_data(m.data_prevista or m.prazo), m.status or "—"])
        elementos.append(_tabela_simples(linhas, [190, 100, 90, 100]))
    else:
        elementos.append(Paragraph("Nenhuma meta estruturada registrada.", styles["Normal"]))
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("Ações do plano de cuidado", styles["Heading2"]))
    if acoes:
        linhas = [["Ação", "Responsável", "Prazo", "Status"]]
        for a in acoes:
            linhas.append([a.descricao or a.tipo_acao or "—", a.responsavel or "—", _formatar_data(a.prazo), a.status or "—"])
        elementos.append(_tabela_simples(linhas, [220, 100, 80, 90]))
    else:
        elementos.append(Paragraph("Nenhuma ação estruturada registrada.", styles["Normal"]))
    elementos.append(Spacer(1, 12))

    if planos:
        elementos.append(Paragraph("Plano narrativo/legado", styles["Heading2"]))
        for plano in planos:
            elementos.append(Paragraph(f"<b>Problema:</b> {plano.problema_identificado or '—'}", styles["Normal"]))
            elementos.append(Paragraph(f"<b>Objetivo:</b> {plano.objetivo_terapeutico or '—'}", styles["Normal"]))
            elementos.append(Paragraph(f"<b>Intervenções planejadas:</b> {plano.intervencoes_planejadas or '—'}", styles["Normal"]))
            elementos.append(Spacer(1, 8))

    elementos.extend(assinatura_profissional(current, styles))
    doc.build(elementos, onFirstPage=lambda canvas, doc: rodape_institucional(canvas, doc, current), onLaterPages=lambda canvas, doc: rodape_institucional(canvas, doc, current))
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": f"inline; filename=plano_cuidado_{paciente.id}.pdf"})


def svc_evolucoes_clinicas_pdf(paciente_clinico_id: int, db: Session = None, current=None):
    paciente = db.query(PacienteClinico).filter(PacienteClinico.id == paciente_clinico_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente clínico não encontrado")
    prontuario = db.query(ProntuarioClinico).filter(ProntuarioClinico.paciente_clinico_id == paciente.id).first()
    evolucoes = []
    if prontuario:
        evolucoes = db.query(EvolucaoClinica).filter(EvolucaoClinica.prontuario_id == prontuario.id).order_by(EvolucaoClinica.data_evolucao.desc()).all()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    elementos = cabecalho_institucional(styles, "Evoluções Clínicas Farmacêuticas")
    elementos.append(_tabela_simples(_dados_paciente_clinico(paciente)))
    elementos.append(Spacer(1, 14))

    if not evolucoes:
        elementos.append(Paragraph("Nenhuma evolução clínica registrada.", styles["Normal"]))
    for evolucao in evolucoes:
        elementos.append(Paragraph(f"<b>{evolucao.tipo_atendimento or 'Evolução clínica'}</b> — {_formatar_data(evolucao.data_evolucao)}", styles["Heading3"]))
        for rotulo, valor in [
            ("Queixa principal", evolucao.queixa_principal),
            ("História breve", evolucao.historia_breve),
            ("Avaliação farmacêutica", evolucao.avaliacao_farmaceutica),
            ("Problemas identificados", evolucao.problemas_identificados),
            ("Conduta", evolucao.conduta),
            ("Orientações realizadas", evolucao.orientacoes_realizadas),
            ("Plano de acompanhamento", evolucao.plano_acompanhamento),
            ("Observações", evolucao.observacoes),
        ]:
            if valor:
                elementos.append(Paragraph(f"<b>{rotulo}:</b> {valor}", styles["Normal"]))
        elementos.append(Spacer(1, 10))

    elementos.extend(assinatura_profissional(current, styles))
    doc.build(elementos, onFirstPage=lambda canvas, doc: rodape_institucional(canvas, doc, current), onLaterPages=lambda canvas, doc: rodape_institucional(canvas, doc, current))
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": f"inline; filename=evolucoes_clinicas_{paciente.id}.pdf"})


def svc_orientacoes_farmaceuticas_pdf(paciente_clinico_id: int, db: Session = None, current=None):
    paciente = db.query(PacienteClinico).filter(PacienteClinico.id == paciente_clinico_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente clínico não encontrado")
    prontuario = db.query(ProntuarioClinico).filter(ProntuarioClinico.paciente_clinico_id == paciente.id).first()
    evolucoes = []
    if prontuario:
        evolucoes = db.query(EvolucaoClinica).filter(EvolucaoClinica.prontuario_id == prontuario.id).order_by(EvolucaoClinica.data_evolucao.desc()).all()
    medicamentos = db.query(MedicamentoUso).filter(MedicamentoUso.paciente_clinico_id == paciente.id, MedicamentoUso.ativo == True).order_by(MedicamentoUso.nome_medicamento.asc()).all()
    metas = db.query(MetaTerapeutica).filter(MetaTerapeutica.paciente_clinico_id == paciente.id).order_by(MetaTerapeutica.criado_em.desc()).all()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    elementos = cabecalho_institucional(styles, "Orientações Farmacêuticas ao Paciente")
    elementos.append(_tabela_simples(_dados_paciente_clinico(paciente)))
    elementos.append(Spacer(1, 14))

    elementos.append(Paragraph("Medicamentos em uso", styles["Heading2"]))
    if medicamentos:
        linhas = [["Medicamento", "Dose / via / frequência", "Horários"]]
        for m in medicamentos:
            linhas.append([m.nome_medicamento or "—", f"{m.dose or '—'} · {m.via or '—'} · {m.frequencia_uso or m.frequencia or '—'}", m.horarios_uso or "—"])
        elementos.append(_tabela_simples(linhas, [180, 190, 130]))
    else:
        elementos.append(Paragraph("Nenhum medicamento ativo registrado.", styles["Normal"]))
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("Orientações registradas", styles["Heading2"]))
    orientacoes = [e.orientacoes_realizadas for e in evolucoes if e.orientacoes_realizadas]
    if orientacoes:
        for idx, texto in enumerate(orientacoes[:10], start=1):
            elementos.append(Paragraph(f"{idx}. {texto}", styles["Normal"]))
    else:
        elementos.append(Paragraph("Nenhuma orientação estruturada registrada nas evoluções.", styles["Normal"]))
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("Metas e acompanhamento", styles["Heading2"]))
    if metas:
        for m in metas[:8]:
            elementos.append(Paragraph(f"<b>{m.descricao or m.parametro}</b> — alvo: {m.valor_alvo or '—'} {m.unidade or ''} · prazo: {_formatar_data(m.data_prevista or m.prazo)}", styles["Normal"]))
    else:
        elementos.append(Paragraph("Nenhuma meta terapêutica estruturada registrada.", styles["Normal"]))

    elementos.extend(assinatura_profissional(current, styles))
    doc.build(elementos, onFirstPage=lambda canvas, doc: rodape_institucional(canvas, doc, current), onLaterPages=lambda canvas, doc: rodape_institucional(canvas, doc, current))
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": f"inline; filename=orientacoes_farmaceuticas_{paciente.id}.pdf"})
