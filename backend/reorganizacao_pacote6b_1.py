from pathlib import Path
from datetime import datetime

BASE = Path.cwd()
ROUTERS = BASE / 'routers'
MAIN = BASE / 'main.py'
BIO = ROUTERS / 'bioimpedancia.py'
BACKUP_DIR = BASE / f"backup_reorganizacao_pacote6b_1_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
BACKUP_DIR.mkdir(exist_ok=True)

for p in [MAIN, BIO]:
    if p.exists():
        (BACKUP_DIR / p.name).write_text(p.read_text(encoding='utf-8'), encoding='utf-8')

bio_code = r'''from io import BytesIO
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

# Import provisório a partir do módulo legado.
# No pacote final de models, Bioimpedancia, AtendimentoRapido e PacienteSimplificado
# devem vir de models/consultorio_models.py.
from routers.consultorio import (
    Bioimpedancia,
    AtendimentoRapido,
    PacienteSimplificado,
    get_db_consultorio,
    get_current_user_consultorio,
)

router = APIRouter(
    prefix="/consultorio",
    tags=["Bioimpedância"]
)


def _texto(valor):
    return str(valor) if valor not in [None, ""] else "Não informado"


@router.get("/paciente-simplificado/{paciente_id}/bioimpedancia-historico")
def historico_bioimpedancia_paciente(
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
        AtendimentoRapido.data_atendimento.asc()
    ).all()

    historico = []

    for atendimento in atendimentos:
        bio = db.query(Bioimpedancia).filter(
            Bioimpedancia.atendimento_rapido_id == atendimento.id
        ).first()

        if not bio:
            continue

        historico.append({
            "atendimento_id": atendimento.id,
            "data": atendimento.data_atendimento,
            "peso": getattr(bio, "peso", None),
            "altura": getattr(bio, "altura", None),
            "imc": getattr(bio, "imc", None),
            "classificacao_imc": getattr(bio, "classificacao_imc", None),
            "percentual_gordura": getattr(bio, "percentual_gordura", None),
            "percentual_massa_muscular": getattr(bio, "percentual_massa_muscular", None),
            "gordura_visceral": getattr(bio, "gordura_visceral", None),
            "classificacao_gordura_visceral": getattr(
                bio,
                "classificacao_gordura_visceral",
                None
            ),
            "fmi": getattr(bio, "fmi", None),
            "ffmi": getattr(bio, "ffmi", None),
            "relacao_gordura_musculo": getattr(
                bio,
                "relacao_gordura_musculo",
                None
            ),
            "metabolismo_basal": getattr(bio, "metabolismo_basal", None),
            "idade_corporal": getattr(bio, "idade_corporal", None),
            "observacoes": getattr(bio, "observacoes", None),
        })

    return {
        "paciente": {
            "id": paciente.id,
            "nome": paciente.nome,
            "idade": paciente.idade,
            "sexo": paciente.sexo,
            "bairro": paciente.bairro,
        },
        "total_avaliacoes": len(historico),
        "historico": historico
    }


@router.get("/paciente-simplificado/{paciente_id}/bioimpedancia-comparativo")
def comparativo_bioimpedancia_paciente(
    paciente_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    historico_response = historico_bioimpedancia_paciente(
        paciente_id=paciente_id,
        db=db,
        current=current
    )

    historico = historico_response.get("historico", [])

    if len(historico) < 2:
        return {
            "comparativo_disponivel": False,
            "mensagem": "São necessárias pelo menos duas avaliações de bioimpedância para comparação.",
            "comparacoes": [],
            "resumo": "Histórico insuficiente",
            "favoraveis": 0,
            "desfavoraveis": 0
        }

    primeira = historico[0]
    ultima = historico[-1]

    campos = [
        ("peso", "Peso", "menor_melhor"),
        ("imc", "IMC", "menor_melhor"),
        ("percentual_gordura", "% gordura corporal", "menor_melhor"),
        ("percentual_massa_muscular", "% massa muscular", "maior_melhor"),
        ("gordura_visceral", "Gordura visceral", "menor_melhor"),
        ("fmi", "FMI", "menor_melhor"),
        ("ffmi", "FFMI", "maior_melhor"),
    ]

    comparacoes = []
    favoraveis = 0
    desfavoraveis = 0

    for chave, rotulo, regra in campos:
        valor_inicial = primeira.get(chave)
        valor_final = ultima.get(chave)

        if valor_inicial is None or valor_final is None:
            continue

        try:
            diferenca = round(float(valor_final) - float(valor_inicial), 2)
        except Exception:
            continue

        if diferenca > 0:
            tendencia = "aumento"
        elif diferenca < 0:
            tendencia = "redução"
        else:
            tendencia = "estável"

        avaliacao = "neutra"

        if regra == "menor_melhor":
            if diferenca < 0:
                avaliacao = "favoravel"
                favoraveis += 1
            elif diferenca > 0:
                avaliacao = "desfavoravel"
                desfavoraveis += 1

        if regra == "maior_melhor":
            if diferenca > 0:
                avaliacao = "favoravel"
                favoraveis += 1
            elif diferenca < 0:
                avaliacao = "desfavoravel"
                desfavoraveis += 1

        comparacoes.append({
            "indicador": rotulo,
            "valor_inicial": valor_inicial,
            "valor_final": valor_final,
            "diferenca": diferenca,
            "tendencia": tendencia,
            "avaliacao": avaliacao
        })

    if favoraveis > desfavoraveis:
        resumo = "Evolução favorável"
    elif desfavoraveis > favoraveis:
        resumo = "Evolução desfavorável"
    else:
        resumo = "Evolução parcialmente favorável"

    return {
        "comparativo_disponivel": True,
        "data_inicial": primeira.get("data"),
        "data_final": ultima.get("data"),
        "resumo": resumo,
        "favoraveis": favoraveis,
        "desfavoraveis": desfavoraveis,
        "comparacoes": comparacoes
    }


@router.get("/bioimpedancia/{bioimpedancia_id}/laudo-pdf")
def laudo_bioimpedancia_pdf(
    bioimpedancia_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
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

    elementos.append(Paragraph("FARMÁCIA ESCOLA", styles["Title"]))
    elementos.append(Paragraph("PROFª ANA MARIA CERVANTES BARAZA", styles["Heading2"]))
    elementos.append(Paragraph("Universidade Federal de Mato Grosso do Sul", styles["Normal"]))
    elementos.append(Spacer(1, 14))

    elementos.append(Paragraph("Laudo de Avaliação por Bioimpedância", styles["Title"]))
    elementos.append(Spacer(1, 12))

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

    doc.build(elementos)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "inline; filename=laudo_bioimpedancia.pdf"
        }
    )
'''

BIO.write_text(bio_code, encoding='utf-8')

main_text = MAIN.read_text(encoding='utf-8')
if 'from routers.bioimpedancia import router as bioimpedancia_router' not in main_text:
    marker = 'from routers.consultorio import router as consultorio_router\n'
    if marker in main_text:
        main_text = main_text.replace(marker, marker + 'from routers.bioimpedancia import router as bioimpedancia_router\n')
    else:
        main_text = 'from routers.bioimpedancia import router as bioimpedancia_router\n' + main_text

if 'app.include_router(bioimpedancia_router)' not in main_text:
    marker = 'app.include_router(consultorio_router)\n'
    if marker in main_text:
        main_text = main_text.replace(marker, marker + 'app.include_router(bioimpedancia_router)\n')
    else:
        insert_after = 'app = FastAPI(title="Sistema de Intervenção Farmacêutica", version="1.0.0")\n'
        main_text = main_text.replace(insert_after, insert_after + 'app.include_router(bioimpedancia_router)\n')

MAIN.write_text(main_text, encoding='utf-8')

resultado = BASE / 'README_reorganizacao_pacote6b_1_resultado.md'
resultado.write_text(f'''# Resultado - Reorganização Pacote 6B-1

Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

## Ações realizadas

- Backup automático em `{BACKUP_DIR.name}`.
- Criado/atualizado `routers/bioimpedancia.py`.
- Adicionado import de `bioimpedancia_router` ao `main.py`, quando necessário.
- Adicionado `app.include_router(bioimpedancia_router)` ao `main.py`, quando necessário.
- Nenhuma rota foi removida de `routers/consultorio.py` nesta etapa.

## Rotas migradas para teste

- `GET /consultorio/paciente-simplificado/{{paciente_id}}/bioimpedancia-historico`
- `GET /consultorio/paciente-simplificado/{{paciente_id}}/bioimpedancia-comparativo`
- `GET /consultorio/bioimpedancia/{{bioimpedancia_id}}/laudo-pdf`

## Próximos comandos

```bash
python -m py_compile routers/bioimpedancia.py
python -m py_compile main.py
uvicorn main:app --reload
```

Depois teste as rotas no Swagger. Se estiverem funcionando, seguimos para o Pacote 6B-2, removendo as duplicadas do `consultorio.py`.
''', encoding='utf-8')

print('Pacote 6B-1 aplicado com sucesso.')
print(f'Relatório: {resultado.name}')
print(f'Backup: {BACKUP_DIR.name}')
