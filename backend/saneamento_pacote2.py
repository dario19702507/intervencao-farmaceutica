"""
Pacote 2 de saneamento estrutural - Projeto Farmácia Escola

Objetivo: aplicar correções de baixo/médio risco no backend antes de avançar
para novas funcionalidades:
1) limpar função de próxima dispensação automática;
2) corrigir atualização de status de notificações;
3) reposicionar create_all para depois dos modelos principais;
4) consolidar criação de agenda usando paciente mestre;
5) criar índices úteis no SQLite.

Como usar:
- Copie este arquivo para a pasta backend.
- Execute: python saneamento_pacote2.py
- Depois: python -m py_compile routers/consultorio.py
- Depois: uvicorn main:app --reload
"""
from __future__ import annotations

import os
import re
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

BACKEND_DIR = Path.cwd()
CONSULTORIO_PATH = BACKEND_DIR / "routers" / "consultorio.py"
DB_PATH = BACKEND_DIR / "intervencoes.db"


def backup_file(path: Path) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = path.with_suffix(path.suffix + f".backup_pacote2_{ts}")
    shutil.copy2(path, backup)
    return backup


def replace_block(text: str, start_pattern: str, end_pattern: str, replacement: str) -> tuple[str, bool]:
    start = re.search(start_pattern, text, flags=re.MULTILINE)
    if not start:
        return text, False
    end = re.search(end_pattern, text[start.start():], flags=re.MULTILINE)
    if not end:
        return text, False
    end_abs = start.start() + end.start()
    return text[:start.start()] + replacement.rstrip() + "\n\n" + text[end_abs:], True


CLEAN_CRIAR_PROXIMA = r'''
def criar_proxima_dispensacao_automatica(
    db: Session,
    agenda_atual: AgendaIntegrada
):
    """Cria próxima dispensação em 30 dias, ou alerta de risco se a vigência não permitir.

    Regra operacional:
    - só se aplica a dispensação marcada como realizada;
    - não cria duplicidade futura para mesmo paciente/medicamento;
    - se a próxima retirada extrapola a vigência do laudo, cria alerta de risco;
    - respeita capacidade diária quando houver configuração.
    """
    servico_normalizado = (agenda_atual.servico_origem or "").strip().lower()

    if servico_normalizado not in ["dispensacao", "dispensação"]:
        return None

    if not agenda_atual.data_evento:
        return None

    proxima_data = agenda_atual.data_evento + timedelta(days=30)

    # Não agenda nova retirada fora da vigência do laudo.
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

    # Evita duplicidade: prioriza paciente_id quando existir; usa nome/telefone como fallback.
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
            AgendaIntegrada.paciente_nome == agenda_atual.paciente_nome,
            AgendaIntegrada.telefone == agenda_atual.telefone
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


CLEAN_ATUALIZAR_NOTIFICACAO = r'''
@router.put("/agenda/notificacoes/{notificacao_id}/status")
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


HELPER_OBTER_PACIENTE = r'''
def obter_ou_criar_paciente_agenda(
    db: Session,
    nome: str,
    telefone: Optional[str] = None,
    cpf: Optional[str] = None,
    cns: Optional[str] = None,
    origem: str = "integracao"
):
    """Obtém ou cria o cadastro mestre do paciente.

    Ordem de identificação: CPF, CNS, nome+telefone e, por fim, nome.
    Atualiza campos vazios quando uma informação nova chega de outro módulo.
    """
    nome = (nome or "").strip()
    telefone = (telefone or "").strip() or None
    cpf = (cpf or "").strip() or None
    cns = (cns or "").strip() or None

    if not nome:
        return None

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


CLEAN_CRIAR_AGENDAMENTO = r'''
@router.post("/agenda")
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

    paciente_agenda = None

    if dados.paciente_id:
        paciente_agenda = db.query(PacienteAgenda).filter(
            PacienteAgenda.id == dados.paciente_id
        ).first()

    if not paciente_agenda:
        paciente_agenda = obter_ou_criar_paciente_agenda(
            db=db,
            nome=dados.paciente_nome,
            telefone=dados.telefone,
            origem="agenda_manual"
        )

    paciente_id = paciente_agenda.id if paciente_agenda else dados.paciente_id

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


def ensure_create_all_position(text: str) -> tuple[str, bool]:
    # Remove todas as chamadas soltas para evitar create_all antes de modelos tardios.
    new_text, count = re.subn(r"^BaseConsultorio\.metadata\.create_all\(bind=engine\)\s*\n", "", text, flags=re.MULTILINE)
    if "class AgendaIntegradaCreate(BaseModel):" in new_text:
        new_text = new_text.replace(
            "class AgendaIntegradaCreate(BaseModel):",
            "BaseConsultorio.metadata.create_all(bind=engine)\n\nclass AgendaIntegradaCreate(BaseModel):",
            1,
        )
        return new_text, count > 0
    return text, False


def ensure_helper(text: str) -> tuple[str, bool]:
    if "def obter_ou_criar_paciente_agenda(" in text:
        return text, False
    marker = "def calcular_capacidade_agenda("
    if marker not in text:
        return text, False
    return text.replace(marker, HELPER_OBTER_PACIENTE.rstrip() + "\n\n" + marker, 1), True


def create_indexes() -> None:
    if not DB_PATH.exists():
        print(f"[AVISO] Banco SQLite não encontrado em {DB_PATH}. Índices não foram aplicados.")
        return

    sql = [
        "CREATE INDEX IF NOT EXISTS idx_agenda_paciente_id ON agenda_integrada (paciente_id);",
        "CREATE INDEX IF NOT EXISTS idx_agenda_status_data ON agenda_integrada (status, data_evento);",
        "CREATE INDEX IF NOT EXISTS idx_agenda_servico_data ON agenda_integrada (servico_origem, data_evento);",
        "CREATE INDEX IF NOT EXISTS idx_notificacao_status ON notificacoes_agenda (status);",
        "CREATE INDEX IF NOT EXISTS idx_notificacao_data ON notificacoes_agenda (data_programada);",
        "CREATE INDEX IF NOT EXISTS idx_notificacao_agenda_id ON notificacoes_agenda (agenda_id);",
        "CREATE INDEX IF NOT EXISTS idx_paciente_agenda_nome ON pacientes_agenda (nome);",
        "CREATE INDEX IF NOT EXISTS idx_paciente_agenda_telefone ON pacientes_agenda (telefone);",
        "CREATE INDEX IF NOT EXISTS idx_paciente_simplificado_agenda_id ON pacientes_simplificados (paciente_agenda_id);",
        "CREATE INDEX IF NOT EXISTS idx_paciente_clinico_agenda_id ON pacientes_clinicos (paciente_agenda_id);",
    ]

    conn = sqlite3.connect(DB_PATH)
    try:
        for stmt in sql:
            try:
                conn.execute(stmt)
            except sqlite3.OperationalError as exc:
                print(f"[AVISO] Índice não aplicado: {stmt} -> {exc}")
        conn.commit()
        print("[OK] Índices aplicados/verificados no SQLite.")
    finally:
        conn.close()


def main() -> None:
    if not CONSULTORIO_PATH.exists():
        raise SystemExit(f"Arquivo não encontrado: {CONSULTORIO_PATH}")

    backup = backup_file(CONSULTORIO_PATH)
    print(f"[OK] Backup criado: {backup.name}")

    text = CONSULTORIO_PATH.read_text(encoding="utf-8")
    changes: list[str] = []

    text, changed = ensure_create_all_position(text)
    if changed:
        changes.append("create_all reposicionado após AgendaIntegrada")

    text, changed = ensure_helper(text)
    if changed:
        changes.append("helper obter_ou_criar_paciente_agenda adicionado")

    text, changed = replace_block(
        text,
        r"^def criar_proxima_dispensacao_automatica\(",
        r"^def gerar_alertas_renovacao_laudo\(",
        CLEAN_CRIAR_PROXIMA,
    )
    if changed:
        changes.append("criar_proxima_dispensacao_automatica saneada")
    else:
        print("[AVISO] Função criar_proxima_dispensacao_automatica não foi localizada para substituição.")

    text, changed = replace_block(
        text,
        r"^@router\.post\(\"/agenda\"\)",
        r"^@router\.get\(\"/agenda\"\)",
        CLEAN_CRIAR_AGENDAMENTO,
    )
    if changed:
        changes.append("POST /agenda consolidado com paciente mestre")
    else:
        print("[AVISO] Rota POST /agenda não foi localizada para substituição.")

    text, changed = replace_block(
        text,
        r"^@router\.put\(\"/agenda/notificacoes/\{notificacao_id\}/status\"\)",
        r"^@router\.get\(\"/agenda/painel-pendencias\"\)",
        CLEAN_ATUALIZAR_NOTIFICACAO,
    )
    if changed:
        changes.append("PUT status de notificações saneado")
    else:
        print("[AVISO] Rota de atualização de notificação não foi localizada para substituição.")

    CONSULTORIO_PATH.write_text(text, encoding="utf-8")
    create_indexes()

    print("\nAlterações aplicadas:")
    for item in changes:
        print(f"- {item}")

    print("\nPróximos comandos:")
    print("python -m py_compile routers/consultorio.py")
    print("uvicorn main:app --reload")
    print("\nTestes sugeridos:")
    print("1. Criar evento na agenda com paciente já existente.")
    print("2. Criar evento na agenda com paciente novo.")
    print("3. Marcar dispensação como realizado.")
    print("4. Alterar notificação para enviada, erro, pendente.")
    print("5. Abrir Pacientes > Histórico.")


if __name__ == "__main__":
    main()
