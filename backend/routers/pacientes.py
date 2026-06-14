from datetime import datetime, date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from routers.consultorio import (
    get_db_consultorio,
    get_current_user_consultorio,
    PacienteAgenda,
    AgendaIntegrada,
    PacienteSimplificado,
    PacienteClinico,
    NotificacaoAgenda,
    PacienteAgendaCreate,
    PacienteAgendaUpdate,
    registrar_auditoria,
    obter_ou_criar_paciente_agenda,
)

router = APIRouter(
    prefix="/consultorio",
    tags=["Pacientes - Cadastro Mestre"]
)


@router.get("/pacientes")
def listar_pacientes_mestre(
    termo: Optional[str] = None,
    ativo: Optional[bool] = True,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    query = db.query(PacienteAgenda)

    if ativo is not None:
        query = query.filter(PacienteAgenda.ativo == ativo)

    if termo:
        termo_like = f"%{termo.strip()}%"

        query = query.filter(
            PacienteAgenda.nome.ilike(termo_like)
            | PacienteAgenda.cpf.ilike(termo_like)
            | PacienteAgenda.cns.ilike(termo_like)
            | PacienteAgenda.telefone.ilike(termo_like)
        )

    pacientes = query.order_by(
        PacienteAgenda.nome.asc()
    ).limit(300).all()

    return {
        "total": len(pacientes),
        "pacientes": pacientes
    }


@router.get("/pacientes/{paciente_id}")
def obter_paciente_mestre(
    paciente_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    paciente = db.query(PacienteAgenda).filter(
        PacienteAgenda.id == paciente_id
    ).first()

    if not paciente:
        raise HTTPException(
            status_code=404,
            detail="Paciente não encontrado."
        )

    return {
        "paciente": paciente
    }


@router.put("/pacientes/{paciente_id}")
def atualizar_paciente_mestre(
    paciente_id: int,
    dados: PacienteAgendaUpdate,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    paciente = db.query(PacienteAgenda).filter(
        PacienteAgenda.id == paciente_id
    ).first()

    if not paciente:
        raise HTTPException(
            status_code=404,
            detail="Paciente não encontrado."
        )

    dados_atualizados = dados.model_dump(exclude_unset=True)

    for campo, valor in dados_atualizados.items():
        setattr(paciente, campo, valor)

    paciente.atualizado_em = datetime.utcnow()

    if "nome" in dados_atualizados or "telefone" in dados_atualizados:
        novo_nome = dados_atualizados.get("nome", paciente.nome)
        novo_telefone = dados_atualizados.get("telefone", paciente.telefone)

        db.query(AgendaIntegrada).filter(
            AgendaIntegrada.paciente_id == paciente_id
        ).update(
            {
                AgendaIntegrada.paciente_nome: novo_nome,
                AgendaIntegrada.telefone: novo_telefone,
                AgendaIntegrada.atualizado_em: datetime.utcnow(),
            },
            synchronize_session=False
        )

        db.query(NotificacaoAgenda).filter(
            NotificacaoAgenda.paciente_id == paciente_id
        ).update(
            {
                NotificacaoAgenda.paciente_nome: novo_nome,
                NotificacaoAgenda.telefone: novo_telefone,
                NotificacaoAgenda.atualizado_em: datetime.utcnow(),
            },
            synchronize_session=False
        )

    registrar_auditoria(
        db=db,
        current=current,
        modulo="pacientes",
        acao="atualizacao",
        registro_id=paciente_id,
        descricao=f"Paciente atualizado: {paciente.nome}"
    )

    db.commit()
    db.refresh(paciente)

    return {
        "mensagem": "Paciente atualizado com sucesso.",
        "paciente": paciente
    }


def _ordenar_data_timeline(item):
    data = item.get("data")

    if isinstance(data, str):
        try:
            return datetime.strptime(data, "%Y-%m-%d")
        except Exception:
            return datetime.min

    if isinstance(data, datetime):
        return data

    if isinstance(data, date):
        return datetime.combine(data, datetime.min.time())

    return datetime.min


@router.get("/pacientes/{paciente_id}/historico")
def historico_paciente_mestre(
    paciente_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    paciente = db.query(PacienteAgenda).filter(
        PacienteAgenda.id == paciente_id
    ).first()

    if not paciente:
        raise HTTPException(
            status_code=404,
            detail="Paciente não encontrado."
        )

    agenda = db.query(AgendaIntegrada).filter(
        AgendaIntegrada.paciente_id == paciente_id
    ).order_by(
        AgendaIntegrada.data_evento.desc(),
        AgendaIntegrada.id.desc()
    ).all()

    simplificados = db.query(PacienteSimplificado).filter(
        PacienteSimplificado.paciente_agenda_id == paciente_id
    ).order_by(
        PacienteSimplificado.criado_em.desc()
    ).all()

    clinicos = db.query(PacienteClinico).filter(
        PacienteClinico.paciente_agenda_id == paciente_id
    ).order_by(
        PacienteClinico.criado_em.desc()
    ).all()

    notificacoes = db.query(NotificacaoAgenda).filter(
        NotificacaoAgenda.paciente_id == paciente_id
    ).order_by(
        NotificacaoAgenda.criado_em.desc()
    ).all()

    notificacoes_pendentes = sum(1 for n in notificacoes if n.status == "pendente")
    notificacoes_enviadas = sum(1 for n in notificacoes if n.status == "enviada")
    notificacoes_erro = sum(1 for n in notificacoes if n.status == "erro")

    timeline = []

    for evento in agenda:
        timeline.append({
            "data": evento.data_evento,
            "origem": "agenda",
            "tipo": evento.tipo_evento,
            "titulo": evento.servico_origem,
            "descricao": evento.medicamento or evento.observacoes or "",
            "status": evento.status,
        })

    for item in simplificados:
        timeline.append({
            "data": item.criado_em,
            "origem": "atendimento_rapido",
            "tipo": "cadastro_simplificado",
            "titulo": "Cadastro em atendimento rápido",
            "descricao": item.bairro or "",
            "status": "registrado",
        })

    for item in clinicos:
        timeline.append({
            "data": item.criado_em,
            "origem": "consultorio_clinico",
            "tipo": "cadastro_clinico",
            "titulo": "Cadastro clínico",
            "descricao": item.origem or "",
            "status": "registrado",
        })

    for n in notificacoes:
        timeline.append({
            "data": n.criado_em,
            "origem": "notificacao",
            "tipo": n.tipo_notificacao,
            "titulo": "Notificação",
            "descricao": n.mensagem,
            "status": n.status,
        })

    timeline = sorted(
        timeline,
        key=_ordenar_data_timeline,
        reverse=True
    )

    dispensacoes = [
        e for e in agenda
        if e.servico_origem == "dispensacao"
    ]

    ultima_dispensacao = next(
        (
            e for e in sorted(
                dispensacoes,
                key=lambda x: x.data_evento or date.min,
                reverse=True
            )
            if e.status == "realizado"
        ),
        None
    )

    proxima_dispensacao = next(
        (
            e for e in sorted(
                dispensacoes,
                key=lambda x: x.data_evento or date.max
            )
            if e.status in ["agendado", "notificado", "reagendado"]
            and e.data_evento >= date.today()
        ),
        None
    )

    laudos = [
        e for e in agenda
        if e.data_fim_vigencia is not None
    ]

    laudo_mais_recente = next(
        (
            e for e in sorted(
                laudos,
                key=lambda x: x.data_fim_vigencia or date.min,
                reverse=True
            )
        ),
        None
    )

    ultima_notificacao = next(
        (
            n for n in sorted(
                notificacoes,
                key=lambda x: x.criado_em or datetime.min,
                reverse=True
            )
        ),
        None
    )

    painel_paciente = {
        "ultima_dispensacao": ultima_dispensacao,
        "proxima_dispensacao": proxima_dispensacao,
        "laudo_mais_recente": laudo_mais_recente,
        "ultima_notificacao": ultima_notificacao,
        "total_atendimentos_rapidos": len(simplificados),
        "total_cadastros_clinicos": len(clinicos),
        "total_eventos_agenda": len(agenda),
        "total_notificacoes": len(notificacoes),
    }

    status_paciente = {
        "cor": "green",
        "descricao": "Regular"
    }

    hoje = date.today()

    if laudo_mais_recente and laudo_mais_recente.data_fim_vigencia:
        dias_para_vencer = (
            laudo_mais_recente.data_fim_vigencia - hoje
        ).days

        if dias_para_vencer <= 30:
            status_paciente = {
                "cor": "red",
                "descricao": "Risco de interrupção do tratamento"
            }

        elif dias_para_vencer <= 60:
            status_paciente = {
                "cor": "yellow",
                "descricao": "Renovação próxima"
            }

    dispensacao_atrasada = any(
        e.status == "agendado"
        and e.data_evento
        and e.data_evento < hoje
        for e in agenda
    )

    if dispensacao_atrasada:
        status_paciente = {
            "cor": "orange",
            "descricao": "Dispensação atrasada"
        }

    painel_paciente["status_paciente"] = status_paciente

    return {
        "paciente": paciente,
        "resumo": {
            "total_eventos_agenda": len(agenda),
            "total_cadastros_simplificados": len(simplificados),
            "total_cadastros_clinicos": len(clinicos),
            "total_notificacoes": len(notificacoes),
            "notificacoes_pendentes": notificacoes_pendentes,
            "notificacoes_enviadas": notificacoes_enviadas,
            "notificacoes_erro": notificacoes_erro,
        },
        "painel_paciente": painel_paciente,
        "agenda": agenda,
        "pacientes_simplificados": simplificados,
        "pacientes_clinicos": clinicos,
        "notificacoes": notificacoes,
        "timeline": timeline,
    }


# Rotas mantidas por compatibilidade com AgendaIntegrada.jsx
def criar_paciente_agenda(
    dados: PacienteAgendaCreate,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    existente = None

    if dados.cpf:
        existente = db.query(PacienteAgenda).filter(
            PacienteAgenda.cpf == dados.cpf
        ).first()

    if not existente and dados.cns:
        existente = db.query(PacienteAgenda).filter(
            PacienteAgenda.cns == dados.cns
        ).first()

    if existente:
        raise HTTPException(
            status_code=409,
            detail="Paciente já cadastrado na agenda."
        )

    paciente = PacienteAgenda(
        **dados.model_dump(),
        ativo=True
    )

    db.add(paciente)
    db.flush()
    db.refresh(paciente)

    registrar_auditoria(
        db=db,
        current=current,
        modulo="pacientes",
        acao="criacao",
        registro_id=paciente.id,
        descricao=f"Paciente cadastrado: {paciente.nome}"
    )

    db.commit()
    db.refresh(paciente)

    return {
        "mensagem": "Paciente cadastrado com sucesso.",
        "paciente": paciente
    }


def listar_pacientes_agenda(
    ativo: Optional[bool] = True,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    query = db.query(PacienteAgenda)

    if ativo is not None:
        query = query.filter(PacienteAgenda.ativo == ativo)

    pacientes = query.order_by(
        PacienteAgenda.nome.asc()
    ).limit(200).all()

    return {
        "total": len(pacientes),
        "pacientes": pacientes
    }


def buscar_pacientes_agenda(
    termo: str,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    termo = (termo or "").strip()

    if len(termo) < 3:
        return {
            "total": 0,
            "pacientes": []
        }

    termo_like = f"%{termo}%"

    pacientes = db.query(PacienteAgenda).filter(
        PacienteAgenda.ativo != False,
        (
            PacienteAgenda.nome.ilike(termo_like)
            | PacienteAgenda.cpf.ilike(termo_like)
            | PacienteAgenda.cns.ilike(termo_like)
            | PacienteAgenda.telefone.ilike(termo_like)
        )
    ).order_by(
        PacienteAgenda.nome.asc()
    ).limit(50).all()

    return {
        "total": len(pacientes),
        "pacientes": pacientes
    }


def atualizar_paciente_agenda(
    paciente_id: int,
    dados: PacienteAgendaUpdate,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    return atualizar_paciente_mestre(
        paciente_id=paciente_id,
        dados=dados,
        db=db,
        current=current
    )
