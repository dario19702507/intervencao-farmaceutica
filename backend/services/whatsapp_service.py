"""Camada preparatória para WhatsApp.

Passo 10E: cria fila e status de envio sem depender ainda de API externa.
O envio real será conectado posteriormente a um provedor como Evolution API ou Meta Cloud API.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from models.consultorio_models import AgendaIntegrada, NotificacaoInterna, WhatsAppEnvio

STATUS_WHATSAPP = ["PENDENTE", "SIMULADO", "ENVIADO", "ERRO", "CANCELADO", "BLOQUEADO"]
PROVEDORES_WHATSAPP = ["SIMULADOR", "EVOLUTION_API", "META_CLOUD_API"]
ORIGENS_WHATSAPP = ["NOTIFICACAO_INTERNA", "MANUAL", "SISTEMA"]


ORIGENS_BLOQUEADAS_WHATSAPP_AUTOMATICO = {
    "DOCUMENTO_AUTOMATICA",
    "PROCESSO_DOCUMENTAL",
    "PENDENCIA_DOCUMENTAL",
}

TIPOS_BLOQUEADOS_WHATSAPP_AUTOMATICO = {
    "DOCUMENTO",
    "PENDENCIA_DOCUMENTAL",
}


def notificacao_permite_whatsapp_automatico(notificacao: NotificacaoInterna) -> bool:
    """Bloqueia WhatsApp automático para pendências documentais.

    A comunicação documental é intencionalmente manual para evitar mensagens
    ambíguas ou confusas ao paciente. O operador pode usar /whatsapp/envio-manual.
    """
    origem = (getattr(notificacao, "origem", None) or "").upper()
    tipo = (getattr(notificacao, "tipo", None) or "").upper()
    return origem not in ORIGENS_BLOQUEADAS_WHATSAPP_AUTOMATICO and tipo not in TIPOS_BLOQUEADOS_WHATSAPP_AUTOMATICO


def normalizar_telefone(telefone: Optional[str]) -> Optional[str]:
    if not telefone:
        return None
    digitos = "".join(ch for ch in str(telefone) if ch.isdigit())
    if not digitos:
        return None
    return digitos


def obter_telefone_notificacao(notificacao: NotificacaoInterna) -> Optional[str]:
    if getattr(notificacao, "evento", None) and getattr(notificacao.evento, "telefone", None):
        return normalizar_telefone(notificacao.evento.telefone)
    return None


def mensagem_padrao_notificacao(notificacao: NotificacaoInterna) -> str:
    return f"{notificacao.titulo}\n\n{notificacao.mensagem}"


def serializar_envio(envio: WhatsAppEnvio) -> dict:
    return {
        "id": envio.id,
        "notificacao_id": envio.notificacao_id,
        "paciente_id": envio.paciente_id,
        "telefone": envio.telefone,
        "mensagem": envio.mensagem,
        "status": envio.status,
        "provedor": envio.provedor,
        "origem": envio.origem,
        "prioridade": envio.prioridade,
        "tentativa_envio": envio.tentativa_envio,
        "ultimo_erro": envio.ultimo_erro,
        "data_programada": envio.data_programada,
        "data_envio": envio.data_envio,
        "criado_em": envio.criado_em,
        "atualizado_em": envio.atualizado_em,
        "criado_por": envio.criado_por,
    }


def criar_envio_manual(
    db: Session,
    *,
    telefone: str,
    mensagem: str,
    paciente_id: Optional[int] = None,
    prioridade: str = "NORMAL",
    data_programada: Optional[datetime] = None,
    criado_por: Optional[str] = None,
) -> WhatsAppEnvio:
    telefone_normalizado = normalizar_telefone(telefone)
    envio = WhatsAppEnvio(
        notificacao_id=None,
        paciente_id=paciente_id,
        telefone=telefone_normalizado,
        mensagem=mensagem,
        status="PENDENTE" if telefone_normalizado else "BLOQUEADO",
        provedor="SIMULADOR",
        origem="MANUAL",
        prioridade=(prioridade or "NORMAL").upper(),
        data_programada=data_programada,
        criado_por=criado_por,
        ultimo_erro=None if telefone_normalizado else "Telefone ausente ou inválido.",
    )
    db.add(envio)
    return envio


def enfileirar_notificacao(db: Session, notificacao: NotificacaoInterna, criado_por: Optional[str] = None) -> Optional[WhatsAppEnvio]:
    if not notificacao_permite_whatsapp_automatico(notificacao):
        return None

    existente = db.query(WhatsAppEnvio).filter(WhatsAppEnvio.notificacao_id == notificacao.id).first()
    if existente:
        return None

    telefone = obter_telefone_notificacao(notificacao)
    envio = WhatsAppEnvio(
        notificacao_id=notificacao.id,
        paciente_id=notificacao.paciente_id,
        telefone=telefone,
        mensagem=mensagem_padrao_notificacao(notificacao),
        status="PENDENTE" if telefone else "BLOQUEADO",
        provedor="SIMULADOR",
        origem="NOTIFICACAO_INTERNA",
        prioridade=(notificacao.prioridade or "NORMAL").upper(),
        criado_por=criado_por,
        ultimo_erro=None if telefone else "Notificação sem telefone vinculado ao evento da agenda.",
    )
    db.add(envio)
    return envio


def enfileirar_notificacoes_pendentes(db: Session, criado_por: Optional[str] = None) -> Dict[str, int]:
    notificacoes = db.query(NotificacaoInterna).filter(
        NotificacaoInterna.lida == False,  # noqa: E712
        NotificacaoInterna.enviada_whatsapp == False,  # noqa: E712
    ).all()
    criadas = 0
    ignoradas = 0
    bloqueadas = 0

    for notificacao in notificacoes:
        envio = enfileirar_notificacao(db, notificacao, criado_por=criado_por)
        if envio is None:
            ignoradas += 1
        else:
            criadas += 1
            if envio.status == "BLOQUEADO":
                bloqueadas += 1

    db.commit()
    return {"criadas": criadas, "ignoradas": ignoradas, "bloqueadas": bloqueadas}


def simular_envios_pendentes(db: Session, limite: int = 50) -> Dict[str, int]:
    itens = db.query(WhatsAppEnvio).filter(WhatsAppEnvio.status == "PENDENTE").order_by(
        WhatsAppEnvio.prioridade.desc(), WhatsAppEnvio.criado_em.asc()
    ).limit(max(1, min(limite, 200))).all()
    enviados = 0
    agora = datetime.utcnow()

    for envio in itens:
        envio.status = "SIMULADO"
        envio.tentativa_envio = (envio.tentativa_envio or 0) + 1
        envio.data_envio = agora
        envio.atualizado_em = agora
        envio.ultimo_erro = None
        if envio.notificacao:
            envio.notificacao.enviada_whatsapp = True
            envio.notificacao.data_envio_whatsapp = agora
            envio.notificacao.status_envio_whatsapp = "SIMULADO"
        enviados += 1

    db.commit()
    return {"simulados": enviados}


def dashboard_whatsapp(db: Session) -> Dict[str, int]:
    total = db.query(WhatsAppEnvio).count()
    pendentes = db.query(WhatsAppEnvio).filter(WhatsAppEnvio.status == "PENDENTE").count()
    simulados = db.query(WhatsAppEnvio).filter(WhatsAppEnvio.status == "SIMULADO").count()
    enviados = db.query(WhatsAppEnvio).filter(WhatsAppEnvio.status == "ENVIADO").count()
    erros = db.query(WhatsAppEnvio).filter(WhatsAppEnvio.status == "ERRO").count()
    bloqueados = db.query(WhatsAppEnvio).filter(WhatsAppEnvio.status == "BLOQUEADO").count()
    cancelados = db.query(WhatsAppEnvio).filter(WhatsAppEnvio.status == "CANCELADO").count()
    urgentes_pendentes = db.query(WhatsAppEnvio).filter(
        WhatsAppEnvio.status == "PENDENTE", WhatsAppEnvio.prioridade == "URGENTE"
    ).count()
    return {
        "total": total,
        "pendentes": pendentes,
        "simulados": simulados,
        "enviados": enviados,
        "erros": erros,
        "bloqueados": bloqueados,
        "cancelados": cancelados,
        "urgentes_pendentes": urgentes_pendentes,
    }
