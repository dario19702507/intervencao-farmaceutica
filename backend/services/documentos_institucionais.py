from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import Image, Paragraph, Spacer, Table, TableStyle

from models.consultorio_models import AfericaoPA, GlicemiaCapilar, Bioimpedancia, PicoFluxo

BASE_DIR = Path(__file__).resolve().parents[1]
LOGO_DIR = BASE_DIR / "assets" / "logos"
LOGO_FARMACIA = LOGO_DIR / "farmacia_escola.png"
LOGO_UFMS = LOGO_DIR / "ufms.png"

NOME_INSTITUCIONAL = "Farmácia Escola Profa. Ana Maria Cervantes Baraza"
UNIDADE_INSTITUCIONAL = "Instituto Integrado de Saúde – INISA"
UFMS_INSTITUCIONAL = "Fundação Universidade Federal de Mato Grosso do Sul – UFMS"
SISTEMA_INSTITUCIONAL = "Sistema Integrado de Atenção Farmacêutica"


def _logo(path: Path, width: float, height: float):
    if not path.exists():
        return ""
    img = Image(str(path))
    img._restrictSize(width, height)
    return img


def cabecalho_institucional(styles, titulo: str | None = None):
    """Retorna elementos de cabeçalho institucional para PDFs ReportLab."""
    logo_fe = _logo(LOGO_FARMACIA, 3.0 * cm, 1.8 * cm)
    logo_ufms = _logo(LOGO_UFMS, 5.0 * cm, 1.8 * cm)
    bloco_texto = [
        Paragraph(f"<b>{NOME_INSTITUCIONAL}</b>", styles["Normal"]),
        Paragraph(UNIDADE_INSTITUCIONAL, styles["Normal"]),
        Paragraph(UFMS_INSTITUCIONAL, styles["Normal"]),
        Paragraph(SISTEMA_INSTITUCIONAL, styles["Normal"]),
    ]
    tabela = Table([[logo_fe, bloco_texto, logo_ufms]], colWidths=[3.2 * cm, 9.5 * cm, 5.2 * cm])
    tabela.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "LEFT"),
        ("ALIGN", (2, 0), (2, 0), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#CBD5E1")),
    ]))
    elementos = [tabela, Spacer(1, 12)]
    if titulo:
        elementos.append(Paragraph(titulo, styles["Title"]))
        elementos.append(Spacer(1, 12))
    return elementos


def rodape_institucional(canvas, doc, usuario: Any = None):
    canvas.saveState()
    usuario_nome = getattr(usuario, "nome", None) or getattr(usuario, "email", None) or "usuário autenticado"
    texto = (
        f"Documento emitido eletronicamente pelo {SISTEMA_INSTITUCIONAL} · "
        f"{datetime.now().strftime('%d/%m/%Y %H:%M')} · Responsável: {usuario_nome}"
    )
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#64748B"))
    canvas.drawString(doc.leftMargin, 0.75 * cm, texto[:150])
    canvas.restoreState()


def assinatura_profissional(current, styles):
    nome_profissional = getattr(current, "nome", "Farmacêutico responsável")
    categoria = getattr(current, "categoria_profissional", "Farmacêutico")
    crf = getattr(current, "crf", None) or "CRF: __________________"
    assinatura = [["________________________________________"], [nome_profissional], [categoria], [crf]]
    tabela = Table(assinatura, colWidths=[420])
    tabela.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 1), (0, 1), "Helvetica-Bold"),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))
    return [Spacer(1, 46), tabela]


def tabela_resultados_servico(atendimento, db, styles):
    """Monta tabela com resultados clínicos do serviço rápido, quando disponíveis."""
    linhas: list[list[str]] = [["Resultado", "Valor"]]
    tipo = (getattr(atendimento, "tipo_servico", "") or "").lower()
    atendimento_id = atendimento.id

    pa = db.query(AfericaoPA).filter(AfericaoPA.atendimento_rapido_id == atendimento_id).first()
    glicemia = db.query(GlicemiaCapilar).filter(GlicemiaCapilar.atendimento_rapido_id == atendimento_id).first()
    bio = db.query(Bioimpedancia).filter(Bioimpedancia.atendimento_rapido_id == atendimento_id).first()
    pico = db.query(PicoFluxo).filter(PicoFluxo.atendimento_rapido_id == atendimento_id).first()

    if pa:
        linhas.append(["Pressão arterial", f"{pa.pressao_sistolica}/{pa.pressao_diastolica} mmHg"])
        if pa.frequencia_cardiaca is not None:
            linhas.append(["Frequência cardíaca", f"{pa.frequencia_cardiaca} bpm"])
        if pa.classificacao:
            linhas.append(["Classificação", pa.classificacao])
    if glicemia:
        linhas.append(["Glicemia capilar", f"{glicemia.valor_glicemia} mg/dL"])
        if glicemia.tipo_jejum:
            linhas.append(["Condição", glicemia.tipo_jejum])
        if glicemia.classificacao:
            linhas.append(["Classificação", glicemia.classificacao])
    if bio:
        if bio.peso is not None:
            linhas.append(["Peso", f"{bio.peso} kg"])
        if bio.imc is not None:
            linhas.append(["IMC", str(bio.imc)])
        if bio.percentual_gordura is not None:
            linhas.append(["Gordura corporal", f"{bio.percentual_gordura} %"])
        if bio.classificacao_imc:
            linhas.append(["Classificação IMC", bio.classificacao_imc])
    if pico:
        linhas.append(["Pico de fluxo expiratório", f"{pico.valor_medido} L/min"])
        if pico.percentual_previsto is not None:
            linhas.append(["Percentual previsto", f"{pico.percentual_previsto} %"])
        if pico.classificacao:
            linhas.append(["Classificação", pico.classificacao])

    if len(linhas) == 1:
        linhas.append(["Resultado", "Não há resultado estruturado vinculado a este atendimento."])

    tabela = Table(linhas, colWidths=[180, 320])
    tabela.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E0F2F1")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("PADDING", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return [Paragraph("Resultado do serviço prestado", styles["Heading2"]), tabela, Spacer(1, 14)]
