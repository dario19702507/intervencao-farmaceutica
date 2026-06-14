"""Motor de vigência documental integrado à Agenda, Notificações e WhatsApp.

Passo 11D: Documento -> Vigência -> Agenda -> Notificação -> Fila WhatsApp.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from models.consultorio_models import (
    AgendaIntegrada,
    DocumentoPaciente,
    HistoricoVigenciaDocumento,
    NotificacaoInterna,
    PacienteClinico,
    WhatsAppEnvio,
)
from services.agenda_inteligente import (
    ajustar_para_proximo_dia_atendimento,
    calcular_data_alerta_renovacao,
    calcular_data_risco_pos_vencimento,
    horarios_do_dia,
    somar_meses,
)

OPERACOES_VIGENCIA = ["INCLUSAO", "RENOVACAO", "ADEQUACAO"]
STATUS_VIGENCIA = ["AGUARDANDO_INICIO", "ATIVA", "ENCERRADA", "SUBSTITUIDA", "VENCIDA"]


def _primeiro_dia_mes_subsequente(data_base: date) -> date:
    if data_base.month == 12:
        return date(data_base.year + 1, 1, 1)
    return date(data_base.year, data_base.month + 1, 1)


def aplicar_regra_dia_23(data_base: date) -> date:
    """Se a data calculada iniciar após o dia 23, transfere para 01 do mês subsequente."""
    if data_base.day > 23:
        return _primeiro_dia_mes_subsequente(data_base)
    return data_base


def calcular_fim_padrao(inicio: date, meses: int = 6) -> date:
    """Calcula fim de vigência padrão institucional: 6 meses menos 1 dia.

    Exemplo: início em 01/10/2026 -> fim em 31/03/2027.
    """
    return somar_meses(inicio, meses) - timedelta(days=1)




def calcular_primeira_retirada_inclusao(inicio_vigencia: date) -> dict:
    """Calcula o primeiro agendamento de retirada após o início de vigência.

    Regra 11G.1: toda inclusão deve gerar uma retirada no primeiro dia de
    funcionamento da Farmácia Escola a partir do início da vigência.

    Exemplo: início em sábado, 13/06/2026 -> segunda, 15/06/2026, 13:30.
    """
    data_retirada = ajustar_para_proximo_dia_atendimento(inicio_vigencia)
    horarios = horarios_do_dia(data_retirada)
    horario_inicio = horarios[0]["inicio"] if horarios else None
    return {"data": data_retirada, "horario_inicio": horario_inicio}

def _documento_vigente_atual(db: Session, paciente_id: int, documento_id_excluir: Optional[int] = None) -> Optional[DocumentoPaciente]:
    hoje = date.today()
    query = db.query(DocumentoPaciente).filter(
        DocumentoPaciente.paciente_id == paciente_id,
        DocumentoPaciente.tipo_documento == "LAUDO",
        DocumentoPaciente.ativo == True,  # noqa: E712
        DocumentoPaciente.vigencia_fim.isnot(None),
        DocumentoPaciente.vigencia_fim >= hoje,
    )
    if documento_id_excluir:
        query = query.filter(DocumentoPaciente.id != documento_id_excluir)
    return query.order_by(DocumentoPaciente.vigencia_fim.desc()).first()


def _documento_vencido_ate_tres_meses(db: Session, paciente_id: int, documento_id_excluir: Optional[int] = None) -> Optional[DocumentoPaciente]:
    hoje = date.today()
    limite_inferior = hoje - timedelta(days=92)
    query = db.query(DocumentoPaciente).filter(
        DocumentoPaciente.paciente_id == paciente_id,
        DocumentoPaciente.tipo_documento == "LAUDO",
        DocumentoPaciente.ativo == True,  # noqa: E712
        DocumentoPaciente.vigencia_fim.isnot(None),
        DocumentoPaciente.vigencia_fim < hoje,
        DocumentoPaciente.vigencia_fim >= limite_inferior,
    )
    if documento_id_excluir:
        query = query.filter(DocumentoPaciente.id != documento_id_excluir)
    return query.order_by(DocumentoPaciente.vigencia_fim.desc()).first()


def calcular_vigencia_documento(
    db: Session,
    documento: DocumentoPaciente,
    operacao_vigencia: Optional[str] = None,
    data_lancamento: Optional[date] = None,
) -> dict:
    """Calcula vigência com base nas regras da Farmácia Escola.

    Regras oficiais:
    - INCLUSAO: início = lançamento + 30 dias; se cair após dia 23, 01 do mês subsequente.
    - RENOVACAO com laudo vigente: início = dia seguinte ao fim do laudo vigente.
    - RENOVACAO vencida até 3 meses: início = cadastro + 8 dias; se após dia 23, 01 do mês subsequente.
    - ADEQUACAO: nova data a partir do cadastro, ajustada para dia de atendimento.
    """
    operacao = (operacao_vigencia or documento.operacao_vigencia or "").upper() or None
    hoje = data_lancamento or date.today()

    if documento.tipo_documento not in {"LAUDO", "RECEITA"}:
        return {"inicio": None, "fim": documento.data_validade, "status": None, "origem": "NAO_APLICAVEL"}

    if operacao == "INCLUSAO":
        inicio = aplicar_regra_dia_23(hoje + timedelta(days=30))
        origem = "INCLUSAO_D30"
    elif operacao == "RENOVACAO":
        vigente = _documento_vigente_atual(db, documento.paciente_id, documento.id)
        if vigente and vigente.vigencia_fim:
            inicio = vigente.vigencia_fim + timedelta(days=1)
            origem = f"RENOVACAO_APOS_LAUDO_{vigente.id}"
        else:
            vencido = _documento_vencido_ate_tres_meses(db, documento.paciente_id, documento.id)
            if vencido:
                inicio = aplicar_regra_dia_23(hoje + timedelta(days=8))
                origem = f"RENOVACAO_VENCIDA_ATE_3_MESES_{vencido.id}"
            else:
                inicio = aplicar_regra_dia_23(hoje + timedelta(days=8))
                origem = "RENOVACAO_SEM_LAUDO_REFERENCIA_D8"
    elif operacao == "ADEQUACAO":
        inicio = ajustar_para_proximo_dia_atendimento(hoje)
        origem = "ADEQUACAO_NOVA_DATA"
    else:
        inicio = documento.data_emissao or hoje
        origem = "DATA_EMISSAO_OU_CADASTRO"

    # Regra institucional 11D.1: a vigência automática do laudo/receita é
    # sempre calculada como início + 6 meses - 1 dia. A data_validade do
    # documento pode continuar registrada como metadado, mas não substitui a
    # vigência operacional. Exceções devem ser feitas pela edição manual de
    # vigência, com motivo e histórico obrigatórios.
    fim = calcular_fim_padrao(inicio)

    status = status_vigencia(inicio, fim)
    return {"inicio": inicio, "fim": fim, "status": status, "origem": origem}


def status_vigencia(inicio: Optional[date], fim: Optional[date], hoje: Optional[date] = None) -> Optional[str]:
    if not inicio and not fim:
        return None
    hoje = hoje or date.today()
    if inicio and hoje < inicio:
        return "AGUARDANDO_INICIO"
    if fim and hoje > fim:
        return "VENCIDA"
    return "ATIVA"


def registrar_historico_vigencia(
    db: Session,
    documento: DocumentoPaciente,
    anterior: dict,
    novo: dict,
    motivo: str,
    observacao: Optional[str],
    usuario: Optional[str],
    origem: str = "SISTEMA",
) -> None:
    db.add(
        HistoricoVigenciaDocumento(
            documento_id=documento.id,
            paciente_id=documento.paciente_id,
            vigencia_inicio_anterior=anterior.get("inicio"),
            vigencia_fim_anterior=anterior.get("fim"),
            vigencia_status_anterior=anterior.get("status"),
            vigencia_inicio_nova=novo.get("inicio"),
            vigencia_fim_nova=novo.get("fim"),
            vigencia_status_nova=novo.get("status"),
            motivo=motivo,
            observacao=observacao,
            usuario=usuario,
            origem=origem,
        )
    )


def aplicar_vigencia_calculada(
    db: Session,
    documento: DocumentoPaciente,
    operacao_vigencia: Optional[str],
    usuario: Optional[str],
    motivo: str = "Cálculo automático de vigência documental",
) -> dict:
    anterior = {
        "inicio": documento.vigencia_inicio,
        "fim": documento.vigencia_fim,
        "status": documento.vigencia_status,
    }
    calculada = calcular_vigencia_documento(db, documento, operacao_vigencia)
    documento.operacao_vigencia = operacao_vigencia or documento.operacao_vigencia
    documento.vigencia_inicio = calculada["inicio"]
    documento.vigencia_fim = calculada["fim"]
    documento.vigencia_status = calculada["status"]
    documento.vigencia_origem_calculo = calculada["origem"]
    documento.atualizado_em = datetime.utcnow()
    registrar_historico_vigencia(db, documento, anterior, calculada, motivo, None, usuario, origem="SISTEMA")
    return calculada


def _paciente(db: Session, paciente_id: Optional[int]) -> Optional[PacienteClinico]:
    if not paciente_id:
        return None
    return db.query(PacienteClinico).filter(PacienteClinico.id == paciente_id).first()


def _telefone_paciente(paciente: Optional[PacienteClinico]) -> Optional[str]:
    return getattr(paciente, "telefone", None) if paciente else None


def _nome_paciente(paciente: Optional[PacienteClinico], paciente_id: Optional[int]) -> str:
    return getattr(paciente, "nome", None) or f"Paciente ID {paciente_id}"


def criar_evento_notificacao_whatsapp_documento(
    db: Session,
    documento: DocumentoPaciente,
    usuario: Optional[str] = None,
) -> dict:
    """Cria Agenda e Notificação interna; WhatsApp documental somente manual a partir da vigência do documento.

    Evita duplicidade por referencia_tipo/referencia_id quando possível.
    """
    criados = {"agenda": 0, "notificacoes": 0, "whatsapp": 0}
    if documento.tipo_documento not in {"LAUDO", "RECEITA"} or not documento.vigencia_fim:
        return criados

    paciente = _paciente(db, documento.paciente_id)
    nome = _nome_paciente(paciente, documento.paciente_id)
    telefone = _telefone_paciente(paciente)

    # Evento de RETIRADA após INCLUSÃO: primeiro dia de funcionamento da
    # Farmácia Escola a partir do início da vigência. Esta regra é específica
    # para processos de inclusão e evita que a primeira retirada fique sem
    # agendamento operacional.
    operacao = (documento.operacao_vigencia or "").upper()
    if operacao == "INCLUSAO" and documento.vigencia_inicio:
        primeira_retirada = calcular_primeira_retirada_inclusao(documento.vigencia_inicio)
        evento_ret = db.query(AgendaIntegrada).filter(
            AgendaIntegrada.referencia_tipo == "DOCUMENTO_INCLUSAO_RETIRADA",
            AgendaIntegrada.referencia_id == documento.id,
        ).first()
        observacao_retirada = (
            f"Primeira retirada gerada automaticamente para inclusão. "
            f"Atendimento a partir das {primeira_retirada['horario_inicio']} horas."
            if primeira_retirada.get("horario_inicio")
            else "Primeira retirada gerada automaticamente para inclusão."
        )
        if not evento_ret:
            evento_ret = AgendaIntegrada(
                servico_origem="DOCUMENTO",
                tipo_evento="RETIRADA",
                paciente_id=documento.paciente_id,
                paciente_nome=nome,
                telefone=telefone,
                data_evento=primeira_retirada["data"],
                prioridade="NORMAL",
                status="AGENDADO",
                titulo=f"Primeira retirada após inclusão - {nome}",
                data_inicio_vigencia=documento.vigencia_inicio,
                data_fim_vigencia=documento.vigencia_fim,
                origem_importacao="DOCUMENTO",
                referencia_tipo="DOCUMENTO_INCLUSAO_RETIRADA",
                referencia_id=documento.id,
                observacoes=observacao_retirada,
                mensagem_notificacao=observacao_retirada,
            )
            db.add(evento_ret)
            db.flush()
            criados["agenda"] += 1
        else:
            evento_ret.data_evento = primeira_retirada["data"]
            evento_ret.data_inicio_vigencia = documento.vigencia_inicio
            evento_ret.data_fim_vigencia = documento.vigencia_fim
            evento_ret.paciente_nome = nome
            evento_ret.telefone = telefone
            evento_ret.observacoes = observacao_retirada
            evento_ret.mensagem_notificacao = observacao_retirada
            evento_ret.atualizado_em = datetime.utcnow()

    # Evento IMPORTANTE: renovação no segundo mês anterior ao vencimento.
    data_importante = calcular_data_alerta_renovacao(documento.vigencia_fim)
    evento = db.query(AgendaIntegrada).filter(
        AgendaIntegrada.referencia_tipo == "DOCUMENTO_RENOVACAO_IMPORTANTE",
        AgendaIntegrada.referencia_id == documento.id,
    ).first()
    if not evento:
        evento = AgendaIntegrada(
            servico_origem="DOCUMENTO",
            tipo_evento="RENOVACAO",
            paciente_id=documento.paciente_id,
            paciente_nome=nome,
            telefone=telefone,
            data_evento=data_importante,
            prioridade="IMPORTANTE",
            status="AGENDADO",
            titulo=f"Renovação de {documento.tipo_documento.lower()} - {nome}",
            data_inicio_vigencia=documento.vigencia_inicio,
            data_fim_vigencia=documento.vigencia_fim,
            origem_importacao="DOCUMENTO",
            referencia_tipo="DOCUMENTO_RENOVACAO_IMPORTANTE",
            referencia_id=documento.id,
            observacoes=f"Gerado automaticamente a partir do documento {documento.id}.",
        )
        db.add(evento)
        db.flush()
        criados["agenda"] += 1
    else:
        evento.data_evento = data_importante
        evento.data_inicio_vigencia = documento.vigencia_inicio
        evento.data_fim_vigencia = documento.vigencia_fim
        evento.paciente_nome = nome
        evento.telefone = telefone
        evento.atualizado_em = datetime.utcnow()

    notif = db.query(NotificacaoInterna).filter(
        NotificacaoInterna.evento_agenda_id == evento.id,
        NotificacaoInterna.tipo == "RENOVACAO",
        NotificacaoInterna.prioridade == "IMPORTANTE",
        NotificacaoInterna.lida == False,  # noqa: E712
    ).first()
    if not notif:
        notif = NotificacaoInterna(
            paciente_id=documento.paciente_id,
            evento_agenda_id=evento.id,
            tipo="RENOVACAO",
            prioridade="IMPORTANTE",
            origem="DOCUMENTO_AUTOMATICA",
            titulo=f"Renovação programada de {documento.tipo_documento.lower()}",
            mensagem=(
                f"{documento.tipo_documento.title()} do paciente {nome} vence em "
                f"{documento.vigencia_fim.strftime('%d/%m/%Y')}. Iniciar renovação."
            ),
            lida=False,
            necessita_acao=True,
        )
        db.add(notif)
        db.flush()
        criados["notificacoes"] += 1
    else:
        notif.mensagem = (
            f"{documento.tipo_documento.title()} do paciente {nome} vence em "
            f"{documento.vigencia_fim.strftime('%d/%m/%Y')}. Iniciar renovação."
        )

    # Regra 11F: pendências documentais geram notificações internas,
    # mas NÃO entram automaticamente na fila WhatsApp. O envio ao paciente
    # deve ser sempre manual, após avaliação do operador/farmacêutico.

    # Evento URGENTE: primeiro dia útil após vencimento sem renovação.
    data_urgente = calcular_data_risco_pos_vencimento(documento.vigencia_fim)
    evento_u = db.query(AgendaIntegrada).filter(
        AgendaIntegrada.referencia_tipo == "DOCUMENTO_RENOVACAO_URGENTE",
        AgendaIntegrada.referencia_id == documento.id,
    ).first()
    if not evento_u:
        evento_u = AgendaIntegrada(
            servico_origem="DOCUMENTO",
            tipo_evento="RENOVACAO",
            paciente_id=documento.paciente_id,
            paciente_nome=nome,
            telefone=telefone,
            data_evento=data_urgente,
            prioridade="URGENTE",
            status="AGENDADO",
            titulo=f"URGENTE: {documento.tipo_documento.lower()} vencido - {nome}",
            data_inicio_vigencia=documento.vigencia_inicio,
            data_fim_vigencia=documento.vigencia_fim,
            origem_importacao="DOCUMENTO",
            referencia_tipo="DOCUMENTO_RENOVACAO_URGENTE",
            referencia_id=documento.id,
            observacoes="Gerado automaticamente para primeiro dia útil após vencimento sem renovação.",
        )
        db.add(evento_u)
        db.flush()
        criados["agenda"] += 1
    else:
        evento_u.data_evento = data_urgente
        evento_u.data_inicio_vigencia = documento.vigencia_inicio
        evento_u.data_fim_vigencia = documento.vigencia_fim
        evento_u.paciente_nome = nome
        evento_u.telefone = telefone
        evento_u.atualizado_em = datetime.utcnow()

    notif_u = db.query(NotificacaoInterna).filter(
        NotificacaoInterna.evento_agenda_id == evento_u.id,
        NotificacaoInterna.tipo == "RENOVACAO",
        NotificacaoInterna.prioridade == "URGENTE",
        NotificacaoInterna.lida == False,  # noqa: E712
    ).first()
    if not notif_u:
        notif_u = NotificacaoInterna(
            paciente_id=documento.paciente_id,
            evento_agenda_id=evento_u.id,
            tipo="RENOVACAO",
            prioridade="URGENTE",
            origem="DOCUMENTO_AUTOMATICA",
            titulo=f"URGENTE: {documento.tipo_documento.lower()} vencido sem renovação",
            mensagem=(
                f"{documento.tipo_documento.title()} do paciente {nome} vence/venceu em "
                f"{documento.vigencia_fim.strftime('%d/%m/%Y')}. Ação imediata no primeiro dia útil após vencimento."
            ),
            lida=False,
            necessita_acao=True,
        )
        db.add(notif_u)
        db.flush()
        criados["notificacoes"] += 1
    else:
        notif_u.mensagem = (
            f"{documento.tipo_documento.title()} do paciente {nome} vence/venceu em "
            f"{documento.vigencia_fim.strftime('%d/%m/%Y')}. Ação imediata no primeiro dia útil após vencimento."
        )

    # Regra 11F: WhatsApp documental urgente também permanece manual.

    return criados


def recalcular_fluxo_documento(db: Session, documento: DocumentoPaciente, usuario: Optional[str] = None) -> dict:
    """Reprocessa vigência e cria vínculos operacionais derivados."""
    criados = criar_evento_notificacao_whatsapp_documento(db, documento, usuario=usuario)
    return {"documento_id": documento.id, "criados": criados}
