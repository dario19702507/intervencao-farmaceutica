"""
Pacote de Reorganizacao 4 - Notificacoes

Cria/atualiza routers/notificacoes.py e inclui o router no main.py.
Mantem as URLs atuais usadas pelo frontend:
- GET  /consultorio/agenda/notificacoes
- POST /consultorio/agenda/notificacoes/gerar
- GET  /consultorio/agenda/notificacoes/listar
- PUT  /consultorio/agenda/notificacoes/{notificacao_id}/status

Este pacote nao remove rotas antigas do consultorio.py. A limpeza vem depois da validacao.
"""

from pathlib import Path
from datetime import datetime
import shutil

BASE = Path.cwd()
ROUTERS = BASE / "routers"
BACKUP = BASE / f"backup_reorganizacao_pacote4_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def backup_file(path: Path):
    if path.exists():
        BACKUP.mkdir(exist_ok=True)
        destino = BACKUP / path.name
        shutil.copy2(path, destino)
        print(f"Backup criado: {destino}")


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def write_notificacoes_router():
    ensure_dir(ROUTERS)
    path = ROUTERS / "notificacoes.py"
    backup_file(path)

    content = '''from datetime import datetime, date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models.consultorio_models import (
    AgendaIntegrada,
    NotificacaoAgenda,
)
from schemas.consultorio_schemas import NotificacaoAgendaUpdate
from routers.utils_consultorio import (
    get_db_consultorio,
    get_current_user_consultorio,
    registrar_auditoria,
)

router = APIRouter(
    prefix="/consultorio/agenda/notificacoes",
    tags=["Notificações da Agenda"]
)


def gerar_notificacoes_agenda(db: Session):
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
                AgendaIntegrada.data_evento == amanha,
            ),
            "mensagem": lambda e: (
                f"Olá, {e.paciente_nome}. Lembramos que sua retirada de "
                f"{e.medicamento or 'medicamento'} na Farmácia Escola está "
                f"prevista para amanhã ({e.data_evento.strftime('%d/%m/%Y')})."
            ),
            "data_programada": amanha,
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
            "data_programada": hoje,
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
            "data_programada": hoje,
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
            "data_programada": hoje,
        },
    ]

    for regra in regras:
        eventos = regra["query"].all()

        for evento in eventos:
            existente = db.query(NotificacaoAgenda).filter(
                NotificacaoAgenda.agenda_id == evento.id,
                NotificacaoAgenda.tipo_notificacao == regra["tipo"],
                NotificacaoAgenda.status.in_(["pendente", "enviada"]),
            ).first()

            if existente:
                if not existente.paciente_id and evento.paciente_id:
                    existente.paciente_id = evento.paciente_id
                    existente.atualizado_em = datetime.utcnow()

                ignoradas += 1
                continue

            notificacao = NotificacaoAgenda(
                agenda_id=evento.id,
                paciente_id=evento.paciente_id,
                paciente_nome=evento.paciente_nome,
                telefone=evento.telefone,
                tipo_notificacao=regra["tipo"],
                mensagem=regra["mensagem"](evento),
                data_programada=regra["data_programada"],
                status="pendente",
                canal="interno",
            )

            db.add(notificacao)
            db.flush()
            db.refresh(notificacao)

            criadas += 1

    return {
        "mensagem": "Geração de notificações concluída.",
        "notificacoes_criadas": criadas,
        "notificacoes_ignoradas": ignoradas,
    }


@router.get("")
def buscar_notificacoes_agenda(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    hoje = date.today()
    amanha = hoje + timedelta(days=1)

    risco_interrupcao = db.query(AgendaIntegrada).filter(
        AgendaIntegrada.status == "risco_interrupcao_tratamento"
    ).all()

    renovacoes_urgentes = db.query(AgendaIntegrada).filter(
        AgendaIntegrada.status == "renovacao_urgente"
    ).all()

    renovacoes_recomendadas = db.query(AgendaIntegrada).filter(
        AgendaIntegrada.status == "renovacao_recomendada"
    ).all()

    dispensacoes_amanha = db.query(AgendaIntegrada).filter(
        AgendaIntegrada.servico_origem == "dispensacao",
        AgendaIntegrada.data_evento == amanha,
        AgendaIntegrada.status == "agendado",
    ).all()

    consultas_amanha = db.query(AgendaIntegrada).filter(
        AgendaIntegrada.servico_origem == "consultorio",
        AgendaIntegrada.data_evento == amanha,
        AgendaIntegrada.status == "agendado",
    ).all()

    return {
        "resumo": {
            "risco_interrupcao": len(risco_interrupcao),
            "renovacoes_urgentes": len(renovacoes_urgentes),
            "renovacoes_recomendadas": len(renovacoes_recomendadas),
            "dispensacoes_amanha": len(dispensacoes_amanha),
            "consultas_amanha": len(consultas_amanha),
        },
        "risco_interrupcao": risco_interrupcao,
        "renovacoes_urgentes": renovacoes_urgentes,
        "renovacoes_recomendadas": renovacoes_recomendadas,
        "dispensacoes_amanha": dispensacoes_amanha,
        "consultas_amanha": consultas_amanha,
    }


@router.post("/gerar")
def executar_geracao_notificacoes_agenda(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    resultado = gerar_notificacoes_agenda(db)

    registrar_auditoria(
        db=db,
        current=current,
        modulo="notificacoes",
        acao="geracao_automatica",
        registro_id=None,
        descricao=(
            f"Notificações criadas: {resultado.get('notificacoes_criadas', 0)}; "
            f"ignoradas: {resultado.get('notificacoes_ignoradas', 0)}"
        ),
    )

    db.commit()

    return resultado


@router.get("/listar")
def listar_notificacoes_agenda(
    status: Optional[str] = None,
    tipo_notificacao: Optional[str] = None,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    query = db.query(NotificacaoAgenda)

    if status:
        query = query.filter(NotificacaoAgenda.status == status)

    if tipo_notificacao:
        query = query.filter(
            NotificacaoAgenda.tipo_notificacao == tipo_notificacao
        )

    notificacoes = query.order_by(
        NotificacaoAgenda.data_programada.asc(),
        NotificacaoAgenda.criado_em.desc(),
    ).all()

    return {
        "total": len(notificacoes),
        "notificacoes": notificacoes,
    }


@router.put("/{notificacao_id}/status")
def atualizar_status_notificacao_agenda(
    notificacao_id: int,
    dados: NotificacaoAgendaUpdate,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    notificacao = db.query(NotificacaoAgenda).filter(
        NotificacaoAgenda.id == notificacao_id
    ).first()

    if not notificacao:
        raise HTTPException(
            status_code=404,
            detail="Notificação não encontrada",
        )

    status_anterior = notificacao.status

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

    registrar_auditoria(
        db=db,
        current=current,
        modulo="notificacoes",
        acao="alteracao_status",
        registro_id=notificacao.id,
        descricao=(
            f"Status da notificação alterado de "
            f"{status_anterior} para {notificacao.status} "
            f"para {notificacao.paciente_nome}"
        ),
    )

    db.commit()
    db.refresh(notificacao)

    return {
        "mensagem": "Status da notificação atualizado.",
        "notificacao": notificacao,
    }
'''
    path.write_text(content, encoding="utf-8")
    print(f"Arquivo criado/atualizado: {path}")


def update_main():
    path = BASE / "main.py"
    backup_file(path)
    text = path.read_text(encoding="utf-8")

    import_line = "from routers.notificacoes import router as notificacoes_router\n"
    if import_line not in text:
        marker = "from routers.consultorio import router as consultorio_router\n"
        if marker in text:
            text = text.replace(marker, marker + import_line)
        else:
            text = import_line + text

    include_line = "app.include_router(notificacoes_router)\n"
    if include_line not in text:
        marker = "app.include_router(consultorio_router)\n"
        if marker in text:
            text = text.replace(marker, marker + include_line)
        else:
            text += "\n" + include_line

    path.write_text(text, encoding="utf-8")
    print("main.py atualizado com notificacoes_router.")


def main():
    write_notificacoes_router()
    update_main()
    print("\nPacote 4 aplicado.")
    print("Agora execute:")
    print("python -m py_compile routers/notificacoes.py")
    print("python -m py_compile main.py")
    print("uvicorn main:app --reload")


if __name__ == "__main__":
    main()
