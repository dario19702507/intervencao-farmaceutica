from datetime import datetime, date, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from models.consultorio_models import (
    AgendaIntegrada,
    CapacidadeAgenda,
    NotificacaoAgenda,
    PacienteAgenda,
)
from services.agenda_inteligente import (
    calcular_proxima_retirada,
    calcular_data_alerta_renovacao,
    calcular_data_risco_pos_vencimento,
)


def obter_ou_criar_paciente_agenda(
    db: Session,
    nome: str,
    telefone: Optional[str] = None,
    cpf: Optional[str] = None,
    cns: Optional[str] = None,
    origem: str = "integracao"
):
    if not nome:
        return None

    paciente = None

    if cpf:
        paciente = db.query(PacienteAgenda).filter(PacienteAgenda.cpf == cpf).first()

    if not paciente and cns:
        paciente = db.query(PacienteAgenda).filter(PacienteAgenda.cns == cns).first()

    if not paciente and telefone:
        paciente = db.query(PacienteAgenda).filter(
            PacienteAgenda.nome == nome,
            PacienteAgenda.telefone == telefone
        ).first()

    if not paciente:
        paciente = db.query(PacienteAgenda).filter(PacienteAgenda.nome == nome).first()

    if paciente:
        if telefone and not paciente.telefone:
            paciente.telefone = telefone
        if cpf and not paciente.cpf:
            paciente.cpf = cpf
        if cns and not paciente.cns:
            paciente.cns = cns

        paciente.atualizado_em = datetime.utcnow()
        db.flush()
        return paciente

    paciente = PacienteAgenda(
        nome=nome,
        telefone=telefone,
        cpf=cpf,
        cns=cns,
        origem=origem,
        ativo=True
    )

    db.add(paciente)
    db.flush()
    db.refresh(paciente)

    return paciente


def calcular_capacidade_agenda(
    db: Session,
    servico_origem: str,
    data_evento: date,
    ignorar_agenda_id: Optional[int] = None
):
    if not data_evento:
        return {
            "capacidade_configurada": False,
            "capacidade_maxima": None,
            "agendados": 0,
            "vagas_disponiveis": None,
            "capacidade_atingida": False,
        }

    dia_semana = data_evento.weekday()

    capacidade = db.query(CapacidadeAgenda).filter(
        CapacidadeAgenda.servico_origem == servico_origem,
        CapacidadeAgenda.dia_semana == dia_semana,
        CapacidadeAgenda.ativo == True
    ).first()

    capacidade_maxima = (
        capacidade.capacidade_maxima
        if capacidade
        else None
    )

    query = db.query(AgendaIntegrada).filter(
        AgendaIntegrada.servico_origem == servico_origem,
        AgendaIntegrada.data_evento == data_evento,
        AgendaIntegrada.status.in_([
            "agendado",
            "notificado",
            "reagendado"
        ])
    )

    if ignorar_agenda_id:
        query = query.filter(
            AgendaIntegrada.id != ignorar_agenda_id
        )

    agendados = query.count()

    vagas_disponiveis = (
        capacidade_maxima - agendados
        if capacidade_maxima is not None
        else None
    )

    capacidade_atingida = (
        agendados >= capacidade_maxima
        if capacidade_maxima is not None
        else False
    )

    return {
        "capacidade_configurada": capacidade is not None,
        "capacidade_maxima": capacidade_maxima,
        "agendados": agendados,
        "vagas_disponiveis": vagas_disponiveis,
        "capacidade_atingida": capacidade_atingida,
    }


def criar_proxima_dispensacao_automatica(
    db: Session,
    agenda_atual: AgendaIntegrada
):
    """Cria a próxima retirada respeitando limite de 30 dias e funcionamento.

    A regra operacional definida para a Farmácia Escola é: a próxima retirada
    deve respeitar o limite máximo de 30 dias e cair em dia de atendimento.
    Quando D+30 cair em sexta, sábado ou domingo, a agenda recua para o dia de
    atendimento anterior, preservando o limite de 30 dias.
    """
    servico_normalizado = (agenda_atual.servico_origem or "").strip().lower()
    tipo_normalizado = (agenda_atual.tipo_evento or "").strip().upper()

    if servico_normalizado not in ["dispensacao", "dispensação", "agenda"] and tipo_normalizado != "RETIRADA":
        return None

    if not agenda_atual.data_evento:
        return None

    proxima_data = calcular_proxima_retirada(agenda_atual.data_evento, "MENSAL")

    dentro_da_vigencia = not (
        agenda_atual.data_fim_vigencia
        and proxima_data > agenda_atual.data_fim_vigencia
    )

    if not dentro_da_vigencia:
        alerta_existente = db.query(AgendaIntegrada).filter(
            AgendaIntegrada.evento_pai_id == agenda_atual.id,
            AgendaIntegrada.status == "risco_interrupcao_tratamento"
        ).first()
        if alerta_existente:
            alerta_existente._origem_automacao = "existente"
            return alerta_existente

        alerta = AgendaIntegrada(
            evento_pai_id=agenda_atual.id,
            servico_origem="renovacao_laudo",
            tipo_evento="RENOVACAO",
            prioridade="URGENTE",
            paciente_id=agenda_atual.paciente_id,
            paciente_nome=agenda_atual.paciente_nome,
            telefone=agenda_atual.telefone,
            medicamento_id=getattr(agenda_atual, "medicamento_id", None),
            medicamento=agenda_atual.medicamento,
            data_evento=calcular_data_risco_pos_vencimento(agenda_atual.data_fim_vigencia),
            data_inicio_vigencia=agenda_atual.data_inicio_vigencia,
            data_fim_vigencia=agenda_atual.data_fim_vigencia,
            situacao_laudo="risco_interrupcao_tratamento",
            status="risco_interrupcao_tratamento",
            data_status=datetime.utcnow(),
            usuario_status="sistema",
            notificar_whatsapp=True,
            observacoes=(
                "Próxima retirada automática não criada porque a vigência do laudo "
                "termina antes da próxima retirada prevista. Alerta programado para "
                "o segundo mês após o vencimento."
            )
        )
        db.add(alerta)
        db.flush()
        db.refresh(alerta)
        alerta._origem_automacao = "risco_interrupcao"
        return alerta

    query_existente = db.query(AgendaIntegrada).filter(
        AgendaIntegrada.id != agenda_atual.id,
        AgendaIntegrada.tipo_evento == "RETIRADA",
        AgendaIntegrada.medicamento == agenda_atual.medicamento,
        AgendaIntegrada.status.in_(["agendado", "notificado", "reagendado", "AGENDADO"]),
        AgendaIntegrada.data_evento >= proxima_data
    )

    if agenda_atual.paciente_id:
        query_existente = query_existente.filter(AgendaIntegrada.paciente_id == agenda_atual.paciente_id)
    else:
        query_existente = query_existente.filter(
            AgendaIntegrada.paciente_nome == agenda_atual.paciente_nome,
            AgendaIntegrada.telefone == agenda_atual.telefone
        )

    existe = query_existente.first()
    if existe:
        existe._origem_automacao = "existente"
        return existe

    novo_evento = AgendaIntegrada(
        evento_pai_id=agenda_atual.id,
        servico_origem="dispensacao",
        tipo_evento="RETIRADA",
        prioridade="NORMAL",
        paciente_id=agenda_atual.paciente_id,
        paciente_nome=agenda_atual.paciente_nome,
        telefone=agenda_atual.telefone,
        medicamento_id=getattr(agenda_atual, "medicamento_id", None),
        medicamento=agenda_atual.medicamento,
        data_evento=proxima_data,
        data_inicio_vigencia=agenda_atual.data_inicio_vigencia,
        data_fim_vigencia=agenda_atual.data_fim_vigencia,
        situacao_laudo=agenda_atual.situacao_laudo,
        status="AGENDADO",
        notificar_whatsapp=True,
        observacoes=(
            "Agendamento inteligente gerado após retirada realizada em "
            f"{agenda_atual.data_evento.strftime('%d/%m/%Y')}. "
            "A data respeita o limite de 30 dias e o funcionamento da Farmácia Escola."
        )
    )

    db.add(novo_evento)
    db.flush()
    db.refresh(novo_evento)
    novo_evento._origem_automacao = "criado"
    return novo_evento


def gerar_alertas_renovacao_laudo(
    db: Session
):
    """Gera alerta de renovação no segundo mês anterior ao vencimento."""
    hoje = date.today()
    criados = 0
    atualizados = 0

    eventos = db.query(AgendaIntegrada).filter(
        AgendaIntegrada.data_fim_vigencia.isnot(None),
        AgendaIntegrada.renovado == False
    ).all()

    for evento in eventos:
        data_alerta = calcular_data_alerta_renovacao(evento.data_fim_vigencia)
        if hoje < data_alerta or hoje > evento.data_fim_vigencia:
            continue

        dias_para_vencimento = (evento.data_fim_vigencia - hoje).days
        novo_status = "renovacao_urgente" if 0 <= dias_para_vencimento <= 30 else "renovacao_recomendada"
        prioridade = "URGENTE" if novo_status == "renovacao_urgente" else "IMPORTANTE"

        alerta_existente = db.query(AgendaIntegrada).filter(
            AgendaIntegrada.servico_origem == "renovacao_laudo",
            AgendaIntegrada.paciente_nome == evento.paciente_nome,
            AgendaIntegrada.medicamento == evento.medicamento,
            AgendaIntegrada.data_fim_vigencia == evento.data_fim_vigencia,
            AgendaIntegrada.status.in_(["renovacao_recomendada", "renovacao_urgente"])
        ).first()

        if alerta_existente:
            if alerta_existente.status != novo_status or alerta_existente.prioridade != prioridade:
                alerta_existente.status = novo_status
                alerta_existente.prioridade = prioridade
                alerta_existente.data_status = datetime.utcnow()
                alerta_existente.usuario_status = "sistema"
                alerta_existente.atualizado_em = datetime.utcnow()
                atualizados += 1
            continue

        novo_alerta = AgendaIntegrada(
            evento_pai_id=evento.id,
            servico_origem="renovacao_laudo",
            tipo_evento="RENOVACAO",
            prioridade=prioridade,
            paciente_id=evento.paciente_id,
            paciente_nome=evento.paciente_nome,
            telefone=evento.telefone,
            medicamento_id=getattr(evento, "medicamento_id", None),
            medicamento=evento.medicamento,
            data_evento=data_alerta,
            data_inicio_vigencia=evento.data_inicio_vigencia,
            data_fim_vigencia=evento.data_fim_vigencia,
            situacao_laudo=evento.situacao_laudo,
            status=novo_status,
            data_status=datetime.utcnow(),
            usuario_status="sistema",
            notificar_whatsapp=True,
            observacoes=(
                "Alerta automático de renovação gerado no segundo mês anterior "
                f"ao vencimento do laudo ({evento.data_fim_vigencia.strftime('%d/%m/%Y')})."
            )
        )
        db.add(novo_alerta)
        criados += 1

    db.commit()
    return {
        "mensagem": "Verificação de renovação de laudos concluída.",
        "regra": "segundo_mês_anterior_ao_vencimento",
        "alertas_criados": criados,
        "alertas_atualizados": atualizados
    }


def gerar_alertas_risco_interrupcao(
    db: Session
):
    """Gera alerta urgente no segundo mês após vencimento sem renovação."""
    hoje = date.today()
    criados = 0

    eventos = db.query(AgendaIntegrada).filter(
        AgendaIntegrada.data_fim_vigencia.isnot(None),
        AgendaIntegrada.renovado == False
    ).all()

    for evento in eventos:
        data_risco = calcular_data_risco_pos_vencimento(evento.data_fim_vigencia)
        if hoje < data_risco:
            continue

        alerta_existente = db.query(AgendaIntegrada).filter(
            AgendaIntegrada.servico_origem == "renovacao_laudo",
            AgendaIntegrada.status == "risco_interrupcao_tratamento",
            AgendaIntegrada.paciente_nome == evento.paciente_nome,
            AgendaIntegrada.medicamento == evento.medicamento,
            AgendaIntegrada.data_fim_vigencia == evento.data_fim_vigencia
        ).first()

        if alerta_existente:
            continue

        alerta = AgendaIntegrada(
            evento_pai_id=evento.id,
            servico_origem="renovacao_laudo",
            tipo_evento="RENOVACAO",
            prioridade="URGENTE",
            paciente_id=evento.paciente_id,
            paciente_nome=evento.paciente_nome,
            telefone=evento.telefone,
            medicamento_id=getattr(evento, "medicamento_id", None),
            medicamento=evento.medicamento,
            data_evento=data_risco,
            data_inicio_vigencia=evento.data_inicio_vigencia,
            data_fim_vigencia=evento.data_fim_vigencia,
            situacao_laudo="risco_interrupcao_tratamento",
            status="risco_interrupcao_tratamento",
            data_status=datetime.utcnow(),
            usuario_status="sistema",
            notificar_whatsapp=True,
            observacoes=(
                "Alerta automático: segundo mês após vencimento do laudo sem renovação registrada."
            )
        )
        db.add(alerta)
        criados += 1

    db.commit()
    return {
        "mensagem": "Verificação de risco de interrupção concluída.",
        "regra": "segundo_mês_após_vencimento_sem_renovação",
        "alertas_criados": criados
    }


def gerar_notificacoes_agenda(
    db: Session
):
    hoje = date.today()
    amanha = hoje + timedelta(days=1)

    criadas = 0
    ignoradas = 0

    regras = [
        {
            "tipo": "dispensacao_amanha",
            "query": db.query(AgendaIntegrada).filter(
                AgendaIntegrada.servico_origem == "dispensacao",
                AgendaIntegrada.status == "agendado",
                AgendaIntegrada.data_evento == amanha
            ),
            "mensagem": lambda e: (
                f"Olá, {e.paciente_nome}. Lembramos que sua retirada de "
                f"{e.medicamento or 'medicamento'} na Farmácia Escola está "
                f"prevista para amanhã ({e.data_evento.strftime('%d/%m/%Y')})."
            ),
            "data_programada": amanha
        },
        {
            "tipo": "renovacao_urgente",
            "query": db.query(AgendaIntegrada).filter(
                AgendaIntegrada.status == "renovacao_urgente"
            ),
            "mensagem": lambda e: (
                f"Olá, {e.paciente_nome}. Seu laudo está próximo do vencimento "
                f"({e.data_fim_vigencia.strftime('%d/%m/%Y') if e.data_fim_vigencia else 'data não informada'}). "
                f"Procure a Farmácia Escola para orientações sobre a renovação."
            ),
            "data_programada": hoje
        },
        {
            "tipo": "renovacao_recomendada",
            "query": db.query(AgendaIntegrada).filter(
                AgendaIntegrada.status == "renovacao_recomendada"
            ),
            "mensagem": lambda e: (
                f"Olá, {e.paciente_nome}. Identificamos que seu laudo terá vencimento em breve "
                f"({e.data_fim_vigencia.strftime('%d/%m/%Y') if e.data_fim_vigencia else 'data não informada'}). "
                f"Recomendamos iniciar a renovação para evitar interrupção do tratamento."
            ),
            "data_programada": hoje
        },
        {
            "tipo": "risco_interrupcao_tratamento",
            "query": db.query(AgendaIntegrada).filter(
                AgendaIntegrada.status == "risco_interrupcao_tratamento"
            ),
            "mensagem": lambda e: (
                f"Olá, {e.paciente_nome}. Identificamos risco de interrupção do tratamento, "
                f"pois a vigência do laudo está encerrando ou foi encerrada. "
                f"Procure a Farmácia Escola para orientação."
            ),
            "data_programada": hoje
        },
    ]

    for regra in regras:
        eventos = regra["query"].all()

        for evento in eventos:
            existente = db.query(NotificacaoAgenda).filter(
                NotificacaoAgenda.agenda_id == evento.id,
                NotificacaoAgenda.tipo_notificacao == regra["tipo"],
                NotificacaoAgenda.status.in_(["pendente", "enviada"])
            ).first()

            if existente:
                ignoradas += 1
                continue

            notificacao = NotificacaoAgenda(
                agenda_id=evento.id,
                paciente_nome=evento.paciente_nome,
                telefone=evento.telefone,
                tipo_notificacao=regra["tipo"],
                mensagem=regra["mensagem"](evento),
                data_programada=regra["data_programada"],
                status="pendente"
            )

            db.add(notificacao)
            criadas += 1

    db.commit()

    return {
        "mensagem": "Geração de notificações concluída.",
        "notificacoes_criadas": criadas,
        "notificacoes_ignoradas": ignoradas
    }


