"""Rotas de Metas Terapêuticas Estruturadas — Passo 14E.2C.3A.

Este router cria um contrato canônico para metas terapêuticas sem remover
as rotas legadas do motor de cuidado farmacêutico. O foco é padronização
clínica, vínculo com PRM/intervenção e preparação para Analytics.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import engine
from models.consultorio_models import (
    BaseConsultorio,
    PacienteClinico,
    MetaTerapeutica,
    ProblemaFarmacoterapeutico,
    IntervencaoFarmacoterapia,
)
from routers.consultorio import (
    get_db_consultorio,
    get_current_user_consultorio,
    exigir_farmaceutico_ou_admin,
)

BaseConsultorio.metadata.create_all(bind=engine)

router = APIRouter(prefix="/consultorio", tags=["Metas Terapêuticas"])

VERSAO_CATALOGO_METAS = "2026.06"

METAS_CATEGORIAS = [
    "CONTROLE_CLINICO",
    "ADESAO",
    "SEGURANCA",
    "PROCESSO_ASSISTENCIAL",
    "OUTRA",
]

METAS_SUBCATEGORIAS = {
    "CONTROLE_CLINICO": [
        "PRESSAO_ARTERIAL",
        "GLICEMIA_JEJUM",
        "GLICEMIA_POS_PRANDIAL",
        "HBA1C",
        "LDL",
        "HDL",
        "TRIGLICERIDEOS",
        "PESO",
        "IMC",
        "CIRCUNFERENCIA_ABDOMINAL",
        "PICO_FLUXO",
    ],
    "ADESAO": [
        "ADESAO_TRATAMENTO",
        "RETIRADA_REGULAR",
        "COMPARECIMENTO_CONSULTAS",
        "USO_CORRETO_MEDICAMENTO",
        "USO_CORRETO_DISPOSITIVO_INALATORIO",
    ],
    "SEGURANCA": [
        "AUSENCIA_RAM",
        "MONITORAMENTO_LABORATORIAL",
        "REDUCAO_EVENTOS_ADVERSOS",
    ],
    "PROCESSO_ASSISTENCIAL": [
        "RENOVACAO_DOCUMENTAL",
        "ATUALIZACAO_CADASTRAL",
        "REALIZACAO_EXAMES",
        "CONSULTA_ESPECIALIZADA",
    ],
    "OUTRA": ["OUTRA"],
}

UNIDADES_PADRAO = [
    "mmHg",
    "mg/dL",
    "%",
    "kg",
    "kg/m²",
    "cm",
    "L/min",
    "dias",
    "pontos",
    "sim/não",
]

STATUS_METAS_ESTRUTURADAS = [
    "PLANEJADA",
    "EM_ANDAMENTO",
    "ATINGIDA",
    "PARCIALMENTE_ATINGIDA",
    "NAO_ATINGIDA",
    "CANCELADA",
]

ORIGENS_META = [
    "CONSULTA",
    "RETORNO",
    "INTERVENCAO",
    "APP_INTERVENCOES",
    "IMPORTACAO",
    "OUTRO",
]

# Compatibilidade com status usados antes do 14E.2C.3A.
STATUS_LEGADOS_MAP = {
    "ATIVA": "EM_ANDAMENTO",
    "ALCANCADA": "ATINGIDA",
    "PARCIAL": "PARCIALMENTE_ATINGIDA",
    "NAO_ALCANCADA": "NAO_ATINGIDA",
}


def _usuario_email(current: Any) -> str | None:
    return getattr(current, "email", None) or getattr(current, "nome", None)


def _normalizar(value: Any, default: str | None = None) -> str | None:
    if value is None:
        return default
    text = str(value).strip().upper()
    return text or default


def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    text = str(value).strip()
    try:
        return date.fromisoformat(text[:10])
    except Exception:
        raise HTTPException(status_code=422, detail=f"Data inválida: {value}. Use AAAA-MM-DD.")


def _getattr(obj: Any, name: str, fallback: Any = None) -> Any:
    return getattr(obj, name, fallback)


def _set_if_attr(obj: Any, name: str, value: Any) -> None:
    if hasattr(obj, name):
        setattr(obj, name, value)


def _status_canonic(status: str | None) -> str:
    raw = _normalizar(status, "EM_ANDAMENTO") or "EM_ANDAMENTO"
    return STATUS_LEGADOS_MAP.get(raw, raw)


def serializar_meta_estruturada(meta: MetaTerapeutica) -> dict[str, Any]:
    categoria = _getattr(meta, "categoria", None) or _getattr(meta, "parametro", None) or "OUTRA"
    subcategoria = _getattr(meta, "subcategoria", None) or _getattr(meta, "parametro", None) or "OUTRA"
    data_prevista = _getattr(meta, "data_prevista", None) or _getattr(meta, "prazo", None)
    valor_atual = _getattr(meta, "valor_atual", None) or _getattr(meta, "valor_inicial", None)
    intervencao_id = _getattr(meta, "intervencao_farmacoterapia_id", None)
    status = _status_canonic(_getattr(meta, "status", None))
    return {
        "id": meta.id,
        "paciente_clinico_id": meta.paciente_clinico_id,
        "prm_id": _getattr(meta, "problema_id", None),
        "intervencao_farmacoterapia_id": intervencao_id,
        "categoria": categoria,
        "subcategoria": subcategoria,
        "descricao": meta.descricao,
        "valor_atual": valor_atual,
        "valor_alvo": _getattr(meta, "valor_alvo", None),
        "valor_resultado": _getattr(meta, "valor_resultado", None),
        "unidade": _getattr(meta, "unidade", None),
        "data_criacao": _dt(_getattr(meta, "criado_em", None)),
        "data_inicial": _dt(_getattr(meta, "data_inicial", None) or _getattr(meta, "criado_em", None)),
        "data_prevista": _dt(data_prevista),
        "data_conclusao": _dt(_getattr(meta, "data_conclusao", None)),
        "data_avaliacao": _dt(_getattr(meta, "data_avaliacao", None)),
        "status": status,
        "origem": _getattr(meta, "origem", None) or "CONSULTA",
        "codigo_catalogo": _getattr(meta, "codigo_catalogo", None),
        "versao_catalogo": _getattr(meta, "versao_catalogo", None) or VERSAO_CATALOGO_METAS,
        "resultado_observado": _getattr(meta, "resultado_observado", None),
        "legado": not bool(_getattr(meta, "categoria", None) or _getattr(meta, "subcategoria", None)),
        "criado_por": _getattr(meta, "criado_por", None),
        "criado_em": _dt(_getattr(meta, "criado_em", None)),
        "atualizado_em": _dt(_getattr(meta, "atualizado_em", None)),
    }


def _dt(value: Any) -> str | None:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _validar_categoria_subcategoria(categoria: str, subcategoria: str) -> None:
    if categoria not in METAS_CATEGORIAS:
        raise HTTPException(status_code=422, detail=f"Categoria inválida: {categoria}")
    if subcategoria not in METAS_SUBCATEGORIAS.get(categoria, []):
        raise HTTPException(
            status_code=422,
            detail=f"Subcategoria {subcategoria} incompatível com categoria {categoria}",
        )


def _aplicar_payload_meta(meta: MetaTerapeutica, payload: dict[str, Any], parcial: bool = False) -> None:
    categoria = _normalizar(payload.get("categoria"), None)
    subcategoria = _normalizar(payload.get("subcategoria"), None)
    if categoria or subcategoria or not parcial:
        categoria = categoria or _getattr(meta, "categoria", None) or "OUTRA"
        subcategoria = subcategoria or _getattr(meta, "subcategoria", None) or "OUTRA"
        _validar_categoria_subcategoria(categoria, subcategoria)
        _set_if_attr(meta, "categoria", categoria)
        _set_if_attr(meta, "subcategoria", subcategoria)
        # Compatibilidade com campo legado parametro.
        meta.parametro = subcategoria

    if "descricao" in payload or not parcial:
        descricao = payload.get("descricao")
        if not descricao and not parcial:
            raise HTTPException(status_code=422, detail="Descrição da meta é obrigatória")
        if descricao is not None:
            meta.descricao = str(descricao).strip()

    if "valor_atual" in payload:
        _set_if_attr(meta, "valor_atual", payload.get("valor_atual"))
        meta.valor_inicial = payload.get("valor_atual")
    elif "valor_inicial" in payload:
        _set_if_attr(meta, "valor_atual", payload.get("valor_inicial"))
        meta.valor_inicial = payload.get("valor_inicial")

    if "valor_alvo" in payload:
        meta.valor_alvo = payload.get("valor_alvo")
    if "unidade" in payload:
        meta.unidade = payload.get("unidade")

    if "data_inicial" in payload:
        _set_if_attr(meta, "data_inicial", _parse_date(payload.get("data_inicial")))
    if "data_prevista" in payload:
        data_prevista = _parse_date(payload.get("data_prevista"))
        _set_if_attr(meta, "data_prevista", data_prevista)
        meta.prazo = data_prevista
    elif "prazo" in payload:
        data_prevista = _parse_date(payload.get("prazo"))
        _set_if_attr(meta, "data_prevista", data_prevista)
        meta.prazo = data_prevista

    if "data_conclusao" in payload:
        _set_if_attr(meta, "data_conclusao", _parse_date(payload.get("data_conclusao")))

    if "status" in payload or not parcial:
        status = _normalizar(payload.get("status"), "EM_ANDAMENTO") or "EM_ANDAMENTO"
        if status not in STATUS_METAS_ESTRUTURADAS:
            raise HTTPException(status_code=422, detail=f"Status inválido: {status}")
        meta.status = status

    if "origem" in payload or not parcial:
        origem = _normalizar(payload.get("origem"), "CONSULTA") or "CONSULTA"
        if origem not in ORIGENS_META:
            origem = "OUTRO"
        _set_if_attr(meta, "origem", origem)

    if "codigo_catalogo" in payload:
        _set_if_attr(meta, "codigo_catalogo", payload.get("codigo_catalogo"))
    if "versao_catalogo" in payload:
        _set_if_attr(meta, "versao_catalogo", payload.get("versao_catalogo") or VERSAO_CATALOGO_METAS)
    elif not parcial:
        _set_if_attr(meta, "versao_catalogo", VERSAO_CATALOGO_METAS)

    if "intervencao_farmacoterapia_id" in payload:
        _set_if_attr(meta, "intervencao_farmacoterapia_id", payload.get("intervencao_farmacoterapia_id"))

    if "prm_id" in payload:
        meta.problema_id = payload.get("prm_id")
    elif "problema_id" in payload:
        meta.problema_id = payload.get("problema_id")

    meta.atualizado_em = datetime.utcnow()


@router.get("/metas/opcoes")
def opcoes_metas_terapeuticas(current=Depends(get_current_user_consultorio)):
    return {
        "versao_catalogo": VERSAO_CATALOGO_METAS,
        "categorias": METAS_CATEGORIAS,
        "subcategorias": METAS_SUBCATEGORIAS,
        "unidades": UNIDADES_PADRAO,
        "status": STATUS_METAS_ESTRUTURADAS,
        "origens": ORIGENS_META,
        "modelo": "PRM -> Intervenção -> Meta -> Plano de cuidado -> Avaliação",
        "compatibilidade_legado": True,
    }


@router.get("/metas/dashboard")
def dashboard_metas_terapeuticas(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    metas = db.query(MetaTerapeutica).all()
    hoje = date.today()
    total = len(metas)
    por_status: dict[str, int] = {}
    por_categoria: dict[str, int] = {}
    vencidas = 0
    proximas_30 = 0
    legadas = 0
    atingidas = 0

    for meta in metas:
        item = serializar_meta_estruturada(meta)
        status = item["status"] or "NAO_INFORMADO"
        categoria = item["categoria"] or "NAO_INFORMADA"
        por_status[status] = por_status.get(status, 0) + 1
        por_categoria[categoria] = por_categoria.get(categoria, 0) + 1
        if item.get("legado"):
            legadas += 1
        if status == "ATINGIDA":
            atingidas += 1
        data_prevista = _parse_date(item.get("data_prevista")) if item.get("data_prevista") else None
        if data_prevista and status not in ("ATINGIDA", "CANCELADA"):
            delta = (data_prevista - hoje).days
            if delta < 0:
                vencidas += 1
            elif delta <= 30:
                proximas_30 += 1

    return {
        "resumo": {
            "total_metas": total,
            "metas_ativas": sum(por_status.get(s, 0) for s in ["PLANEJADA", "EM_ANDAMENTO"]),
            "metas_atingidas": atingidas,
            "metas_vencidas": vencidas,
            "metas_proximas_30_dias": proximas_30,
            "metas_legadas_nao_padronizadas": legadas,
            "taxa_atingimento": round((atingidas / total) * 100, 2) if total else 0,
            "taxa_padronizacao": round(((total - legadas) / total) * 100, 2) if total else 0,
        },
        "por_status": por_status,
        "por_categoria": por_categoria,
        "versao_catalogo": VERSAO_CATALOGO_METAS,
    }


@router.get("/metas")
def listar_metas_terapeuticas(
    paciente_id: int | None = None,
    status: str | None = None,
    categoria: str | None = None,
    limite: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    query = db.query(MetaTerapeutica)
    if paciente_id:
        query = query.filter(MetaTerapeutica.paciente_clinico_id == paciente_id)
    if status:
        query = query.filter(func.upper(MetaTerapeutica.status) == status.upper())
    # Categoria pode não existir em versões antigas do modelo; por isso filtramos em memória.
    metas = query.order_by(MetaTerapeutica.criado_em.desc()).limit(limite).all()
    itens = [serializar_meta_estruturada(m) for m in metas]
    if categoria:
        cat = categoria.upper()
        itens = [i for i in itens if str(i.get("categoria") or "").upper() == cat]
    return {"total": len(itens), "metas": itens}


@router.get("/paciente-clinico/{paciente_id}/metas-estruturadas")
def listar_metas_paciente(
    paciente_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    paciente = db.query(PacienteClinico).filter(PacienteClinico.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente clínico não encontrado")
    metas = (
        db.query(MetaTerapeutica)
        .filter(MetaTerapeutica.paciente_clinico_id == paciente_id)
        .order_by(MetaTerapeutica.criado_em.desc())
        .all()
    )
    return {"paciente_id": paciente_id, "metas": [serializar_meta_estruturada(m) for m in metas]}


@router.post("/metas")
def criar_meta_terapeutica(
    payload: dict[str, Any],
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    exigir_farmaceutico_ou_admin(current)
    paciente_id = payload.get("paciente_id") or payload.get("paciente_clinico_id")
    if not paciente_id:
        raise HTTPException(status_code=422, detail="paciente_id é obrigatório")
    paciente = db.query(PacienteClinico).filter(PacienteClinico.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente clínico não encontrado")

    prm_id = payload.get("prm_id") or payload.get("problema_id")
    if prm_id and not db.query(ProblemaFarmacoterapeutico).filter(ProblemaFarmacoterapeutico.id == prm_id).first():
        raise HTTPException(status_code=404, detail="PRM vinculado não encontrado")

    intervencao_id = payload.get("intervencao_farmacoterapia_id")
    if intervencao_id and not db.query(IntervencaoFarmacoterapia).filter(IntervencaoFarmacoterapia.id == intervencao_id).first():
        raise HTTPException(status_code=404, detail="Intervenção vinculada não encontrada")

    meta = MetaTerapeutica(
        paciente_clinico_id=paciente_id,
        problema_id=prm_id,
        parametro="OUTRA",
        descricao=str(payload.get("descricao") or "").strip() or "Meta terapêutica",
        criado_por=_usuario_email(current),
        criado_em=datetime.utcnow(),
        atualizado_em=datetime.utcnow(),
    )
    _aplicar_payload_meta(meta, payload, parcial=False)
    db.add(meta)
    db.commit()
    db.refresh(meta)
    return {"ok": True, "meta": serializar_meta_estruturada(meta)}


@router.get("/metas/{meta_id}")
def obter_meta_terapeutica(
    meta_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    meta = db.query(MetaTerapeutica).filter(MetaTerapeutica.id == meta_id).first()
    if not meta:
        raise HTTPException(status_code=404, detail="Meta terapêutica não encontrada")
    return serializar_meta_estruturada(meta)


@router.put("/metas/{meta_id}")
def atualizar_meta_terapeutica(
    meta_id: int,
    payload: dict[str, Any],
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    exigir_farmaceutico_ou_admin(current)
    meta = db.query(MetaTerapeutica).filter(MetaTerapeutica.id == meta_id).first()
    if not meta:
        raise HTTPException(status_code=404, detail="Meta terapêutica não encontrada")
    _aplicar_payload_meta(meta, payload, parcial=True)
    db.commit()
    db.refresh(meta)
    return {"ok": True, "meta": serializar_meta_estruturada(meta)}
