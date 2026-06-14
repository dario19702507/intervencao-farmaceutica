"""Rotas canônicas do motor de cuidado farmacêutico.

Objetivo: reduzir redundância funcional do consultório criando um contrato único
para PRM, metas, plano de cuidado, complexidade e timeline longitudinal.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import engine
from models.consultorio_models import (
    BaseConsultorio,
    PacienteClinico,
    MedicamentoUso,
    ProblemaFarmacoterapeutico,
    MetaTerapeutica,
    AcaoPlanoCuidado,
)
from routers.consultorio import get_db_consultorio, get_current_user_consultorio, exigir_farmaceutico_ou_admin
from services.cuidado_farmaceutico import (
    PRM_CATEGORIAS,
    PRM_TIPOS,
    PRM_CATALOGO,
    PRM_CATALOGO_VERSAO,
    PRM_SISTEMA_CODIFICACAO,
    PRM_NATUREZAS,
    PRM_CRITICIDADES,
    DESFECHOS_PRM,
    ORIGENS_PRM,
    CAUSAS_PRM,
    STATUS_PRM,
    GRAVIDADES,
    METAS_PARAMETROS,
    STATUS_METAS,
    TIPOS_ACAO,
    STATUS_ACAO,
    CATEGORIAS_TIMELINE_UNIFICADA,
    calcular_complexidade_farmacoterapeutica,
    montar_dashboard_cuidado,
    montar_indicadores_prm,
    montar_resumo_cuidado,
    montar_timeline_unificada_cuidado,
    serializar_prm,
    serializar_meta,
    serializar_acao,
)

BaseConsultorio.metadata.create_all(bind=engine)


def _adicionar_coluna_prm_se_nao_existir(definicao_coluna: str) -> None:
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql(f"ALTER TABLE problemas_farmacoterapeuticos ADD COLUMN {definicao_coluna}")
            conn.commit()
    except Exception:
        pass


# Compatibilidade para bancos criados antes da padronização 14E.2C.1A.
_adicionar_coluna_prm_se_nao_existir("subcategoria VARCHAR")
_adicionar_coluna_prm_se_nao_existir("natureza VARCHAR DEFAULT 'MANIFESTO'")
_adicionar_coluna_prm_se_nao_existir("criticidade VARCHAR DEFAULT 'MODERADA'")
_adicionar_coluna_prm_se_nao_existir("desfecho VARCHAR DEFAULT 'NAO_AVALIADO'")
_adicionar_coluna_prm_se_nao_existir("causa_fator VARCHAR")
_adicionar_coluna_prm_se_nao_existir("condicao_saude VARCHAR")
_adicionar_coluna_prm_se_nao_existir("sistema_codificacao VARCHAR DEFAULT 'PRM_FE_NEES_V1'")
_adicionar_coluna_prm_se_nao_existir("versao_catalogo VARCHAR DEFAULT '2026.1'")
_adicionar_coluna_prm_se_nao_existir("codigo_externo VARCHAR")

router = APIRouter(prefix="/consultorio", tags=["Cuidado Farmacêutico"])


def _usuario_email(current: Any) -> str | None:
    return getattr(current, "email", None) or getattr(current, "nome", None)


@router.get("/cuidado/opcoes")
def opcoes_cuidado_farmaceutico(current=Depends(get_current_user_consultorio)):
    return {
        "prm_categorias": PRM_CATEGORIAS,
        "prm_catalogo": PRM_CATALOGO,
        "prm_tipos": PRM_TIPOS,
        "prm_naturezas": PRM_NATUREZAS,
        "prm_status": STATUS_PRM,
        "prm_desfechos": DESFECHOS_PRM,
        "prm_origens": ORIGENS_PRM,
        "prm_causas": CAUSAS_PRM,
        "prm_criticidades": PRM_CRITICIDADES,
        "gravidades": GRAVIDADES,
        "catalogo_versao": PRM_CATALOGO_VERSAO,
        "sistema_codificacao": PRM_SISTEMA_CODIFICACAO,
        "modelo": "duas_camadas_nees_pcne_fhir_compativel",
        "orientacao_prm": "Use campos controlados + descrição clínica complementar; preserve registros legados sem reclassificação automática.",
        "metas_parametros": METAS_PARAMETROS,
        "metas_status": STATUS_METAS,
        "tipos_acao": TIPOS_ACAO,
        "status_acao": STATUS_ACAO,
        "regra": "PRM -> Intervenção -> Meta -> Ação do plano -> Evolução/resultado",
        "timeline_unificada_categorias": CATEGORIAS_TIMELINE_UNIFICADA,
    }


@router.get("/cuidado/dashboard")
def dashboard_cuidado_farmaceutico(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    return montar_dashboard_cuidado(db)




@router.get("/cuidado/timeline-unificada/opcoes")
def opcoes_timeline_unificada(current=Depends(get_current_user_consultorio)):
    return {
        "categorias": CATEGORIAS_TIMELINE_UNIFICADA,
        "endpoint": "/consultorio/paciente-clinico/{paciente_id}/timeline-unificada",
        "descricao": "Timeline única do paciente reunindo CEAF, agenda, documentos, OCR, consultório, farmacoterapia, PRM, intervenções, metas, plano e desfechos.",
        "filtros": {"categorias": "lista separada por vírgula", "limite": "1 a 1000"},
    }



@router.get("/cuidado/prm-indicadores")
def indicadores_prm_globais(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    return montar_indicadores_prm(db)


@router.get("/paciente-clinico/{paciente_id}/prm-indicadores")
def indicadores_prm_paciente(
    paciente_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    paciente = db.query(PacienteClinico).filter(PacienteClinico.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente clínico não encontrado")
    return montar_indicadores_prm(db, paciente_id=paciente_id)


@router.get("/paciente-clinico/{paciente_id}/resumo-cuidado")
def resumo_cuidado_paciente(
    paciente_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    resumo = montar_resumo_cuidado(paciente_id, db)
    if resumo.get("erro"):
        raise HTTPException(status_code=404, detail=resumo["erro"])
    return resumo




@router.get("/paciente-clinico/{paciente_id}/timeline-unificada")
def timeline_unificada_paciente(
    paciente_id: int,
    categorias: str | None = None,
    limite: int = 300,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    categorias_lista = None
    if categorias:
        categorias_lista = [c.strip().upper() for c in categorias.split(",") if c.strip()]
    resultado = montar_timeline_unificada_cuidado(
        paciente_id=paciente_id,
        db=db,
        categorias=categorias_lista,
        limite=limite,
    )
    if resultado.get("erro"):
        raise HTTPException(status_code=404, detail=resultado["erro"])
    return resultado

@router.get("/paciente-clinico/{paciente_id}/complexidade-farmacoterapeutica")
def obter_complexidade_farmacoterapeutica(
    paciente_id: int,
    salvar: bool = False,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    paciente = db.query(PacienteClinico).filter(PacienteClinico.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente clínico não encontrado")
    return calcular_complexidade_farmacoterapeutica(paciente_id, db, usuario=_usuario_email(current), salvar=salvar)


@router.get("/paciente-clinico/{paciente_id}/prm")
def listar_prm(
    paciente_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    registros = db.query(ProblemaFarmacoterapeutico).filter(
        ProblemaFarmacoterapeutico.paciente_clinico_id == paciente_id
    ).order_by(ProblemaFarmacoterapeutico.data_identificacao.desc()).all()
    return {"paciente_id": paciente_id, "problemas": [serializar_prm(p) for p in registros]}


@router.post("/paciente-clinico/{paciente_id}/prm")
def criar_prm(
    paciente_id: int,
    payload: dict,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    exigir_farmaceutico_ou_admin(current)
    paciente = db.query(PacienteClinico).filter(PacienteClinico.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente clínico não encontrado")

    categoria = str(payload.get("categoria") or "").upper().strip()
    subcategoria = str(payload.get("subcategoria") or payload.get("tipo") or "").upper().strip()
    natureza = str(payload.get("natureza") or "MANIFESTO").upper().strip()
    criticidade = str(payload.get("criticidade") or payload.get("gravidade") or "MODERADA").upper().strip()
    status = str(payload.get("status") or "ABERTO").upper().strip()
    desfecho = str(payload.get("desfecho") or "NAO_AVALIADO").upper().strip()
    origem = str(payload.get("origem") or "CONSULTA_FARMACEUTICA").upper().strip()
    causa_fator = str(payload.get("causa_fator") or "").upper().strip() or None

    if categoria not in PRM_CATEGORIAS:
        raise HTTPException(status_code=422, detail=f"Categoria de PRM inválida. Use: {', '.join(PRM_CATEGORIAS)}")

    subcategorias_validas = {item["codigo"] for item in PRM_CATALOGO.get(categoria, [])}
    if subcategoria not in subcategorias_validas and subcategoria != "OUTRO":
        raise HTTPException(status_code=422, detail="Subcategoria incompatível com a categoria selecionada")
    if natureza not in PRM_NATUREZAS:
        raise HTTPException(status_code=422, detail=f"Natureza inválida. Use: {', '.join(PRM_NATUREZAS)}")
    if criticidade not in PRM_CRITICIDADES:
        raise HTTPException(status_code=422, detail=f"Criticidade inválida. Use: {', '.join(PRM_CRITICIDADES)}")
    if status not in STATUS_PRM:
        raise HTTPException(status_code=422, detail=f"Status inválido. Use: {', '.join(STATUS_PRM)}")
    if desfecho not in DESFECHOS_PRM:
        raise HTTPException(status_code=422, detail=f"Desfecho inválido. Use: {', '.join(DESFECHOS_PRM)}")
    if origem not in ORIGENS_PRM:
        origem = "OUTRO"
    if causa_fator and causa_fator not in CAUSAS_PRM:
        causa_fator = "OUTRA"

    if status in ("RESOLVIDO", "NAO_RESOLVIDO") and desfecho == "NAO_AVALIADO":
        raise HTTPException(status_code=422, detail="Informe o desfecho ao encerrar o PRM")

    medicamento_uso_id = payload.get("medicamento_uso_id")
    if medicamento_uso_id:
        med = db.query(MedicamentoUso).filter(MedicamentoUso.id == medicamento_uso_id, MedicamentoUso.paciente_clinico_id == paciente_id).first()
        if not med:
            raise HTTPException(status_code=404, detail="Medicamento não encontrado para este paciente")

    registro = ProblemaFarmacoterapeutico(
        paciente_clinico_id=paciente_id,
        medicamento_uso_id=medicamento_uso_id,
        categoria=categoria,
        tipo=subcategoria,
        subcategoria=subcategoria,
        natureza=natureza,
        gravidade=criticidade,
        criticidade=criticidade,
        descricao=payload.get("descricao"),
        evidencias=payload.get("evidencias"),
        causa_fator=causa_fator,
        condicao_saude=payload.get("condicao_saude"),
        status=status,
        desfecho=desfecho,
        origem=origem,
        sistema_codificacao=PRM_SISTEMA_CODIFICACAO,
        versao_catalogo=PRM_CATALOGO_VERSAO,
        codigo_externo=payload.get("codigo_externo"),
        criado_por=_usuario_email(current),
    )
    if status in ("RESOLVIDO", "NAO_RESOLVIDO", "REGISTRO_INVALIDO", "DESCARTADO"):
        registro.data_resolucao = datetime.utcnow()
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return {"ok": True, "problema": serializar_prm(registro)}


@router.put("/prm/{prm_id}/status")
def atualizar_status_prm(
    prm_id: int,
    payload: dict,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    exigir_farmaceutico_ou_admin(current)
    prm = db.query(ProblemaFarmacoterapeutico).filter(ProblemaFarmacoterapeutico.id == prm_id).first()
    if not prm:
        raise HTTPException(status_code=404, detail="PRM não encontrado")
    status = str(payload.get("status") or "").upper().strip()
    if status not in STATUS_PRM:
        raise HTTPException(status_code=422, detail=f"Status inválido. Use: {', '.join(STATUS_PRM)}")
    desfecho = str(payload.get("desfecho") or getattr(prm, "desfecho", None) or "NAO_AVALIADO").upper().strip()
    if desfecho not in DESFECHOS_PRM:
        raise HTTPException(status_code=422, detail=f"Desfecho inválido. Use: {', '.join(DESFECHOS_PRM)}")
    if status in ("RESOLVIDO", "NAO_RESOLVIDO") and desfecho == "NAO_AVALIADO":
        raise HTTPException(status_code=422, detail="Informe o desfecho ao encerrar o PRM")

    prm.status = status
    prm.desfecho = desfecho
    prm.resolucao = payload.get("resolucao") or prm.resolucao
    prm.atualizado_em = datetime.utcnow()
    if status in ("RESOLVIDO", "NAO_RESOLVIDO", "REGISTRO_INVALIDO", "DESCARTADO"):
        prm.data_resolucao = datetime.utcnow()
    db.commit()
    db.refresh(prm)
    return {"ok": True, "problema": serializar_prm(prm)}


@router.get("/paciente-clinico/{paciente_id}/metas-terapeuticas")
def listar_metas(
    paciente_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    metas = db.query(MetaTerapeutica).filter(MetaTerapeutica.paciente_clinico_id == paciente_id).order_by(MetaTerapeutica.criado_em.desc()).all()
    return {"paciente_id": paciente_id, "metas": [serializar_meta(m) for m in metas]}


@router.post("/paciente-clinico/{paciente_id}/metas-terapeuticas")
def criar_meta(
    paciente_id: int,
    payload: dict,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    exigir_farmaceutico_ou_admin(current)
    paciente = db.query(PacienteClinico).filter(PacienteClinico.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente clínico não encontrado")
    parametro = str(payload.get("parametro") or "OUTRO").upper().strip()
    if parametro not in METAS_PARAMETROS:
        parametro = "OUTRO"
    descricao = payload.get("descricao")
    if not descricao:
        raise HTTPException(status_code=422, detail="Descrição da meta é obrigatória")

    meta = MetaTerapeutica(
        paciente_clinico_id=paciente_id,
        problema_id=payload.get("problema_id"),
        parametro=parametro,
        descricao=descricao,
        valor_alvo=payload.get("valor_alvo"),
        valor_inicial=payload.get("valor_inicial"),
        unidade=payload.get("unidade"),
        prazo=payload.get("prazo"),
        status=str(payload.get("status") or "ATIVA").upper(),
        criado_por=_usuario_email(current),
    )
    db.add(meta)
    db.commit()
    db.refresh(meta)
    return {"ok": True, "meta": serializar_meta(meta)}


@router.put("/metas-terapeuticas/{meta_id}/avaliar")
def avaliar_meta(
    meta_id: int,
    payload: dict,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    exigir_farmaceutico_ou_admin(current)
    meta = db.query(MetaTerapeutica).filter(MetaTerapeutica.id == meta_id).first()
    if not meta:
        raise HTTPException(status_code=404, detail="Meta terapêutica não encontrada")
    status = str(payload.get("status") or meta.status).upper().strip()
    if status not in STATUS_METAS:
        raise HTTPException(status_code=422, detail=f"Status inválido. Use: {', '.join(STATUS_METAS)}")
    meta.status = status
    meta.valor_resultado = payload.get("valor_resultado")
    meta.resultado_observado = payload.get("resultado_observado")
    meta.data_avaliacao = datetime.utcnow()
    meta.atualizado_em = datetime.utcnow()
    db.commit()
    db.refresh(meta)
    return {"ok": True, "meta": serializar_meta(meta)}


@router.get("/paciente-clinico/{paciente_id}/acoes-plano-cuidado")
def listar_acoes(
    paciente_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    acoes = db.query(AcaoPlanoCuidado).filter(AcaoPlanoCuidado.paciente_clinico_id == paciente_id).order_by(AcaoPlanoCuidado.criado_em.desc()).all()
    return {"paciente_id": paciente_id, "acoes": [serializar_acao(a) for a in acoes]}


@router.post("/paciente-clinico/{paciente_id}/acoes-plano-cuidado")
def criar_acao(
    paciente_id: int,
    payload: dict,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    exigir_farmaceutico_ou_admin(current)
    paciente = db.query(PacienteClinico).filter(PacienteClinico.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente clínico não encontrado")
    tipo = str(payload.get("tipo_acao") or "OUTRO").upper().strip()
    if tipo not in TIPOS_ACAO:
        tipo = "OUTRO"
    descricao = payload.get("descricao")
    if not descricao:
        raise HTTPException(status_code=422, detail="Descrição da ação é obrigatória")
    acao = AcaoPlanoCuidado(
        paciente_clinico_id=paciente_id,
        problema_id=payload.get("problema_id"),
        meta_id=payload.get("meta_id"),
        intervencao_farmacoterapia_id=payload.get("intervencao_farmacoterapia_id"),
        tipo_acao=tipo,
        descricao=descricao,
        responsavel=payload.get("responsavel"),
        prazo=payload.get("prazo"),
        prioridade=str(payload.get("prioridade") or "NORMAL").upper(),
        status=str(payload.get("status") or "PENDENTE").upper(),
        criado_por=_usuario_email(current),
    )
    db.add(acao)
    db.commit()
    db.refresh(acao)
    return {"ok": True, "acao": serializar_acao(acao)}


@router.put("/acoes-plano-cuidado/{acao_id}/status")
def atualizar_status_acao(
    acao_id: int,
    payload: dict,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    exigir_farmaceutico_ou_admin(current)
    acao = db.query(AcaoPlanoCuidado).filter(AcaoPlanoCuidado.id == acao_id).first()
    if not acao:
        raise HTTPException(status_code=404, detail="Ação do plano não encontrada")
    status = str(payload.get("status") or "").upper().strip()
    if status not in STATUS_ACAO:
        raise HTTPException(status_code=422, detail=f"Status inválido. Use: {', '.join(STATUS_ACAO)}")
    acao.status = status
    acao.resultado = payload.get("resultado") or acao.resultado
    acao.atualizado_em = datetime.utcnow()
    if status == "CONCLUIDA":
        acao.concluido_em = datetime.utcnow()
    db.commit()
    db.refresh(acao)
    return {"ok": True, "acao": serializar_acao(acao)}
