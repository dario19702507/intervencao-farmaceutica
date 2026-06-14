"""Rotas administrativas para migração segura do App de Intervenções."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from database import get_db
from routers.consultorio import get_current_user_consultorio
from services.migracao_intervencoes import (
    CAMPOS_ESPERADOS,
    carregar_json_bytes,
    consolidar_batch,
    criar_checkpoint,
    dashboard_migracao,
    garantir_estrutura_migracao,
    importar_para_staging,
    rollback_batch_importacao,
    listar_checkpoints_migracao,
    avaliar_consistencia_migracao,
    rastreabilidade_migracao,
    resumo_integracao_intervencoes,
)

router = APIRouter(prefix="/consultorio/migracao-intervencoes", tags=["Migração de Intervenções"])


def _exigir_admin(user):
    if getattr(user, "perfil", None) != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem executar migração de dados")
    return user


@router.get("/opcoes")
def opcoes_migracao_intervencoes(current_user=Depends(get_current_user_consultorio)):
    return {
        "origem_sistema": "APP_INTERVENCOES",
        "fonte_recomendada": "JSON exportado do Supabase",
        "campos_esperados": CAMPOS_ESPERADOS,
        "fluxo_seguro": [
            "1. Criar checkpoint pré-importação",
            "2. Importar JSON para staging",
            "3. Conferir dashboard/validação",
            "4. Consolidar registros validados",
            "5. Criar checkpoint pós-consolidação",
        ],
        "idempotente": True,
        "duplicidades": "Controladas por origem_sistema + origem_id",
    }


@router.post("/checkpoint")
def criar_checkpoint_migracao(
    etapa: str = "MANUAL",
    descricao: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_consultorio),
):
    _exigir_admin(current_user)
    return criar_checkpoint(db, etapa=etapa, descricao=descricao, usuario_email=getattr(current_user, "email", None))


@router.get("/dashboard")
def obter_dashboard_migracao(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_consultorio),
):
    _exigir_admin(current_user)
    return dashboard_migracao(db)




@router.get("/integracao-resumo")
def obter_resumo_integracao_intervencoes(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_consultorio),
):
    _exigir_admin(current_user)
    return resumo_integracao_intervencoes(db)


@router.get("/checkpoints")
def listar_checkpoints_intervencoes(
    limite: int = 50,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_consultorio),
):
    _exigir_admin(current_user)
    return listar_checkpoints_migracao(db, limite=limite)


@router.get("/consistencia")
def verificar_consistencia_intervencoes(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_consultorio),
):
    _exigir_admin(current_user)
    return avaliar_consistencia_migracao(db)


@router.get("/rastreabilidade")
def consultar_rastreabilidade_intervencoes(
    limite: int = 100,
    status: str | None = None,
    batch_id: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_consultorio),
):
    _exigir_admin(current_user)
    return rastreabilidade_migracao(db, limite=limite, status=status, batch_id=batch_id)


@router.post("/staging/importar-json")
async def importar_json_para_staging(
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_consultorio),
):
    _exigir_admin(current_user)
    if not arquivo.filename.lower().endswith(".json"):
        raise HTTPException(status_code=400, detail="Envie um arquivo .json exportado do Supabase")
    try:
        rows = carregar_json_bytes(await arquivo.read())
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"JSON inválido: {exc}")
    resultado = importar_para_staging(db, rows, usuario_email=getattr(current_user, "email", None))
    return {"ok": True, "arquivo": arquivo.filename, "total_lido": len(rows), **resultado}


@router.post("/consolidar")
def consolidar_migracao(
    batch_id: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_consultorio),
):
    _exigir_admin(current_user)
    return consolidar_batch(
        db,
        batch_id=batch_id,
        usuario_id=getattr(current_user, "id", None),
        usuario_email=getattr(current_user, "email", None),
    )


@router.post("/rollback")
def rollback_migracao(
    batch_importacao: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_consultorio),
):
    _exigir_admin(current_user)
    return rollback_batch_importacao(db, batch_importacao=batch_importacao, usuario_email=getattr(current_user, "email", None))


@router.post("/preparar-estrutura")
def preparar_estrutura_migracao(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_consultorio),
):
    _exigir_admin(current_user)
    garantir_estrutura_migracao(db)
    return {"ok": True, "mensagem": "Estrutura de migração verificada/criada com sucesso"}
