"""Extrator estruturado para LME/Laudo CEAF.

Passo 12D.1: transforma texto OCR de LME em campos estruturados para
conferência humana. Não atualiza automaticamente paciente, vigência, agenda,
processo documental ou WhatsApp.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, List, Optional


CABECALHOS_IGNORAR = {
    "SISTEMA UNICO DE SAUDE",
    "MINISTERIO DA SAUDE",
    "SECRETARIA DE ESTADO DA SAUDE",
    "COMPONENTE ESPECIALIZADO DA ASSISTENCIA FARMACEUTICA",
    "LAUDO DE SOLICITACAO, AVALIACAO E AUTORIZACAO DE MEDICAMENTO",
    "SOLICITACAO DE MEDICAMENTO",
    "CAMPOS DE PREENCHIMENTO EXCLUSIVO PELO MEDICO SOLICITANTE",
}


def _sem_acentos(valor: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", valor or "")
        if not unicodedata.combining(c)
    )


def _normalizar_linha(linha: str) -> str:
    linha = (linha or "").strip()
    linha = re.sub(r"\s+", " ", linha)
    return linha.strip(" :-")


def _linhas(texto: str) -> List[str]:
    return [_normalizar_linha(l) for l in (texto or "").splitlines() if _normalizar_linha(l)]


def _eh_nome_provavel(linha: str) -> bool:
    original = _normalizar_linha(linha)
    if not original:
        return False
    sem = _sem_acentos(original).upper()
    if sem in CABECALHOS_IGNORAR:
        return False
    if any(p in sem for p in ["LAUDO", "MEDICAMENTO", "PACIENTE", "DOCUMENTO", "PAGINA", "CAMPO", "CID", "DIAGNOSTICO", "SUS", "SAUDE"]):
        return False
    if re.search(r"\d", sem):
        return False
    partes = sem.split()
    if len(partes) < 2 or len(partes) > 6:
        return False
    return all(len(p) >= 2 for p in partes)


def _extrair_nomes_por_topo(texto: str) -> Dict[str, Optional[str]]:
    candidatos = []
    for linha in _linhas(texto)[:25]:
        if _eh_nome_provavel(linha):
            candidatos.append(linha)
    return {
        "nome_paciente": candidatos[0] if len(candidatos) >= 1 else None,
        "nome_mae": candidatos[1] if len(candidatos) >= 2 else None,
    }


def _extrair_por_rotulo(texto: str, rotulo: str, proximo_rotulo: Optional[str] = None) -> Optional[str]:
    """Extrai trecho após rótulo em textos OCR lineares, quando possível."""
    padrao = re.escape(rotulo)
    if proximo_rotulo:
        m = re.search(padrao + r"\s*[:\-]?\s*(.*?)\s*" + re.escape(proximo_rotulo), texto, re.I | re.S)
    else:
        m = re.search(padrao + r"\s*[:\-]?\s*([^\n]{3,120})", texto, re.I)
    if not m:
        return None
    valor = _normalizar_linha(m.group(1))
    valor = re.sub(r"^\*\s*", "", valor).strip()
    if len(valor) < 3:
        return None
    return valor[:120]


def extrair_cid(texto: str) -> Optional[str]:
    texto_norm = _sem_acentos(texto or "").upper()
    # Prioriza CID próximo aos marcadores do formulário.
    m = re.search(r"CID\s*-?\s*10\s*\*?\s*(?:10-\s*DIAGNOSTICO\s*)?([A-Z][0-9]{2}(?:\.?[0-9A-Z])?)", texto_norm)
    if m:
        return m.group(1).replace(".", "")
    # Padrão comum em LME: G122 DOENC DO NEURONIO MOTOR
    m = re.search(r"\b([A-Z][0-9]{2}(?:\.?[0-9A-Z])?)\s+(?:DOENC|DOENCA|DIAGNOSTICO)", texto_norm)
    if m:
        return m.group(1).replace(".", "")
    # Fallback: primeiro padrão CID plausível, evitando CNS/CPF.
    for m in re.finditer(r"\b([A-Z][0-9]{2}(?:\.?[0-9A-Z])?)\b", texto_norm):
        valor = m.group(1).replace(".", "")
        if valor not in {"SUS"}:
            return valor
    return None


def extrair_diagnostico(texto: str, cid: Optional[str] = None) -> Optional[str]:
    texto_norm = _sem_acentos(texto or "").upper()
    if cid:
        cid_re = re.escape(cid.replace(".", ""))
        m = re.search(cid_re + r"\s+([A-Z ]{5,90})(?:\n|NUMERO|KG|CM|NAO|SIM|13-|12-|$)", texto_norm)
        if m:
            diag = _normalizar_linha(m.group(1).title())
            return diag.upper()
    m = re.search(r"10-\s*DIAGNOSTICO\s*([A-Z0-9 ]{5,90})(?:\n|NUMERO|KG|CM|$)", texto_norm)
    if m:
        valor = _normalizar_linha(m.group(1))
        valor = re.sub(r"^[A-Z][0-9]{2}[0-9A-Z]?\s+", "", valor)
        return valor.upper() if valor else None
    return None


def extrair_medicamentos(texto: str) -> List[str]:
    meds = []
    for linha in _linhas(texto):
        sem = _sem_acentos(linha).upper()
        if "MG" in sem and not any(x in sem for x in ["PAGINA", "EXAMES NECESSARIOS", "DOCUMENTOS GERAIS"]):
            # remove prefixos de tabela, mas preserva concentração/apresentação.
            candidato = re.sub(r"^\d+\s+", "", linha).strip()
            candidato = re.sub(r"\s+", " ", candidato)
            if 5 <= len(candidato) <= 80 and candidato.upper() not in [m.upper() for m in meds]:
                meds.append(candidato.upper())
    # Fallback para fármacos comuns sem linha isolada.
    texto_upper = _sem_acentos(texto or "").upper()
    for m in re.finditer(r"\b([A-ZÇÁÉÍÓÚÂÊÔÃÕ]{4,30})\s+([0-9]{1,4})\s*MG(?:\s+[A-Z]{2,10})?\b", texto_upper):
        candidato = _normalizar_linha(m.group(0)).upper()
        if candidato not in [x.upper() for x in meds]:
            meds.append(candidato)
    return meds[:10]


def extrair_cns(texto: str) -> Optional[str]:
    # Formato visto no modelo: 706.8042.3116.2227, mas aceita CNS numérico com 15 dígitos.
    m = re.search(r"\b(\d{3}[\.\s]?\d{4}[\.\s]?\d{4}[\.\s]?\d{4})\b", texto or "")
    if m:
        return re.sub(r"\s+", ".", m.group(1)).strip()
    m = re.search(r"\b(\d{15})\b", texto or "")
    if m:
        n = m.group(1)
        return f"{n[:3]}.{n[3:7]}.{n[7:11]}.{n[11:]}"
    return None


def extrair_municipio(texto: str) -> str | None:
    linhas = [l.strip() for l in texto.splitlines() if l.strip()]

    for i, linha in enumerate(linhas):
        linha_lower = linha.lower()

        if "município de residência" in linha_lower or "municipio de residencia" in linha_lower:
            for proxima in linhas[i + 1:i + 4]:
                proxima_limpa = proxima.strip()

                if not proxima_limpa:
                    continue

                if proxima_limpa.lower().startswith("página"):
                    continue

                if proxima_limpa.lower().startswith("pagina"):
                    continue

                if "município" in proxima_limpa.lower() or "municipio" in proxima_limpa.lower():
                    continue

                if any(ch.isdigit() for ch in proxima_limpa):
                    continue

                return proxima_limpa

    return None

def extrair_data_solicitacao(texto: str) -> Optional[str]:
    m = re.search(r"16-\s*Data da solicita[cç][aã]o\s*\*?\s*([0-3]?\d[/-][01]?\d[/-](?:20)?\d{2})", texto or "", re.I)
    if m:
        return m.group(1)
    return None


def extrair_campos_lme(texto: str) -> Dict[str, Any]:
    texto = texto or ""
    nomes_topo = _extrair_nomes_por_topo(texto)

    nome_paciente = nomes_topo.get("nome_paciente")
    nome_mae = nomes_topo.get("nome_mae")

    # Tenta rótulos quando o OCR preserva a proximidade visual dos campos.
    rotulo_paciente = _extrair_por_rotulo(texto, "3- Nome completo do Paciente", "4- Nome da mãe")
    if rotulo_paciente and _eh_nome_provavel(rotulo_paciente):
        nome_paciente = rotulo_paciente

    rotulo_mae = _extrair_por_rotulo(texto, "4- Nome da mãe do Paciente", "16- Data")
    if rotulo_mae and _eh_nome_provavel(rotulo_mae):
        nome_mae = rotulo_mae

    cid = extrair_cid(texto)
    diagnostico = extrair_diagnostico(texto, cid)
    medicamentos = extrair_medicamentos(texto)
    cns = extrair_cns(texto)
    municipio = extrair_municipio(texto)
    data_solicitacao = extrair_data_solicitacao(texto)

    campos = {
        "nome_paciente": nome_paciente,
        "nome_mae": nome_mae,
        "cid": cid,
        "diagnostico": diagnostico,
        "medicamento": medicamentos[0] if medicamentos else None,
        "medicamentos": medicamentos,
        "cns_paciente": cns,
        "municipio": municipio,
        "data_solicitacao": data_solicitacao,
        "nome_medico": None,
        "crm": None,
        "cnes": None,
        "estabelecimento": None,
    }

    pesos = {
        "nome_paciente": 2,
        "nome_mae": 1,
        "cid": 2,
        "diagnostico": 1,
        "medicamento": 2,
        "cns_paciente": 1,
        "municipio": 1,
        "data_solicitacao": 1,
    }
    total = sum(pesos.values())
    obtido = sum(peso for campo, peso in pesos.items() if campos.get(campo))
    confianca = round(min(0.98, max(0.25, obtido / total)), 2) if total else 0.0

    return {
        "tipo_extrator": "LME_CEAF",
        "confianca": confianca,
        "campos": campos,
        "observacao": "Campos estruturados sugeridos para conferência humana. Nenhuma atualização automática foi realizada.",
        "atualizacao_automatica": False,
    }
