"""
Saneamento técnico - Pacote 1
Execute a partir da pasta backend:
    python saneamento_pacote1.py
ou informe o caminho:
    python saneamento_pacote1.py routers/consultorio.py

O script faz backup automático antes de alterar.
"""
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import re
import sys

path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("routers/consultorio.py")
if not path.exists():
    raise SystemExit(f"Arquivo não encontrado: {path.resolve()}")

text = path.read_text(encoding="utf-8")
backup = path.with_name(path.name + f".bak_saneamento_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
backup.write_text(text, encoding="utf-8")

changed = []

helper = r'''def obter_ou_criar_paciente_agenda(
    db: Session,
    nome: str,
    telefone: Optional[str] = None,
    cpf: Optional[str] = None,
    cns: Optional[str] = None,
    origem: str = "integracao"
):
    if not nome:
        return None

    nome = nome.strip()
    telefone = telefone.strip() if telefone else None
    cpf = cpf.strip() if cpf else None
    cns = cns.strip() if cns else None

    paciente = None

    if cpf:
        paciente = db.query(PacienteAgenda).filter(
            PacienteAgenda.cpf == cpf
        ).first()

    if not paciente and cns:
        paciente = db.query(PacienteAgenda).filter(
            PacienteAgenda.cns == cns
        ).first()

    if not paciente and telefone:
        paciente = db.query(PacienteAgenda).filter(
            PacienteAgenda.nome == nome,
            PacienteAgenda.telefone == telefone
        ).first()

    if not paciente:
        paciente = db.query(PacienteAgenda).filter(
            PacienteAgenda.nome == nome
        ).first()

    if paciente:
        if telefone and not paciente.telefone:
            paciente.telefone = telefone
        if cpf and not paciente.cpf:
            paciente.cpf = cpf
        if cns and not paciente.cns:
            paciente.cns = cns
        if not paciente.ativo:
            paciente.ativo = True

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

'''

if "def obter_ou_criar_paciente_agenda(" not in text:
    anchor = "def calcular_capacidade_agenda("
    if anchor in text:
        text = text.replace(anchor, helper + anchor, 1)
        changed.append("Inserida função obter_ou_criar_paciente_agenda")
    else:
        raise SystemExit("Não encontrei o ponto para inserir obter_ou_criar_paciente_agenda.")

clean_criar_proxima = r'''def criar_proxima_dispensacao_automatica(
    db: Session,
    agenda_atual: AgendaIntegrada
):
    servico_normalizado = (agenda_atual.servico_origem or "").strip().lower()

    if servico_normalizado not in ["dispensacao", "dispensação"]:
        return None

    if not agenda_atual.data_evento:
        return None

    proxima_data = agenda_atual.data_evento + timedelta(days=30)

    # Se a próxima retirada ultrapassa a vigência do laudo, não agenda nova dispensação.
    # Em vez disso, gera alerta assistencial de risco de interrupção.
    if (
        agenda_atual.data_fim_vigencia
        and proxima_data > agenda_atual.data_fim_vigencia
    ):
        alerta_existente = db.query(AgendaIntegrada).filter(
            AgendaIntegrada.evento_pai_id == agenda_atual.id,
            AgendaIntegrada.status == "risco_interrupcao_tratamento"
        ).first()

        if alerta_existente:
            alerta_existente._origem_automacao = "risco_interrupcao"
            return alerta_existente

        alerta = AgendaIntegrada(
            evento_pai_id=agenda_atual.id,
            servico_origem="renovacao_laudo",
            tipo_evento="risco_interrupcao_tratamento",
            paciente_id=agenda_atual.paciente_id,
            paciente_nome=agenda_atual.paciente_nome,
            telefone=agenda_atual.telefone,
            medicamento=agenda_atual.medicamento,
            data_evento=date.today(),
            data_inicio_vigencia=agenda_atual.data_inicio_vigencia,
            data_fim_vigencia=agenda_atual.data_fim_vigencia,
            situacao_laudo="risco_interrupcao_tratamento",
            status="risco_interrupcao_tratamento",
            data_status=datetime.utcnow(),
            usuario_status="sistema",
            notificar_whatsapp=True,
            observacoes=(
                "Nova dispensação automática não criada porque a vigência "
                "do laudo termina antes da próxima retirada prevista."
            )
        )

        db.add(alerta)
        db.flush()
        db.refresh(alerta)
        alerta._origem_automacao = "risco_interrupcao"
        return alerta

    query_existente = db.query(AgendaIntegrada).filter(
        AgendaIntegrada.id != agenda_atual.id,
        AgendaIntegrada.servico_origem.in_(["dispensacao", "dispensação"]),
        AgendaIntegrada.medicamento == agenda_atual.medicamento,
        AgendaIntegrada.status.in_(["agendado", "notificado", "reagendado"]),
        AgendaIntegrada.data_evento >= proxima_data
    )

    if agenda_atual.paciente_id:
        query_existente = query_existente.filter(
            AgendaIntegrada.paciente_id == agenda_atual.paciente_id
        )
    else:
        query_existente = query_existente.filter(
            AgendaIntegrada.paciente_nome == agenda_atual.paciente_nome
        )

    existe = query_existente.first()

    if existe:
        existe._origem_automacao = "existente"
        return existe

    capacidade = calcular_capacidade_agenda(
        db=db,
        servico_origem="dispensacao",
        data_evento=proxima_data
    )

    if capacidade["capacidade_atingida"]:
        for i in range(1, 15):
            data_teste = proxima_data + timedelta(days=i)

            capacidade_teste = calcular_capacidade_agenda(
                db=db,
                servico_origem="dispensacao",
                data_evento=data_teste
            )

            if (
                capacidade_teste["capacidade_configurada"]
                and not capacidade_teste["capacidade_atingida"]
            ):
                proxima_data = data_teste
                break

    novo_evento = AgendaIntegrada(
        evento_pai_id=agenda_atual.id,
        servico_origem="dispensacao",
        tipo_evento="retirada_medicamento",
        paciente_id=agenda_atual.paciente_id,
        paciente_nome=agenda_atual.paciente_nome,
        telefone=agenda_atual.telefone,
        medicamento=agenda_atual.medicamento,
        data_evento=proxima_data,
        data_inicio_vigencia=agenda_atual.data_inicio_vigencia,
        data_fim_vigencia=agenda_atual.data_fim_vigencia,
        situacao_laudo=agenda_atual.situacao_laudo,
        status="agendado",
        notificar_whatsapp=True,
        observacoes=(
            f"Agendamento automático gerado após retirada realizada "
            f"em {agenda_atual.data_evento.strftime('%d/%m/%Y')}"
        )
    )

    db.add(novo_evento)
    db.flush()
    db.refresh(novo_evento)
    novo_evento._origem_automacao = "criado"
    return novo_evento

'''

pattern = re.compile(r"def criar_proxima_dispensacao_automatica\(.*?(?=\ndef gerar_alertas_renovacao_laudo\()", re.S)
text2, n = pattern.subn(clean_criar_proxima, text, count=1)
if n:
    text = text2
    changed.append("Saneada função criar_proxima_dispensacao_automatica")
else:
    print("AVISO: não encontrei criar_proxima_dispensacao_automatica para substituir.")

clean_criar_agendamento = r'''@router.post("/agenda")
def criar_agendamento(
    dados: AgendaIntegradaCreate,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    alerta_capacidade = None

    if dados.data_evento and dados.data_evento < date.today():
        raise HTTPException(
            status_code=400,
            detail="Não é permitido criar agendamento em data passada."
        )

    if dados.data_evento:
        capacidade = calcular_capacidade_agenda(
            db=db,
            servico_origem=dados.servico_origem,
            data_evento=dados.data_evento
        )

        if capacidade["capacidade_atingida"]:
            alerta_capacidade = {
                "warning": True,
                "mensagem": "Capacidade diária atingida para este serviço e data.",
                "capacidade": capacidade
            }

    paciente_agenda = obter_ou_criar_paciente_agenda(
        db=db,
        nome=dados.paciente_nome,
        telefone=dados.telefone,
        origem="agenda_manual"
    )

    paciente_id = (
        dados.paciente_id
        or (paciente_agenda.id if paciente_agenda else None)
    )

    agenda = AgendaIntegrada(
        **dados.model_dump(exclude={"paciente_id"}),
        paciente_id=paciente_id
    )

    db.add(agenda)
    db.commit()
    db.refresh(agenda)

    return {
        "mensagem": "Agendamento criado com sucesso.",
        "agenda": agenda,
        "alerta_capacidade": alerta_capacidade
    }

'''

pattern = re.compile(r"@router\.post\(\"/agenda\"\)\ndef criar_agendamento\(.*?(?=\n@router\.get\(\"/agenda\"\))", re.S)
text2, n = pattern.subn(clean_criar_agendamento, text, count=1)
if n:
    text = text2
    changed.append("Saneada rota POST /agenda")
else:
    print("AVISO: não encontrei a rota POST /agenda para substituir.")

clean_status_notificacao = r'''@router.put("/agenda/notificacoes/{notificacao_id}/status")
def atualizar_status_notificacao_agenda(
    notificacao_id: int,
    dados: NotificacaoAgendaUpdate,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    notificacao = db.query(NotificacaoAgenda).filter(
        NotificacaoAgenda.id == notificacao_id
    ).first()

    if not notificacao:
        raise HTTPException(
            status_code=404,
            detail="Notificação não encontrada"
        )

    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(notificacao, campo, valor)

    if dados.status == "enviada" and not notificacao.data_envio:
        notificacao.data_envio = datetime.utcnow()
        notificacao.erro_envio = None

    if dados.status == "erro":
        notificacao.tentativa_envio = (notificacao.tentativa_envio or 0) + 1
        if not notificacao.erro_envio:
            notificacao.erro_envio = "Erro registrado manualmente."

    if dados.status == "pendente":
        notificacao.data_envio = None

    notificacao.usuario_atualizacao = (
        getattr(current, "nome", None)
        or getattr(current, "email", None)
        or "sistema"
    )

    notificacao.atualizado_em = datetime.utcnow()

    db.commit()
    db.refresh(notificacao)

    return {
        "mensagem": "Status da notificação atualizado.",
        "notificacao": notificacao
    }

'''

pattern = re.compile(r"@router\.put\(\"/agenda/notificacoes/\{notificacao_id\}/status\"\)\ndef atualizar_status_notificacao_agenda\(.*?(?=\n@router\.get\(\"/agenda/painel-pendencias\"\))", re.S)
text2, n = pattern.subn(clean_status_notificacao, text, count=1)
if n:
    text = text2
    changed.append("Saneada rota PUT /agenda/notificacoes/{id}/status")
else:
    print("AVISO: não encontrei a rota de status de notificação para substituir.")

path.write_text(text, encoding="utf-8")

print("Saneamento concluído.")
print(f"Backup criado em: {backup}")
print("Alterações:")
for item in changed:
    print(f"- {item}")
print("\nAgora rode:")
print("python -m py_compile routers/consultorio.py")
print("uvicorn main:app --reload")
