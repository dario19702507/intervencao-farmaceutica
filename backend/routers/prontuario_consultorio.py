from io import BytesIO
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from routers.consultorio import get_db_consultorio, get_current_user_consultorio
from models.consultorio_models import (
    PacienteClinico, ProntuarioClinico, AtendimentoRapido, AfericaoPA,
    GlicemiaCapilar, Bioimpedancia, PicoFluxo, EvolucaoClinica,
    DesfechoClinico, MedicamentoUso, IntervencaoFarmacoterapia,
    DesfechoIntervencaoFarmacoterapia, EvolucaoFarmaceutica,
)
from services.consultorio_helpers import calcular_idade
from services.relatorios_consultorio import svc_gerar_pdf_prontuario
from services.farmacoterapia import montar_avaliacao_polifarmacia

router = APIRouter(prefix="/consultorio", tags=["Consultório - Prontuário"])


def avaliar_polifarmacia(paciente_id: int, db: Session, current=None):
    return montar_avaliacao_polifarmacia(paciente_id=paciente_id, db=db)


@router.get("/paciente-clinico/{paciente_clinico_id}/prontuario-longitudinal-pdf")
def gerar_pdf_prontuario_longitudinal(
    paciente_clinico_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    paciente = db.query(PacienteClinico).filter(
        PacienteClinico.id == paciente_clinico_id
    ).first()

    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente clínico não encontrado")

    prontuario = db.query(ProntuarioClinico).filter(
        ProntuarioClinico.paciente_clinico_id == paciente.id
    ).first()

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()
    elementos = []

    def texto(valor):
        return str(valor) if valor not in [None, ""] else "Não informado"

    def adicionar_titulo(titulo):
        elementos.append(Spacer(1, 14))
        elementos.append(Paragraph(titulo, styles["Heading2"]))
        elementos.append(Spacer(1, 6))

    def adicionar_tabela(linhas, col1=150, col2=360):
        tabela = Table(linhas, colWidths=[col1, col2])
        tabela.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e0f2f1")),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        elementos.append(tabela)

    elementos.append(Paragraph("Prontuário Longitudinal Farmacêutico", styles["Title"]))
    elementos.append(Paragraph("Farmácia Escola Profª Ana Maria Cervantes Baraza", styles["Normal"]))
    elementos.append(Spacer(1, 14))

    adicionar_titulo("1. Identificação completa")
    adicionar_tabela([
        ["Nome", texto(paciente.nome)],
        ["Data de nascimento", texto(paciente.data_nascimento)],
        ["Idade", texto(calcular_idade(paciente.data_nascimento) or paciente.idade)],
        ["Sexo", texto(paciente.sexo)],
        ["Telefone", texto(paciente.telefone)],
        ["CPF", texto(paciente.cpf)],
        ["CNS", texto(paciente.cns)],
        ["Nome da mãe", texto(paciente.nome_mae)],
        ["Endereço", texto(paciente.endereco)],
        ["Bairro", texto(paciente.bairro)],
        ["Origem", texto(paciente.origem)],
    ])

    adicionar_titulo("2. Perfil clínico ampliado")
    adicionar_tabela([
        ["CID principal", texto(paciente.cid_principal)],
        ["CID secundário", texto(paciente.cid_secundario)],
        ["Comorbidades", texto(paciente.comorbidades)],
        ["Alergias", texto(paciente.alergias)],
        ["Tabagismo", texto(paciente.tabagismo)],
        ["Etilismo", texto(paciente.etilismo)],
        ["Atividade física", texto(paciente.atividade_fisica)],
        ["Histórico familiar", texto(paciente.historico_familiar)],
        ["Pessoa com deficiência", "Sim" if paciente.pessoa_com_deficiencia else "Não"],
        ["Tipo de deficiência", texto(paciente.tipo_deficiencia)],
        ["Vacinação influenza", "Sim" if paciente.vacinacao_influenza else "Não"],
        ["Vacinação COVID-19", "Sim" if paciente.vacinacao_covid else "Não"],
        ["Adesão terapêutica", texto(paciente.adesao_terapeutica)],
        ["Meta pressórica", texto(paciente.meta_pressao_arterial)],
        ["Meta glicêmica", texto(paciente.meta_glicemica)],
        ["Meta de peso", texto(paciente.meta_peso)],
        ["Observações clínicas", texto(paciente.observacoes_clinicas)],
    ])

    adicionar_titulo("3. Dados do prontuário")
    if prontuario:
        adicionar_tabela([
            ["Status", texto(prontuario.status)],
            ["Data de abertura", texto(prontuario.data_abertura)],
            ["Observações", texto(prontuario.observacoes)],
        ])
    else:
        elementos.append(Paragraph("Prontuário clínico não localizado.", styles["Normal"]))

    eventos_timeline = []

    adicionar_titulo("4. Histórico de serviços rápidos")

    if paciente.paciente_simplificado_origem_id:
        atendimentos = db.query(AtendimentoRapido).filter(
            AtendimentoRapido.paciente_simplificado_id == paciente.paciente_simplificado_origem_id
        ).order_by(AtendimentoRapido.data_atendimento.asc()).all()

        if not atendimentos:
            elementos.append(Paragraph("Nenhum serviço rápido registrado.", styles["Normal"]))
        else:
            for atendimento in atendimentos:
                elementos.append(Paragraph(
                    f"<b>Atendimento em {atendimento.data_atendimento}</b> — {texto(atendimento.tipo_servico)}",
                    styles["Heading3"]
                ))

                pa = db.query(AfericaoPA).filter(
                    AfericaoPA.atendimento_rapido_id == atendimento.id
                ).first()

                glicemia = db.query(GlicemiaCapilar).filter(
                    GlicemiaCapilar.atendimento_rapido_id == atendimento.id
                ).first()

                bio = db.query(Bioimpedancia).filter(
                    Bioimpedancia.atendimento_rapido_id == atendimento.id
                ).first()

                pico = db.query(PicoFluxo).filter(
                    PicoFluxo.atendimento_rapido_id == atendimento.id
                ).first()

                if pa:
                    adicionar_tabela([
                        ["Pressão arterial", f"{pa.pressao_sistolica}/{pa.pressao_diastolica} mmHg"],
                        ["Frequência cardíaca", texto(pa.frequencia_cardiaca)],
                        ["Classificação", texto(pa.classificacao)],
                        ["Observações", texto(pa.observacoes)],
                    ])
                    eventos_timeline.append([atendimento.data_atendimento, "Serviço rápido", "Pressão arterial", f"{pa.pressao_sistolica}/{pa.pressao_diastolica} mmHg - {texto(pa.classificacao)}"])

                if glicemia:
                    adicionar_tabela([
                        ["Glicemia capilar", f"{glicemia.valor_glicemia} mg/dL"],
                        ["Tipo de jejum", texto(glicemia.tipo_jejum)],
                        ["Classificação", texto(glicemia.classificacao)],
                        ["Observações", texto(glicemia.observacoes)],
                    ])
                    eventos_timeline.append([atendimento.data_atendimento, "Serviço rápido", "Glicemia capilar", f"{glicemia.valor_glicemia} mg/dL - {texto(glicemia.classificacao)}"])

                if bio:
                    adicionar_tabela([
                        ["Peso", texto(bio.peso)],
                        ["Altura", texto(bio.altura)],
                        ["IMC", texto(bio.imc)],
                        ["Classificação IMC", texto(bio.classificacao_imc or bio.classificacao)],
                        ["Gordura corporal (%)", texto(bio.percentual_gordura)],
                        ["Massa muscular (%)", texto(bio.percentual_massa_muscular)],
                        ["Gordura visceral", texto(bio.gordura_visceral)],
                        ["Classificação gordura visceral", texto(bio.classificacao_gordura_visceral)],
                        ["Risco cardiometabólico", texto(bio.risco_cardiometabolico)],
                        ["Alertas", texto(bio.alertas)],
                        ["Observações", texto(bio.observacoes)],
                    ])
                    eventos_timeline.append([atendimento.data_atendimento, "Serviço rápido", "Bioimpedância", f"IMC {texto(bio.imc)} - Risco {texto(bio.risco_cardiometabolico)}"])

                if pico:
                    adicionar_tabela([
                        ["Pico de fluxo medido", texto(pico.valor_medido)],
                        ["Valor previsto", texto(pico.valor_previsto)],
                        ["Percentual previsto", texto(pico.percentual_previsto)],
                        ["Classificação", texto(pico.classificacao)],
                        ["Observações", texto(pico.observacoes)],
                    ])
                    eventos_timeline.append([atendimento.data_atendimento, "Serviço rápido", "Pico de fluxo", f"{pico.valor_medido} L/min - {texto(pico.classificacao)}"])

                elementos.append(Spacer(1, 8))
    else:
        elementos.append(Paragraph("Paciente não possui vínculo com cadastro simplificado.", styles["Normal"]))

    adicionar_titulo("5. Evoluções farmacêuticas SOAP")

    if paciente.paciente_simplificado_origem_id:
        evolucoes_farmaceuticas = db.query(EvolucaoFarmaceutica).filter(
            EvolucaoFarmaceutica.paciente_simplificado_id == paciente.paciente_simplificado_origem_id
        ).order_by(EvolucaoFarmaceutica.criado_em.asc()).all()
    else:
        evolucoes_farmaceuticas = []

    if not evolucoes_farmaceuticas:
        elementos.append(Paragraph("Nenhuma evolução farmacêutica SOAP registrada.", styles["Normal"]))
    else:
        for e in evolucoes_farmaceuticas:
            elementos.append(Paragraph(f"<b>Evolução em {e.criado_em}</b>", styles["Heading3"]))
            adicionar_tabela([
                ["S - Subjetivo", texto(e.subjetivo)],
                ["O - Objetivo", texto(e.objetivo)],
                ["A - Avaliação", texto(e.avaliacao)],
                ["P - Plano", texto(e.plano)],
                ["PRM/RNM", texto(e.prm)],
                ["Adesão", texto(e.adesao)],
                ["Metas clínicas", texto(e.metas_clinicas)],
                ["Orientações", texto(e.orientacoes)],
                ["Encaminhamento", texto(e.encaminhamento)],
                ["Risco clínico", texto(e.risco_clinico)],
                ["Observações", texto(e.observacoes)],
            ])
            eventos_timeline.append([e.criado_em, "Cuidado farmacêutico", "Evolução SOAP", texto(e.avaliacao or e.plano or e.subjetivo)])

    adicionar_titulo("6. Evoluções clínicas do consultório")

    if prontuario:
        evolucoes = db.query(EvolucaoClinica).filter(
            EvolucaoClinica.prontuario_id == prontuario.id
        ).order_by(EvolucaoClinica.data_evolucao.asc()).all()
    else:
        evolucoes = []

    if not evolucoes:
        elementos.append(Paragraph("Nenhuma evolução clínica registrada.", styles["Normal"]))
    else:
        for e in evolucoes:
            elementos.append(Paragraph(f"<b>{texto(e.tipo_atendimento)} — {e.data_evolucao}</b>", styles["Heading3"]))
            adicionar_tabela([
                ["Queixa principal", texto(e.queixa_principal)],
                ["História breve", texto(e.historia_breve)],
                ["Avaliação farmacêutica", texto(e.avaliacao_farmaceutica)],
                ["Problemas identificados", texto(e.problemas_identificados)],
                ["Conduta", texto(e.conduta)],
                ["Orientações realizadas", texto(e.orientacoes_realizadas)],
                ["Plano de acompanhamento", texto(e.plano_acompanhamento)],
                ["Necessidade de retorno", "Sim" if e.necessidade_retorno else "Não"],
                ["Data de retorno sugerida", texto(e.data_retorno_sugerida)],
                ["Observações", texto(e.observacoes)],
            ])
            eventos_timeline.append([e.data_evolucao, "Consultório", texto(e.tipo_atendimento or "Evolução clínica"), texto(e.avaliacao_farmaceutica or e.conduta or e.queixa_principal)])

            desfechos = db.query(DesfechoClinico).filter(
                DesfechoClinico.evolucao_id == e.id
            ).order_by(DesfechoClinico.data_desfecho.asc()).all()

            for d in desfechos:
                elementos.append(Paragraph("<b>Desfecho clínico vinculado</b>", styles["Heading3"]))
                adicionar_tabela([
                    ["Data", texto(d.data_desfecho)],
                    ["Melhora clínica", texto(d.melhora_clinica)],
                    ["Adesão ao tratamento", texto(d.adesao_tratamento)],
                    ["Resolução do problema", "Sim" if d.resolucao_problema else "Não"],
                    ["Necessidade de encaminhamento", "Sim" if d.necessidade_encaminhamento else "Não"],
                    ["Encaminhamento realizado", texto(d.encaminhamento_realizado)],
                    ["Resultado observado", texto(d.resultado_observado)],
                    ["Observações", texto(d.observacoes)],
                ])
                eventos_timeline.append([d.data_desfecho, "Desfecho", "Desfecho clínico", texto(d.resultado_observado or d.observacoes)])

    adicionar_titulo("7. Farmacoterapia em uso")

    medicamentos = db.query(MedicamentoUso).filter(
        MedicamentoUso.paciente_clinico_id == paciente.id
    ).order_by(MedicamentoUso.criado_em.asc()).all()

    if not medicamentos:
        elementos.append(Paragraph("Nenhum medicamento em uso registrado.", styles["Normal"]))
    else:
        for m in medicamentos:
            adicionar_tabela([
                ["Medicamento", texto(m.nome_medicamento)],
                ["Dose", texto(m.dose)],
                ["Via", texto(m.via)],
                ["Frequência", texto(m.frequencia)],
                ["Indicação", texto(m.indicacao)],
                ["Uso contínuo", "Sim" if m.uso_continuo else "Não"],
                ["Adesão referida", texto(m.adesao_referida)],
                ["Ativo", "Sim" if m.ativo else "Não"],
                ["Observações", texto(m.observacoes)],
            ])
            eventos_timeline.append([m.criado_em, "Farmacoterapia", texto(m.nome_medicamento), f"{texto(m.dose)} {texto(m.via)} {texto(m.frequencia)}"])

    adicionar_titulo("8. Avaliação farmacoterapêutica automatizada")

    avaliacao_polifarmacia = avaliar_polifarmacia(
        paciente_id=paciente.id,
        db=db,
        current=current
    )

    adicionar_tabela([
        ["Medicamentos ativos", texto(avaliacao_polifarmacia.get("total_medicamentos"))],
        ["Polifarmácia", "Sim" if avaliacao_polifarmacia.get("polifarmacia") else "Não"],
        ["Risco farmacoterapêutico", texto(avaliacao_polifarmacia.get("risco"))],
        ["Score", texto(avaliacao_polifarmacia.get("score"))],
        ["Interpretação", texto(avaliacao_polifarmacia.get("interpretacao"))],
    ])

    adicionar_tabela([
        ["Alertas", "; ".join(avaliacao_polifarmacia.get("alertas", [])) or "Nenhum alerta"],
        ["Recomendações", "; ".join(avaliacao_polifarmacia.get("recomendacoes", [])) or "Nenhuma recomendação"],
        ["Interações", "; ".join(avaliacao_polifarmacia.get("interacoes", [])) or "Nenhuma interação identificada"],
        ["Duplicidades", "; ".join(avaliacao_polifarmacia.get("duplicidades", [])) or "Nenhuma duplicidade identificada"],
        ["Medicamentos potencialmente inapropriados", "; ".join(avaliacao_polifarmacia.get("potencialmente_inapropriados", [])) or "Nenhum identificado"],
    ])

    adicionar_titulo("9. Intervenções farmacoterapêuticas")

    intervencoes = db.query(IntervencaoFarmacoterapia).filter(
        IntervencaoFarmacoterapia.paciente_clinico_id == paciente.id
    ).order_by(IntervencaoFarmacoterapia.criado_em.asc()).all()

    if not intervencoes:
        elementos.append(Paragraph("Nenhuma intervenção farmacoterapêutica registrada.", styles["Normal"]))
    else:
        for i in intervencoes:
            elementos.append(Paragraph(f"<b>{texto(i.tipo_intervencao)} — {i.criado_em}</b>", styles["Heading3"]))
            adicionar_tabela([
                ["Tipo de intervenção", texto(i.tipo_intervencao)],
                ["Descrição", texto(i.descricao)],
                ["Conduta", texto(i.conduta)],
                ["Aceita pelo paciente", "Sim" if i.aceita_pelo_paciente else "Não"],
                ["Necessidade de encaminhamento", "Sim" if i.necessidade_encaminhamento else "Não"],
                ["Observações", texto(i.observacoes)],
            ])
            eventos_timeline.append([i.criado_em, "Intervenção farmacoterapêutica", texto(i.tipo_intervencao), texto(i.descricao or i.conduta)])

            desfechos_i = db.query(DesfechoIntervencaoFarmacoterapia).filter(
                DesfechoIntervencaoFarmacoterapia.intervencao_id == i.id
            ).order_by(DesfechoIntervencaoFarmacoterapia.criado_em.asc()).all()

            for d in desfechos_i:
                elementos.append(Paragraph("<b>Desfecho da intervenção</b>", styles["Heading3"]))
                adicionar_tabela([
                    ["Status", texto(d.status_desfecho)],
                    ["Resultado observado", texto(d.resultado_observado)],
                    ["Necessidade de nova intervenção", "Sim" if d.necessidade_nova_intervencao else "Não"],
                    ["Observações", texto(d.observacoes)],
                ])
                eventos_timeline.append([d.criado_em, "Desfecho", "Desfecho da intervenção", texto(d.status_desfecho)])

    adicionar_titulo("10. Linha do tempo longitudinal consolidada")

    eventos_timeline = sorted(eventos_timeline, key=lambda x: x[0] or datetime.min)

    if not eventos_timeline:
        elementos.append(Paragraph("Nenhum evento longitudinal consolidado.", styles["Normal"]))
    else:
        tabela_eventos = [["Data", "Origem", "Evento", "Descrição"]]

        for data, origem, evento, descricao in eventos_timeline:
            data_txt = data.strftime("%d/%m/%Y %H:%M") if data else "-"
            tabela_eventos.append([data_txt, origem, evento, descricao])

        tabela = Table(tabela_eventos, colWidths=[80, 100, 120, 230], repeatRows=1)
        tabela.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 5),
        ]))
        elementos.append(tabela)

    adicionar_titulo("11. Síntese farmacêutica")
    elementos.append(Paragraph(
        "Este prontuário longitudinal consolida dados cadastrais, perfil clínico ampliado, "
        "serviços rápidos, evoluções farmacêuticas, evoluções clínicas, farmacoterapia, "
        "intervenções e desfechos registrados no sistema. A interpretação clínica deve "
        "considerar a qualidade, completude e atualização dos registros.",
        styles["Normal"]
    ))

    elementos.append(Spacer(1, 36))

    nome_profissional = getattr(current, "nome", "Farmacêutico responsável")
    categoria = getattr(current, "categoria_profissional", "Farmacêutico")
    crf = getattr(current, "crf", None) or "CRF: __________________"

    assinatura = Table([
        ["________________________________________"],
        [nome_profissional],
        [categoria],
        [crf],
    ], colWidths=[420])

    assinatura.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 1), (0, 1), "Helvetica-Bold"),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))

    elementos.append(assinatura)

    doc.build(elementos)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition":
            f"inline; filename=prontuario_longitudinal_{paciente.id}.pdf"
        }
    )

@router.get("/paciente-clinico/{paciente_clinico_id}/pdf")
def gerar_pdf_prontuario(
    paciente_clinico_id: int,
    db: Session = Depends(get_db_consultorio)
):
    return svc_gerar_pdf_prontuario(paciente_clinico_id=paciente_clinico_id, db=db)

