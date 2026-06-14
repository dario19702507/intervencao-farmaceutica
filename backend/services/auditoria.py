from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from models.consultorio_models import AuditoriaSistema


def registrar_auditoria(
    db: Session,
    current,
    modulo: str,
    acao: str,
    registro_id: Optional[int] = None,
    descricao: Optional[str] = None
):
    """Registra eventos relevantes do sistema para rastreabilidade.

    A função apenas adiciona o registro na sessão recebida. O commit continua
    sob responsabilidade da rota/serviço chamador, preservando o comportamento
    anterior do sistema.
    """
    usuario = (
        getattr(current, "nome", None)
        or getattr(current, "email", None)
        or "sistema"
    )

    auditoria = AuditoriaSistema(
        usuario=usuario,
        modulo=modulo,
        acao=acao,
        registro_id=registro_id,
        descricao=descricao,
        criado_em=datetime.utcnow()
    )

    db.add(auditoria)
    return auditoria
