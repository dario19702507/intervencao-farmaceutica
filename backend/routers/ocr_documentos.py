"""Rotas de OCR/extração inicial de documentos.

Passo 12A: extrair texto e campos sugeridos para conferência humana, sem
atualização automática de paciente, processo, vigência, agenda ou WhatsApp.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import engine
from models.consultorio_models import BaseConsultorio, DocumentoPaciente, ExtracaoDocumentoOCR, ProcessoDocumental
from routers.consultorio import get_db_consultorio, get_current_user_consultorio
from services.ocr_documentos import extrair_texto_arquivo, sugerir_campos, dumps_sugestoes, loads_sugestoes, classificar_documento, TIPOS_DOCUMENTAIS_OCR

BaseConsultorio.metadata.create_all(bind=engine)

router = APIRouter(prefix="/consultorio", tags=["OCR Documental"])


class ClassificacaoManualUpdate(BaseModel):
    tipo: str
    observacao: str | None = None



def _exigir_farmaceutico_ou_admin(current_user=Depends(get_current_user_consultorio)):
    perfil = (getattr(current_user, "perfil", "") or "").lower()
    if perfil not in {"admin", "farmaceutico", "farmacêutico"}:
        raise HTTPException(status_code=403, detail="Acesso permitido apenas para farmacêutico ou administrador")
    return current_user


def _serializar_extracao(extracao: ExtracaoDocumentoOCR):
    campos_sugeridos = loads_sugestoes(extracao.campos_sugeridos_json)
    classificacao = campos_sugeridos.get("classificacao_documental") or classificar_documento(extracao.texto_extraido or "")
    return {
        "id": extracao.id,
        "documento_id": extracao.documento_id,
        "paciente_id": extracao.paciente_id,
        "processo_documental_id": extracao.processo_documental_id,
        "metodo": extracao.metodo,
        "status": extracao.status,
        "texto_extraido": extracao.texto_extraido,
        "tamanho_texto": len(extracao.texto_extraido or ""),
        "campos_sugeridos": campos_sugeridos,
        "classificacao_documental": classificacao,
        "tipo_documento_sugerido": classificacao.get("tipo"),
        "confianca_classificacao": classificacao.get("confianca"),
        "erro": extracao.erro,
        "criado_por": extracao.criado_por,
        "criado_em": extracao.criado_em.isoformat() if extracao.criado_em else None,
    }


@router.get("/documentos/ocr/opcoes")
def opcoes_ocr_documental(current_user=Depends(get_current_user_consultorio)):
    return {
        "status": ["CONCLUIDO", "SEM_TEXTO_EXTRAIDO", "ERRO"],
        "metodos": ["PDF_TEXTO", "TEXTO_SIMPLES", "IMAGEM_OCR_OPCIONAL", "NAO_SUPORTADO"],
        "tipos_documentais_classificacao": TIPOS_DOCUMENTAIS_OCR,
        "observacao": "As informações extraídas e classificações são apenas sugestões para conferência humana.",
        "atualizacao_automatica_cadastro": False,
        "atualizacao_automatica_tipo_documento": False,
    }




@router.get("/documentos/{documento_id}/ocr/classificacao")
def obter_classificacao_documento(
    documento_id: int,
    db: Session = Depends(get_db_consultorio),
    current_user=Depends(get_current_user_consultorio),
):
    extracao = (
        db.query(ExtracaoDocumentoOCR)
        .filter(ExtracaoDocumentoOCR.documento_id == documento_id)
        .order_by(ExtracaoDocumentoOCR.criado_em.desc())
        .first()
    )
    if not extracao:
        return {
            "documento_id": documento_id,
            "classificacao_documental": None,
            "mensagem": "Nenhuma extração OCR encontrada para este documento.",
        }
    return {
        "documento_id": documento_id,
        "classificacao_documental": _serializar_extracao(extracao).get("classificacao_documental"),
        "atualizacao_automatica": False,
    }


@router.patch("/documentos/{documento_id}/ocr/classificacao")
def reclassificar_documento_ocr(
    documento_id: int,
    payload: ClassificacaoManualUpdate,
    db: Session = Depends(get_db_consultorio),
    current_user=Depends(_exigir_farmaceutico_ou_admin),
):
    tipo = (payload.tipo or "").upper().strip()
    if tipo not in TIPOS_DOCUMENTAIS_OCR:
        raise HTTPException(status_code=400, detail="Tipo documental inválido")

    extracao = (
        db.query(ExtracaoDocumentoOCR)
        .filter(ExtracaoDocumentoOCR.documento_id == documento_id)
        .order_by(ExtracaoDocumentoOCR.criado_em.desc())
        .first()
    )
    if not extracao:
        raise HTTPException(status_code=404, detail="Nenhuma extração OCR encontrada para este documento")

    campos = loads_sugestoes(extracao.campos_sugeridos_json)
    classificacao_atual = campos.get("classificacao_documental") or classificar_documento(extracao.texto_extraido or "")
    campos["classificacao_documental"] = {
        **classificacao_atual,
        "tipo": tipo,
        "confianca": 1.0,
        "manual": True,
        "classificado_por": getattr(current_user, "email", None),
        "classificado_em": datetime.utcnow().isoformat(),
        "observacao": payload.observacao or "Reclassificação manual pelo operador",
    }
    extracao.campos_sugeridos_json = dumps_sugestoes(campos)
    db.commit()
    db.refresh(extracao)
    return {"ok": True, "extracao": _serializar_extracao(extracao)}


@router.post("/documentos/{documento_id}/ocr/extrair")
def extrair_ocr_documento(
    documento_id: int,
    db: Session = Depends(get_db_consultorio),
    current_user=Depends(_exigir_farmaceutico_ou_admin),
):
    documento = db.query(DocumentoPaciente).filter(DocumentoPaciente.id == documento_id, DocumentoPaciente.ativo == True).first()
    if not documento:
        raise HTTPException(status_code=404, detail="Documento não encontrado")

    resultado = extrair_texto_arquivo(documento.caminho_arquivo, documento.content_type)
    texto = resultado["texto"]
    sugestoes = sugerir_campos(texto)

    extracao = ExtracaoDocumentoOCR(
        documento_id=documento.id,
        paciente_id=documento.paciente_id,
        processo_documental_id=getattr(documento, "processo_documental_id", None),
        metodo=resultado["metodo"],
        status=resultado["status"],
        texto_extraido=texto,
        campos_sugeridos_json=dumps_sugestoes(sugestoes),
        criado_por=getattr(current_user, "email", None),
        criado_em=datetime.utcnow(),
    )
    db.add(extracao)
    db.commit()
    db.refresh(extracao)
    return {"ok": True, "extracao": _serializar_extracao(extracao)}


@router.get("/documentos/{documento_id}/ocr")
def listar_ocr_documento(
    documento_id: int,
    db: Session = Depends(get_db_consultorio),
    current_user=Depends(get_current_user_consultorio),
):
    extracoes = (
        db.query(ExtracaoDocumentoOCR)
        .filter(ExtracaoDocumentoOCR.documento_id == documento_id)
        .order_by(ExtracaoDocumentoOCR.criado_em.desc())
        .all()
    )
    return {"documento_id": documento_id, "extracoes": [_serializar_extracao(e) for e in extracoes]}


@router.get("/processos-documentais/{processo_id}/ocr")
def listar_ocr_processo_documental(
    processo_id: int,
    db: Session = Depends(get_db_consultorio),
    current_user=Depends(get_current_user_consultorio),
):
    processo = db.query(ProcessoDocumental).filter(ProcessoDocumental.id == processo_id).first()
    if not processo:
        raise HTTPException(status_code=404, detail="Processo documental não encontrado")

    extracoes = (
        db.query(ExtracaoDocumentoOCR)
        .filter(ExtracaoDocumentoOCR.processo_documental_id == processo_id)
        .order_by(ExtracaoDocumentoOCR.criado_em.desc())
        .all()
    )
    return {"processo_id": processo_id, "extracoes": [_serializar_extracao(e) for e in extracoes]}
