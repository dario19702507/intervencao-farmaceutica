"""Serviço de OCR/extração inicial de documentos.

Correção 12A.1: evita leitura binária bruta de PDFs como texto. O fluxo agora é:
1) tenta extrair texto pesquisável com PyMuPDF;
2) tenta pypdf como alternativa;
3) se o PDF for imagem/scaneado, tenta OCR via PyMuPDF + pytesseract;
4) se não houver OCR disponível, retorna texto vazio e status explicativo.

Nenhuma sugestão atualiza automaticamente paciente, vigência, agenda ou WhatsApp.
"""

from __future__ import annotations

import json
import re
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Optional, Tuple

from services.extratores.lme_extractor import extrair_campos_lme


def _limpar_texto(texto: str) -> str:
    texto = texto or ""
    texto = texto.replace("\x00", " ")
    texto = texto.replace("\r", "\n")
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def _texto_parece_lixo_pdf(texto: str) -> bool:
    """Detecta extração indevida de bytes internos de PDF.

    Quando aparecem muitos marcadores como obj/stream/endstream, normalmente o
    arquivo foi lido como texto binário, o que não é informação clínica útil.
    """
    if not texto:
        return False
    amostra = texto[:5000]
    marcadores = ["%PDF", " obj", "endobj", "stream", "endstream", "/XObject", "/Filter", "DCTDecode", "FlateDecode"]
    pontos = sum(1 for m in marcadores if m in amostra)
    caracteres_ruins = len(re.findall(r"[\x00-\x08\x0b\x0c\x0e-\x1f�]", amostra))
    return pontos >= 3 or caracteres_ruins > 20


def _extrair_pdf_pymupdf_texto(caminho: Path) -> str:
    try:
        import fitz  # type: ignore
    except Exception:
        return ""

    partes = []
    try:
        with fitz.open(str(caminho)) as pdf:
            for pagina in pdf:
                partes.append(pagina.get_text("text") or "")
    except Exception:
        return ""
    texto = _limpar_texto("\n".join(partes))
    if _texto_parece_lixo_pdf(texto):
        return ""
    return texto


def _extrair_pdf_pypdf(caminho: Path) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        try:
            from PyPDF2 import PdfReader  # type: ignore
        except Exception:
            return ""

    partes = []
    try:
        reader = PdfReader(str(caminho))
        for page in reader.pages:
            try:
                partes.append(page.extract_text() or "")
            except Exception:
                continue
    except Exception:
        return ""
    texto = _limpar_texto("\n".join(partes))
    if _texto_parece_lixo_pdf(texto):
        return ""
    return texto


def _tesseract_disponivel() -> bool:
    try:
        import pytesseract  # type: ignore

        # Se tesseract.exe estiver no PATH, melhor. Caso contrário, pytesseract
        # ainda pode estar configurado manualmente pelo usuário.
        if shutil.which("tesseract"):
            return True
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False
    except Exception:
        return False


def _ocr_pdf_imagem(caminho: Path) -> str:
    """Renderiza PDF scaneado e aplica OCR quando Tesseract está disponível."""
    if not _tesseract_disponivel():
        return ""

    try:
        import fitz  # type: ignore
        import pytesseract  # type: ignore
        from PIL import Image  # type: ignore
    except Exception:
        return ""

    textos = []
    try:
        with fitz.open(str(caminho)) as pdf, tempfile.TemporaryDirectory() as tmpdir:
            for idx, pagina in enumerate(pdf):
                # 200 dpi costuma ser suficiente para laudos/receitas e mantém o processamento leve.
                pix = pagina.get_pixmap(dpi=200, alpha=False)
                imagem_path = Path(tmpdir) / f"pagina_{idx + 1}.png"
                pix.save(str(imagem_path))
                with Image.open(str(imagem_path)) as img:
                    try:
                        textos.append(pytesseract.image_to_string(img, lang="por"))
                    except Exception:
                        textos.append(pytesseract.image_to_string(img))
    except Exception:
        return ""
    return _limpar_texto("\n".join(textos))


def extrair_texto_pdf(caminho: Path) -> Tuple[str, str, Optional[str]]:
    """Extrai texto de PDF sem jamais retornar o conteúdo binário bruto.

    Retorna: (texto, metodo, observacao)
    """
    texto = _extrair_pdf_pymupdf_texto(caminho)
    if texto:
        return texto, "PDF_TEXTO_PYMUPDF", None

    texto = _extrair_pdf_pypdf(caminho)
    if texto:
        return texto, "PDF_TEXTO_PYPDF", None

    texto = _ocr_pdf_imagem(caminho)
    if texto:
        return texto, "PDF_IMAGEM_OCR", None

    if not _tesseract_disponivel():
        return "", "PDF_IMAGEM_OCR_NAO_DISPONIVEL", (
            "O PDF parece ser imagem/scaneado ou não possui texto pesquisável. "
            "Instale o Tesseract OCR e as bibliotecas pytesseract/Pillow/PyMuPDF para extrair texto de imagens."
        )

    return "", "PDF_SEM_TEXTO_EXTRAIDO", "Não foi possível extrair texto útil do PDF."


def extrair_texto_imagem(caminho: Path) -> Tuple[str, str, Optional[str]]:
    if not _tesseract_disponivel():
        return "", "IMAGEM_OCR_NAO_DISPONIVEL", "Tesseract OCR não está disponível neste ambiente."

    try:
        from PIL import Image  # type: ignore
        import pytesseract  # type: ignore

        with Image.open(str(caminho)) as img:
            try:
                texto = pytesseract.image_to_string(img, lang="por")
            except Exception:
                texto = pytesseract.image_to_string(img)
        return _limpar_texto(texto), "IMAGEM_OCR", None
    except Exception as exc:
        return "", "IMAGEM_OCR_ERRO", str(exc)


def extrair_texto_arquivo(caminho: str, content_type: Optional[str] = None) -> Dict[str, str]:
    path = Path(caminho)
    suffix = path.suffix.lower()
    content_type = (content_type or "").lower()

    metodo = "NAO_SUPORTADO"
    texto = ""
    observacao = ""

    if not path.exists():
        return {"texto": "", "metodo": "ARQUIVO_NAO_ENCONTRADO", "status": "ERRO", "observacao": "Arquivo não encontrado no servidor."}

    if suffix == ".pdf" or "pdf" in content_type:
        texto, metodo, obs = extrair_texto_pdf(path)
        observacao = obs or ""
    elif suffix in {".txt", ".csv"} or content_type.startswith("text/"):
        metodo = "TEXTO_SIMPLES"
        texto = _limpar_texto(path.read_text(encoding="utf-8", errors="ignore"))
    elif suffix in {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"} or content_type.startswith("image/"):
        texto, metodo, obs = extrair_texto_imagem(path)
        observacao = obs or ""

    if texto and not _texto_parece_lixo_pdf(texto):
        status = "CONCLUIDO"
    elif metodo == "NAO_SUPORTADO":
        status = "NAO_SUPORTADO"
    elif "ERRO" in metodo or metodo == "ARQUIVO_NAO_ENCONTRADO":
        status = "ERRO"
    else:
        texto = ""
        status = "SEM_TEXTO_EXTRAIDO"

    return {"texto": texto, "metodo": metodo, "status": status, "observacao": observacao}



# ---------------------------------------------------------------------------
# Passo 12C.1/12C.2 - Classificação documental automática
# ---------------------------------------------------------------------------

TIPOS_DOCUMENTAIS_OCR = [
    "LAUDO",
    "RECEITA",
    "ESPIROMETRIA",
    "EXAME_LABORATORIAL",
    "DOCUMENTO_PESSOAL",
    "TERMO_ESCLARECIMENTO",
    "OUTROS",
]

PALAVRAS_CHAVE_CLASSIFICACAO = {
    "LAUDO": [
        "lme", "laudo", "laudo para solicitação", "solicitação de medicamento",
        "componente especializado", "cid", "diagnóstico", "diagnostico",
        "justificativa clínica", "justificativa clinica", "medicamento solicitado",
    ],
    "RECEITA": [
        "receita", "receituário", "receituario", "prescrição", "prescricao",
        "posologia", "uso contínuo", "uso continuo", "tomar", "comprimido",
        "cápsula", "capsula", "ampola", "frasco", "seringa", "dose",
    ],
    "ESPIROMETRIA": [
        "espirometria", "vef1", "vef 1", "cvf", "vef1/cvf", "distúrbio ventilatório",
        "disturbio ventilatorio", "prova de função pulmonar", "funcao pulmonar", "bronco",
        "fluxo expiratório", "fluxo expiratorio",
    ],
    "EXAME_LABORATORIAL": [
        "hemograma", "eosinófilos", "eosinofilos", "ige", "creatinina", "resultado",
        "laboratório", "laboratorio", "material", "coleta", "sangue", "laudo laboratorial",
    ],
    "DOCUMENTO_PESSOAL": [
        "cpf", "rg", "carteira de identidade", "identidade", "registro geral",
        "data de nascimento", "nascimento", "filiação", "filiacao", "órgão expedidor", "orgao expedidor",
    ],
    "TERMO_ESCLARECIMENTO": [
        "termo", "esclarecimento", "responsabilidade", "consentimento",
        "declaro", "estou ciente", "riscos", "benefícios", "beneficios",
        "termo de esclarecimento", "termo de responsabilidade",
    ],
}

PESOS_CLASSIFICACAO = {
    "lme": 5,
    "laudo para solicitação": 5,
    "solicitação de medicamento": 5,
    "componente especializado": 4,
    "receita": 4,
    "receituário": 4,
    "receituario": 4,
    "prescrição": 4,
    "prescricao": 4,
    "espirometria": 5,
    "vef1": 5,
    "cvf": 4,
    "hemograma": 4,
    "eosinófilos": 4,
    "eosinofilos": 4,
    "cpf": 3,
    "rg": 3,
    "termo de esclarecimento": 5,
    "termo de responsabilidade": 5,
}


def classificar_documento(texto: str) -> Dict[str, object]:
    """Classifica o tipo documental com base em palavras-chave.

    Esta classificação é uma sugestão operacional. Ela não altera
    automaticamente o tipo cadastrado, vigência, agenda, notificação ou WhatsApp.
    """
    texto_limpo = _limpar_texto(texto or "")
    texto_lower = texto_limpo.lower()

    if not texto_lower:
        return {
            "tipo": "OUTROS",
            "confianca": 0.0,
            "evidencias": [],
            "observacao": "Sem texto suficiente para classificação automática.",
            "atualizacao_automatica": False,
        }

    pontuacoes = {}
    evidencias_por_tipo = {}

    for tipo, palavras in PALAVRAS_CHAVE_CLASSIFICACAO.items():
        score = 0
        evidencias = []
        for palavra in palavras:
            palavra_lower = palavra.lower()
            if palavra_lower in texto_lower:
                peso = PESOS_CLASSIFICACAO.get(palavra_lower, 1)
                score += peso
                evidencias.append(palavra)
        pontuacoes[tipo] = score
        evidencias_por_tipo[tipo] = evidencias

    tipo_vencedor = max(pontuacoes, key=pontuacoes.get)
    score_vencedor = pontuacoes[tipo_vencedor]

    if score_vencedor <= 0:
        return {
            "tipo": "OUTROS",
            "confianca": 0.25,
            "evidencias": [],
            "observacao": "Nenhum marcador documental específico foi identificado.",
            "atualizacao_automatica": False,
        }

    # Confiança heurística: cresce com a pontuação e fica limitada a 0.98.
    confianca = min(0.98, round(score_vencedor / 12, 2))
    if score_vencedor >= 8:
        confianca = max(confianca, 0.85)
    elif score_vencedor >= 5:
        confianca = max(confianca, 0.65)
    else:
        confianca = max(confianca, 0.45)

    # Empate ou diferença pequena reduz a confiança.
    scores_ordenados = sorted(pontuacoes.values(), reverse=True)
    if len(scores_ordenados) > 1 and scores_ordenados[1] > 0 and (score_vencedor - scores_ordenados[1]) <= 1:
        confianca = min(confianca, 0.55)

    return {
        "tipo": tipo_vencedor,
        "confianca": confianca,
        "evidencias": evidencias_por_tipo.get(tipo_vencedor, [])[:8],
        "pontuacoes": pontuacoes,
        "observacao": "Classificação automática para conferência humana.",
        "atualizacao_automatica": False,
    }


def sugerir_campos(texto: str) -> Dict[str, Optional[str]]:
    """Identifica campos simples para conferência humana.

    As sugestões não atualizam automaticamente nenhum cadastro.
    """
    texto = texto or ""
    texto_linhas = [l.strip() for l in texto.splitlines() if l.strip()]
    texto_unico = "\n".join(texto_linhas)

    cid = None
    cid_match = re.search(r"\b([A-Z][0-9]{2}(?:\.[0-9A-Z]{1,2})?)\b", texto_unico, re.I)
    if cid_match:
        cid = cid_match.group(1).upper()

    crm = None
    crm_match = re.search(r"\bCRM\s*[-:/]?\s*([A-Z]{2})?\s*([0-9]{4,7})\b", texto_unico, re.I)
    if crm_match:
        uf = (crm_match.group(1) or "").upper()
        crm = f"CRM {uf} {crm_match.group(2)}".strip()

    data_emissao = None
    validade = None
    datas = re.findall(r"\b([0-3]?\d[/-][01]?\d[/-](?:20)?\d{2})\b", texto_unico)
    if datas:
        data_emissao = datas[0]
        if len(datas) > 1:
            validade = datas[-1]

    nome_paciente = None
    for padrao in [r"Paciente\s*[:\-]?\s*([^\n]{5,80})", r"Nome\s*[:\-]?\s*([^\n]{5,80})"]:
        m = re.search(padrao, texto_unico, re.I)
        if m:
            nome_paciente = m.group(1).strip(" :-")
            break

    medico = None
    m = re.search(r"(?:M[eé]dico|Prescritor)\s*[:\-]?\s*([^\n]{5,80})", texto_unico, re.I)
    if m:
        medico = m.group(1).strip(" :-")

    medicamentos = []
    palavras_chave = [
        "dupilumabe", "mepolizumabe", "benralizumabe", "omalizumabe",
        "budesonida", "formoterol", "tiotrópio", "tiotropio", "salbutamol",
        "montelucaste", "prednisona", "prednisolona"
    ]
    texto_lower = texto_unico.lower()
    for termo in palavras_chave:
        if termo in texto_lower:
            medicamentos.append(termo.upper())

    classificacao = classificar_documento(texto_unico)

    campos_estruturados = None
    if classificacao.get("tipo") == "LAUDO":
        campos_estruturados = extrair_campos_lme(texto_unico)
        campos_lme = campos_estruturados.get("campos", {}) if isinstance(campos_estruturados, dict) else {}
        # Mantém compatibilidade com campos antigos, mas melhora as sugestões quando o extrator LME encontra dados mais precisos.
        nome_paciente = nome_paciente or campos_lme.get("nome_paciente")
        cid = cid or campos_lme.get("cid")
        if not medicamentos and campos_lme.get("medicamentos"):
            medicamentos = campos_lme.get("medicamentos") or []

    return {
        "nome_paciente": nome_paciente,
        "cid": cid,
        "crm": crm,
        "medico": medico,
        "data_emissao": data_emissao,
        "data_validade": validade,
        "medicamentos": ", ".join(sorted(set(medicamentos))) if medicamentos else None,
        "classificacao_documental": classificacao,
        "tipo_documento_sugerido": classificacao.get("tipo"),
        "confianca_classificacao": classificacao.get("confianca"),
        "campos_estruturados": campos_estruturados,
        "extrator_estruturado": campos_estruturados.get("tipo_extrator") if isinstance(campos_estruturados, dict) else None,
        "confianca_extracao_estruturada": campos_estruturados.get("confianca") if isinstance(campos_estruturados, dict) else None,
    }


def dumps_sugestoes(sugestoes: Dict[str, Optional[str]]) -> str:
    return json.dumps(sugestoes, ensure_ascii=False)


def loads_sugestoes(valor: Optional[str]) -> Dict[str, Optional[str]]:
    if not valor:
        return {}
    try:
        return json.loads(valor)
    except Exception:
        return {}
