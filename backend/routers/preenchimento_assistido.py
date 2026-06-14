"""Rotas de pré-preenchimento assistido.

Passo 12E: sugestões baseadas exclusivamente em documentos VALIDADOS e OCR já
realizado. A aplicação exige confirmação do operador e não altera paciente,
vigência, agenda, notificações ou WhatsApp automaticamente.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import engine
from models.consultorio_models import BaseConsultorio
from routers.consultorio import get_db_consultorio, get_current_user_consultorio
from services.preenchimento_assistido import (
    CAMPOS_ASSISTIDOS,
    aplicar_sugestoes_ao_processo,
    gerar_sugestoes_preenchimento_processo,
)

BaseConsultorio.metadata.create_all(bind=engine)

router = APIRouter(prefix="/consultorio", tags=["Pré-preenchimento Assistido"])


class AplicarSugestoesPayload(BaseModel):
    campos: List[str]
    observacao: Optional[str] = None


def _exigir_farmaceutico_ou_admin(current_user=Depends(get_current_user_consultorio)):
    perfil = (getattr(current_user, "perfil", "") or "").lower()
    if perfil not in {"admin", "farmaceutico", "farmacêutico"}:
        raise HTTPException(status_code=403, detail="Acesso permitido apenas para farmacêutico ou administrador")
    return current_user


@router.get("/preenchimento-assistido/opcoes")
def opcoes_preenchimento_assistido(current=Depends(get_current_user_consultorio)):
    return {
        "campos_assistidos": CAMPOS_ASSISTIDOS,
        "fontes_autorizadas": ["DOCUMENTOS_VALIDADOS"],
        "atualizacao_automatica": False,
        "regra_seguranca": "As sugestões não alteram paciente, vigência, agenda, notificação ou WhatsApp sem confirmação do operador.",
    }


@router.get("/processos-documentais/{processo_id}/preenchimento-assistido")
def obter_sugestoes_preenchimento_assistido(
    processo_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    try:
        return gerar_sugestoes_preenchimento_processo(db, processo_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/processos-documentais/{processo_id}/preenchimento-assistido/aplicar")
def aplicar_preenchimento_assistido(
    processo_id: int,
    payload: AplicarSugestoesPayload,
    db: Session = Depends(get_db_consultorio),
    current=Depends(_exigir_farmaceutico_ou_admin),
):
    try:
        return aplicar_sugestoes_ao_processo(
            db,
            processo_id,
            payload.campos,
            usuario=getattr(current, "email", None),
            observacao=payload.observacao,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
