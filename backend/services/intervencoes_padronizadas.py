"""Catálogo e mapeamento inicial de intervenções farmacêuticas padronizadas.

Passo 14E.2C.2A

Objetivo:
- criar um catálogo único e versionado de tipos de intervenção;
- mapear os textos legados do App de Intervenções para categorias padronizadas;
- apoiar integração incremental sem modificar os dados originais.
"""
from __future__ import annotations

import re
import unicodedata
from collections import Counter, defaultdict
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

VERSAO_CATALOGO_INTERVENCOES = "2026.1"

CATALOGO_INTERVENCOES = [
    {
        "codigo": "EDUCACAO_EM_SAUDE",
        "rotulo": "Educação em saúde",
        "grupo": "educacao",
        "descricao": "Atividade educativa voltada ao entendimento da condição de saúde, prevenção de agravos e promoção do autocuidado.",
    },
    {
        "codigo": "ORIENTACAO_FARMACEUTICA",
        "rotulo": "Orientação farmacêutica",
        "grupo": "orientacao",
        "descricao": "Orientação individual sobre uso, conservação, técnica de administração, horários, adesão ou manejo da farmacoterapia.",
    },
    {
        "codigo": "CONCILIACAO_MEDICAMENTOSA",
        "rotulo": "Conciliação medicamentosa",
        "grupo": "seguranca",
        "descricao": "Revisão comparativa de medicamentos em uso, prescrições, histórico e relato do paciente para reduzir discrepâncias.",
    },
    {
        "codigo": "MONITORAMENTO_FARMACOTERAPEUTICO",
        "rotulo": "Monitoramento farmacoterapêutico",
        "grupo": "monitoramento",
        "descricao": "Acompanhamento de parâmetros clínicos, laboratoriais, adesão, efetividade, segurança ou eventos relacionados ao medicamento.",
    },
    {
        "codigo": "ENCAMINHAMENTO",
        "rotulo": "Encaminhamento",
        "grupo": "articulacao",
        "descricao": "Encaminhamento do paciente para outro serviço, profissional ou ponto da rede de atenção.",
    },
    {
        "codigo": "CONTATO_PRESCRITOR",
        "rotulo": "Contato com prescritor",
        "grupo": "articulacao",
        "descricao": "Contato ou comunicação com prescritor para discutir problema farmacoterapêutico, prescrição, dose, segurança ou conduta.",
    },
    {
        "codigo": "CONTATO_EQUIPE",
        "rotulo": "Contato com equipe multiprofissional",
        "grupo": "articulacao",
        "descricao": "Comunicação com equipe de saúde, APS, serviço especializado, gestão ou outro profissional envolvido no cuidado.",
    },
    {
        "codigo": "AJUSTE_TERAPEUTICO_SUGERIDO",
        "rotulo": "Ajuste terapêutico sugerido",
        "grupo": "intervencao_clinica",
        "descricao": "Sugestão de ajuste posológico, troca, suspensão, inclusão ou adequação terapêutica, dependente de avaliação/prescrição quando aplicável.",
    },
    {
        "codigo": "REFORCO_ADESAO",
        "rotulo": "Reforço de adesão",
        "grupo": "adesao",
        "descricao": "Intervenção direcionada a barreiras de adesão, organização de rotina, lembretes, compreensão da terapia ou persistência do tratamento.",
    },
    {
        "codigo": "PREVENCAO_EVENTO_ADVERSO",
        "rotulo": "Prevenção ou manejo de evento adverso",
        "grupo": "seguranca",
        "descricao": "Ação voltada à prevenção, identificação, orientação, monitoramento ou encaminhamento diante de suspeita/risco de evento adverso.",
    },
    {
        "codigo": "ORIENTACAO_DOCUMENTAL",
        "rotulo": "Orientação documental",
        "grupo": "ceaf_documental",
        "descricao": "Orientação sobre laudos, receitas, exames, renovação, adequação, inclusão ou documentação necessária ao tratamento.",
    },
    {
        "codigo": "OUTRA",
        "rotulo": "Outra intervenção",
        "grupo": "outros",
        "descricao": "Intervenção não enquadrada nas categorias padronizadas disponíveis.",
    },
]

NIVEIS_INTERVENCAO = [
    {"codigo": "PACIENTE", "rotulo": "Paciente"},
    {"codigo": "CUIDADOR", "rotulo": "Cuidador"},
    {"codigo": "PRESCRITOR", "rotulo": "Prescritor"},
    {"codigo": "EQUIPE_MULTIPROFISSIONAL", "rotulo": "Equipe multiprofissional"},
    {"codigo": "SISTEMA", "rotulo": "Sistema/fluxo de trabalho"},
]

ACEITACAO_INTERVENCAO = [
    {"codigo": "ACEITA", "rotulo": "Aceita"},
    {"codigo": "PARCIALMENTE_ACEITA", "rotulo": "Parcialmente aceita"},
    {"codigo": "NAO_ACEITA", "rotulo": "Não aceita"},
    {"codigo": "PENDENTE", "rotulo": "Pendente"},
    {"codigo": "NAO_SE_APLICA", "rotulo": "Não se aplica"},
]

IMPLEMENTACAO_INTERVENCAO = [
    {"codigo": "IMPLEMENTADA", "rotulo": "Implementada"},
    {"codigo": "PARCIALMENTE_IMPLEMENTADA", "rotulo": "Parcialmente implementada"},
    {"codigo": "NAO_IMPLEMENTADA", "rotulo": "Não implementada"},
    {"codigo": "NAO_AVALIADA", "rotulo": "Não avaliada"},
]

RESULTADO_INTERVENCAO = [
    {"codigo": "RESOLVIDO", "rotulo": "Resolvido"},
    {"codigo": "PARCIALMENTE_RESOLVIDO", "rotulo": "Parcialmente resolvido"},
    {"codigo": "SEM_MELHORA", "rotulo": "Sem melhora"},
    {"codigo": "PENDENTE_AVALIACAO", "rotulo": "Pendente de avaliação"},
    {"codigo": "NAO_AVALIADO", "rotulo": "Não avaliado"},
]

# Mapeamento inicial, conservador, dos textos já usados no App de Intervenções.
MAPEAMENTO_LEGADO_INICIAL = {
    "posologia": "AJUSTE_TERAPEUTICO_SUGERIDO",
    "acondicionamento": "ORIENTACAO_FARMACEUTICA",
    "tecnica de uso": "ORIENTACAO_FARMACEUTICA",
    "tecnica uso": "ORIENTACAO_FARMACEUTICA",
    "reacao adversa a medicamentos ram": "PREVENCAO_EVENTO_ADVERSO",
    "reacao adversa medicamentos ram": "PREVENCAO_EVENTO_ADVERSO",
    "ram": "PREVENCAO_EVENTO_ADVERSO",
    "erro de prescricao": "CONTATO_PRESCRITOR",
    "orientacao documental": "ORIENTACAO_DOCUMENTAL",
    "encaminhamentos": "ENCAMINHAMENTO",
    "encaminhamento": "ENCAMINHAMENTO",
    "educacao em saude": "EDUCACAO_EM_SAUDE",
    "orientacao ao profissional da saude": "CONTATO_EQUIPE",
    "orientacao profissional saude": "CONTATO_EQUIPE",
    "parametros clinicos": "MONITORAMENTO_FARMACOTERAPEUTICO",
    "monitoramento": "MONITORAMENTO_FARMACOTERAPEUTICO",
}


def _normalizar_texto(valor: Any) -> str:
    texto_valor = str(valor or "").strip().lower()
    texto_valor = unicodedata.normalize("NFKD", texto_valor)
    texto_valor = "".join(ch for ch in texto_valor if not unicodedata.combining(ch))
    texto_valor = re.sub(r"[^a-z0-9]+", " ", texto_valor)
    return re.sub(r"\s+", " ", texto_valor).strip()


def _rotulo_por_codigo(codigo: str | None) -> str | None:
    if not codigo:
        return None
    item = next((i for i in CATALOGO_INTERVENCOES if i["codigo"] == codigo), None)
    return item["rotulo"] if item else None


def _grupo_por_codigo(codigo: str | None) -> str | None:
    if not codigo:
        return None
    item = next((i for i in CATALOGO_INTERVENCOES if i["codigo"] == codigo), None)
    return item["grupo"] if item else None


def mapear_intervencao_legada(texto_legado: str) -> dict[str, Any]:
    normalizado = _normalizar_texto(texto_legado)
    codigo = MAPEAMENTO_LEGADO_INICIAL.get(normalizado)

    if not codigo:
        # Regras por aproximação controlada. Não substituem validação humana.
        if "adesao" in normalizado:
            codigo = "REFORCO_ADESAO"
        elif "prescr" in normalizado or "medico" in normalizado:
            codigo = "CONTATO_PRESCRITOR"
        elif "document" in normalizado or "laudo" in normalizado or "receita" in normalizado:
            codigo = "ORIENTACAO_DOCUMENTAL"
        elif "educ" in normalizado:
            codigo = "EDUCACAO_EM_SAUDE"
        elif "encaminh" in normalizado:
            codigo = "ENCAMINHAMENTO"
        elif "ram" in normalizado or "advers" in normalizado:
            codigo = "PREVENCAO_EVENTO_ADVERSO"
        elif "dose" in normalizado or "posolog" in normalizado:
            codigo = "AJUSTE_TERAPEUTICO_SUGERIDO"

    return {
        "texto_legado": texto_legado,
        "texto_normalizado": normalizado,
        "codigo_sugerido": codigo,
        "rotulo_sugerido": _rotulo_por_codigo(codigo),
        "grupo_sugerido": _grupo_por_codigo(codigo),
        "status_mapeamento": "MAPEADO" if codigo else "NAO_MAPEADO",
        "necessita_revisao": not bool(codigo),
    }


def _dialeto(db: Session) -> str:
    try:
        return db.bind.dialect.name
    except Exception:
        return "sqlite"


def _exec(db: Session, sql: str, params: dict[str, Any] | None = None):
    return db.execute(text(sql), params or {})


def _tabela_existe(db: Session, nome: str) -> bool:
    try:
        dialect = _dialeto(db)
        if dialect == "postgresql":
            row = _exec(
                db,
                "SELECT to_regclass(:nome) IS NOT NULL AS existe",
                {"nome": nome},
            ).first()
            return bool(row[0]) if row else False
        row = _exec(db, "SELECT name FROM sqlite_master WHERE type='table' AND name=:nome", {"nome": nome}).first()
        return bool(row)
    except Exception:
        return False


def garantir_estrutura_intervencoes_padronizadas(db: Session) -> None:
    """Cria catálogo versionado e tabela opcional de mapeamento auditável."""
    dialect = _dialeto(db)

    if dialect == "postgresql":
        _exec(db, """
        CREATE TABLE IF NOT EXISTS catalogo_intervencoes_padronizadas (
            id SERIAL PRIMARY KEY,
            codigo VARCHAR(80) NOT NULL,
            rotulo VARCHAR(255) NOT NULL,
            grupo VARCHAR(80),
            descricao TEXT,
            versao VARCHAR(40) NOT NULL DEFAULT '2026.1',
            ativo BOOLEAN DEFAULT TRUE,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (codigo, versao)
        )
        """)
        _exec(db, """
        CREATE TABLE IF NOT EXISTS mapeamento_intervencoes_legado (
            id SERIAL PRIMARY KEY,
            texto_legado TEXT NOT NULL,
            texto_normalizado TEXT NOT NULL,
            codigo_sugerido VARCHAR(80),
            status_mapeamento VARCHAR(40) NOT NULL DEFAULT 'NAO_MAPEADO',
            versao_catalogo VARCHAR(40) NOT NULL DEFAULT '2026.1',
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (texto_normalizado, versao_catalogo)
        )
        """)
    else:
        _exec(db, """
        CREATE TABLE IF NOT EXISTS catalogo_intervencoes_padronizadas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT NOT NULL,
            rotulo TEXT NOT NULL,
            grupo TEXT,
            descricao TEXT,
            versao TEXT NOT NULL DEFAULT '2026.1',
            ativo BOOLEAN DEFAULT 1,
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (codigo, versao)
        )
        """)
        _exec(db, """
        CREATE TABLE IF NOT EXISTS mapeamento_intervencoes_legado (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            texto_legado TEXT NOT NULL,
            texto_normalizado TEXT NOT NULL,
            codigo_sugerido TEXT,
            status_mapeamento TEXT NOT NULL DEFAULT 'NAO_MAPEADO',
            versao_catalogo TEXT NOT NULL DEFAULT '2026.1',
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (texto_normalizado, versao_catalogo)
        )
        """)

    for item in CATALOGO_INTERVENCOES:
        if dialect == "postgresql":
            _exec(
                db,
                """
                INSERT INTO catalogo_intervencoes_padronizadas
                (codigo, rotulo, grupo, descricao, versao, ativo)
                VALUES (:codigo, :rotulo, :grupo, :descricao, :versao, TRUE)
                ON CONFLICT (codigo, versao) DO UPDATE SET
                    rotulo = EXCLUDED.rotulo,
                    grupo = EXCLUDED.grupo,
                    descricao = EXCLUDED.descricao,
                    ativo = TRUE
                """,
                {**item, "versao": VERSAO_CATALOGO_INTERVENCOES},
            )
        else:
            _exec(
                db,
                """
                INSERT OR IGNORE INTO catalogo_intervencoes_padronizadas
                (codigo, rotulo, grupo, descricao, versao, ativo)
                VALUES (:codigo, :rotulo, :grupo, :descricao, :versao, 1)
                """,
                {**item, "versao": VERSAO_CATALOGO_INTERVENCOES},
            )
            _exec(
                db,
                """
                UPDATE catalogo_intervencoes_padronizadas
                SET rotulo = :rotulo, grupo = :grupo, descricao = :descricao, ativo = 1
                WHERE codigo = :codigo AND versao = :versao
                """,
                {**item, "versao": VERSAO_CATALOGO_INTERVENCOES},
            )

    db.commit()


def opcoes_intervencoes_padronizadas(db: Session | None = None) -> dict[str, Any]:
    if db is not None:
        garantir_estrutura_intervencoes_padronizadas(db)
    return {
        "versao_catalogo": VERSAO_CATALOGO_INTERVENCOES,
        "tipos_intervencao": CATALOGO_INTERVENCOES,
        "niveis_intervencao": NIVEIS_INTERVENCAO,
        "aceitacao": ACEITACAO_INTERVENCAO,
        "implementacao": IMPLEMENTACAO_INTERVENCAO,
        "resultado": RESULTADO_INTERVENCAO,
        "campos_recomendados": [
            "tipo_intervencao_padronizado",
            "nivel_intervencao",
            "aceitacao",
            "implementacao",
            "resultado",
            "descricao_clinica_complementar",
            "prm_id",
            "origem_sistema",
            "origem_id",
        ],
        "compatibilidade_legado": "Textos legados permanecem preservados; o mapeamento é sugerido e auditável.",
    }


def _split_tipos_intervencao(valor: str | None) -> list[str]:
    if not valor:
        return []
    partes = re.split(r"\s*;\s*|\s*,\s*|\s*\|\s*", str(valor))
    return [p.strip() for p in partes if p and p.strip()]


def _coletar_tipos_legados(db: Session) -> tuple[Counter, dict[str, set[str]]]:
    contador: Counter[str] = Counter()
    fontes: dict[str, set[str]] = defaultdict(set)

    if _tabela_existe(db, "intervencoes_importacao_staging"):
        rows = _exec(db, "SELECT tipos_intervencao FROM intervencoes_importacao_staging WHERE tipos_intervencao IS NOT NULL").fetchall()
        for (valor,) in rows:
            for tipo in _split_tipos_intervencao(valor):
                contador[tipo] += 1
                fontes[tipo].add("staging")

    if _tabela_existe(db, "intervencoes"):
        rows = _exec(db, "SELECT tipos_intervencao FROM intervencoes WHERE tipos_intervencao IS NOT NULL").fetchall()
        for (valor,) in rows:
            for tipo in _split_tipos_intervencao(valor):
                contador[tipo] += 1
                fontes[tipo].add("intervencoes")

    if _tabela_existe(db, "intervencoes_farmacoterapia"):
        rows = _exec(db, "SELECT tipo_intervencao FROM intervencoes_farmacoterapia WHERE tipo_intervencao IS NOT NULL").fetchall()
        for (valor,) in rows:
            for tipo in _split_tipos_intervencao(valor):
                contador[tipo] += 1
                fontes[tipo].add("intervencoes_farmacoterapia")

    return contador, fontes


def mapeamento_intervencoes_legado(db: Session, limite: int = 500) -> dict[str, Any]:
    garantir_estrutura_intervencoes_padronizadas(db)
    contador, fontes = _coletar_tipos_legados(db)

    itens = []
    for texto_legado, total in contador.most_common(limite):
        mapeamento = mapear_intervencao_legada(texto_legado)
        item = {
            **mapeamento,
            "total_ocorrencias": total,
            "fontes": sorted(fontes.get(texto_legado, [])),
            "versao_catalogo": VERSAO_CATALOGO_INTERVENCOES,
        }
        itens.append(item)
        _registrar_mapeamento(db, item)

    db.commit()

    total_ocorrencias = sum(contador.values())
    total_distintos = len(contador)
    total_mapeados = sum(1 for item in itens if item["status_mapeamento"] == "MAPEADO")
    return {
        "versao_catalogo": VERSAO_CATALOGO_INTERVENCOES,
        "total_ocorrencias": total_ocorrencias,
        "total_textos_distintos": total_distintos,
        "total_mapeados": total_mapeados,
        "total_nao_mapeados": max(total_distintos - total_mapeados, 0),
        "taxa_mapeamento": round((total_mapeados / total_distintos) * 100, 2) if total_distintos else 100.0,
        "itens": itens,
    }


def _registrar_mapeamento(db: Session, item: dict[str, Any]) -> None:
    dialect = _dialeto(db)
    params = {
        "texto_legado": item["texto_legado"],
        "texto_normalizado": item["texto_normalizado"],
        "codigo_sugerido": item["codigo_sugerido"],
        "status_mapeamento": item["status_mapeamento"],
        "versao_catalogo": VERSAO_CATALOGO_INTERVENCOES,
    }
    if dialect == "postgresql":
        _exec(db, """
        INSERT INTO mapeamento_intervencoes_legado
        (texto_legado, texto_normalizado, codigo_sugerido, status_mapeamento, versao_catalogo)
        VALUES (:texto_legado, :texto_normalizado, :codigo_sugerido, :status_mapeamento, :versao_catalogo)
        ON CONFLICT (texto_normalizado, versao_catalogo) DO UPDATE SET
            texto_legado = EXCLUDED.texto_legado,
            codigo_sugerido = EXCLUDED.codigo_sugerido,
            status_mapeamento = EXCLUDED.status_mapeamento
        """, params)
    else:
        _exec(db, """
        INSERT OR IGNORE INTO mapeamento_intervencoes_legado
        (texto_legado, texto_normalizado, codigo_sugerido, status_mapeamento, versao_catalogo)
        VALUES (:texto_legado, :texto_normalizado, :codigo_sugerido, :status_mapeamento, :versao_catalogo)
        """, params)
        _exec(db, """
        UPDATE mapeamento_intervencoes_legado
        SET texto_legado = :texto_legado,
            codigo_sugerido = :codigo_sugerido,
            status_mapeamento = :status_mapeamento
        WHERE texto_normalizado = :texto_normalizado AND versao_catalogo = :versao_catalogo
        """, params)


def dashboard_intervencoes_padronizadas(db: Session) -> dict[str, Any]:
    dados = mapeamento_intervencoes_legado(db)
    por_codigo: Counter[str] = Counter()
    por_grupo: Counter[str] = Counter()
    nao_mapeados = []

    for item in dados["itens"]:
        codigo = item.get("codigo_sugerido")
        if codigo:
            por_codigo[codigo] += item.get("total_ocorrencias") or 0
            grupo = item.get("grupo_sugerido") or "sem_grupo"
            por_grupo[grupo] += item.get("total_ocorrencias") or 0
        else:
            nao_mapeados.append(item)

    top_tipos = [
        {
            "codigo": codigo,
            "rotulo": _rotulo_por_codigo(codigo) or codigo,
            "grupo": _grupo_por_codigo(codigo),
            "total": total,
        }
        for codigo, total in por_codigo.most_common()
    ]

    return {
        "versao_catalogo": VERSAO_CATALOGO_INTERVENCOES,
        "resumo": {
            "total_ocorrencias_legadas": dados["total_ocorrencias"],
            "textos_distintos": dados["total_textos_distintos"],
            "textos_mapeados": dados["total_mapeados"],
            "textos_nao_mapeados": dados["total_nao_mapeados"],
            "taxa_mapeamento": dados["taxa_mapeamento"],
        },
        "por_tipo_padronizado": top_tipos,
        "por_grupo": [{"grupo": grupo, "total": total} for grupo, total in por_grupo.most_common()],
        "nao_mapeados_prioritarios": sorted(nao_mapeados, key=lambda x: x.get("total_ocorrencias", 0), reverse=True)[:20],
        "proxima_acao_recomendada": "Revisar textos não mapeados e aprovar o catálogo único antes da padronização definitiva dos formulários.",
    }
