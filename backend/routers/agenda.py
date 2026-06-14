"""Módulo Agenda Integrada e Catálogo de Medicamentos.

Passo 10A: consolida o catálogo padrão de medicamentos/apresentações e
prepara a Agenda para vincular eventos a um medicamento padronizado.
"""

from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from database import engine
from models.consultorio_models import (
    BaseConsultorio,
    AgendaIntegrada,
    CatalogoMedicamento,
)
from schemas.consultorio_schemas import (
    CatalogoMedicamentoCreate,
    CatalogoMedicamentoUpdate,
)
from services.agenda_inteligente import configuracao_atendimento_farmacia_escola
from routers.consultorio import (
    get_db_consultorio,
    get_current_user_consultorio,
    exigir_farmaceutico_ou_admin,
)

BaseConsultorio.metadata.create_all(bind=engine)


def _adicionar_coluna_agenda_se_nao_existir(tabela: str, definicao_coluna: str) -> None:
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql(f"ALTER TABLE {tabela} ADD COLUMN {definicao_coluna}")
            conn.commit()
    except Exception:
        # Coluna já existente ou banco sem suporte ao ALTER simples.
        # Mantém compatibilidade com o estágio atual do projeto.
        pass


_adicionar_coluna_agenda_se_nao_existir("agenda_integrada", "medicamento_id INTEGER")
_adicionar_coluna_agenda_se_nao_existir("agenda_integrada", "prioridade VARCHAR DEFAULT 'NORMAL'")
_adicionar_coluna_agenda_se_nao_existir("agenda_integrada", "titulo VARCHAR")

router = APIRouter(
    prefix="/consultorio",
    tags=["Agenda e Medicamentos"]
)

TIPOS_EVENTO_AGENDA = ["INCLUSAO", "RETIRADA", "RENOVACAO", "ADEQUACAO", "ENCERRAMENTO"]
PRIORIDADES_AGENDA = ["NORMAL", "IMPORTANTE", "URGENTE"]
STATUS_AGENDA = ["AGENDADO", "REALIZADO", "ATRASADO", "CANCELADO"]
FREQUENCIAS_DISPENSACAO = ["MENSAL", "BIMESTRAL", "TRIMESTRAL", "SEMESTRAL", "ANUAL"]


def _descricao_medicamento(medicamento: CatalogoMedicamento) -> str:
    partes = [
        medicamento.farmaco,
        medicamento.apresentacao,
        medicamento.concentracao,
        medicamento.forma_farmaceutica,
    ]
    return " - ".join([str(p) for p in partes if p])


def _normalizar_status(status: Optional[str]) -> Optional[str]:
    return status.upper() if status else status


@router.get("/agenda/opcoes")
def opcoes_agenda(current=Depends(get_current_user_consultorio)):
    return {
        "tipos_evento": TIPOS_EVENTO_AGENDA,
        "prioridades": PRIORIDADES_AGENDA,
        "status": STATUS_AGENDA,
        "frequencias_dispensacao": FREQUENCIAS_DISPENSACAO,
        "atendimento_farmacia_escola": configuracao_atendimento_farmacia_escola(),
    }


@router.get("/catalogo-medicamentos")
def listar_catalogo_medicamentos(
    busca: Optional[str] = None,
    ativo: Optional[bool] = True,
    componente: Optional[str] = None,
    limite: int = 100,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    query = db.query(CatalogoMedicamento)

    if ativo is not None:
        query = query.filter(CatalogoMedicamento.ativo == ativo)

    if componente:
        query = query.filter(CatalogoMedicamento.componente == componente)

    if busca:
        termo = f"%{busca}%"
        query = query.filter(
            or_(
                CatalogoMedicamento.farmaco.ilike(termo),
                CatalogoMedicamento.principio_ativo.ilike(termo),
                CatalogoMedicamento.nome_comercial.ilike(termo),
                CatalogoMedicamento.apresentacao.ilike(termo),
                CatalogoMedicamento.concentracao.ilike(termo),
                CatalogoMedicamento.registro_anvisa.ilike(termo),
                CatalogoMedicamento.classe_terapeutica.ilike(termo),
            )
        )

    medicamentos = query.order_by(
        CatalogoMedicamento.farmaco.asc(),
        CatalogoMedicamento.apresentacao.asc(),
    ).limit(max(1, min(limite, 500))).all()

    return {
        "total": len(medicamentos),
        "medicamentos": [
            {
                "id": m.id,
                "farmaco": m.farmaco,
                "principio_ativo": m.principio_ativo or m.farmaco,
                "nome_comercial": m.nome_comercial,
                "apresentacao": m.apresentacao,
                "concentracao": m.concentracao,
                "forma_farmaceutica": m.forma_farmaceutica,
                "laboratorio": m.laboratorio,
                "registro_anvisa": m.registro_anvisa,
                "classe_terapeutica": m.classe_terapeutica,
                "componente": m.componente,
                "frequencia_dispensacao": m.frequencia_dispensacao,
                "ativo": m.ativo,
                "observacoes": m.observacoes,
                "descricao_completa": _descricao_medicamento(m),
            }
            for m in medicamentos
        ]
    }


@router.post("/catalogo-medicamentos")
def criar_medicamento_catalogo(
    dados: CatalogoMedicamentoCreate,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    exigir_farmaceutico_ou_admin(current)

    medicamento_existente = db.query(CatalogoMedicamento).filter(
        func.lower(CatalogoMedicamento.farmaco) == dados.farmaco.strip().lower(),
        func.lower(CatalogoMedicamento.apresentacao) == dados.apresentacao.strip().lower(),
    ).first()

    if medicamento_existente:
        raise HTTPException(status_code=400, detail="Medicamento/apresentação já cadastrado no catálogo")

    novo = CatalogoMedicamento(
        farmaco=dados.farmaco.strip(),
        principio_ativo=(dados.principio_ativo or dados.farmaco).strip() if (dados.principio_ativo or dados.farmaco) else None,
        nome_comercial=(dados.nome_comercial.strip() if dados.nome_comercial else None),
        apresentacao=dados.apresentacao.strip(),
        concentracao=(dados.concentracao or None),
        forma_farmaceutica=(dados.forma_farmaceutica or None),
        laboratorio=(dados.laboratorio or None),
        registro_anvisa=(dados.registro_anvisa or None),
        classe_terapeutica=(dados.classe_terapeutica or None),
        componente=(dados.componente or None),
        frequencia_dispensacao=(dados.frequencia_dispensacao or None),
        observacoes=dados.observacoes,
        ativo=True,
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return {"mensagem": "Medicamento cadastrado com sucesso", "medicamento": novo}


@router.get("/catalogo-medicamentos/{medicamento_id}")
def obter_medicamento_catalogo(
    medicamento_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    medicamento = db.query(CatalogoMedicamento).filter(CatalogoMedicamento.id == medicamento_id).first()
    if not medicamento:
        raise HTTPException(status_code=404, detail="Medicamento não encontrado")
    return medicamento


@router.put("/catalogo-medicamentos/{medicamento_id}")
def atualizar_medicamento_catalogo(
    medicamento_id: int,
    dados: CatalogoMedicamentoUpdate,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    exigir_farmaceutico_ou_admin(current)

    medicamento = db.query(CatalogoMedicamento).filter(CatalogoMedicamento.id == medicamento_id).first()
    if not medicamento:
        raise HTTPException(status_code=404, detail="Medicamento não encontrado")

    for campo, valor in dados.model_dump(exclude_unset=True).items():
        if isinstance(valor, str):
            valor = valor.strip() or None
        setattr(medicamento, campo, valor)

    medicamento.atualizado_em = datetime.utcnow()
    db.commit()
    db.refresh(medicamento)
    return {"mensagem": "Medicamento atualizado com sucesso", "medicamento": medicamento}


@router.delete("/catalogo-medicamentos/{medicamento_id}")
def inativar_medicamento_catalogo(
    medicamento_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    exigir_farmaceutico_ou_admin(current)

    medicamento = db.query(CatalogoMedicamento).filter(CatalogoMedicamento.id == medicamento_id).first()
    if not medicamento:
        raise HTTPException(status_code=404, detail="Medicamento não encontrado")

    medicamento.ativo = False
    medicamento.atualizado_em = datetime.utcnow()
    db.commit()
    db.refresh(medicamento)
    return {"mensagem": "Medicamento inativado com sucesso", "medicamento": medicamento}


@router.post("/catalogo-medicamentos/seed")
def seed_catalogo_medicamentos(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    exigir_farmaceutico_ou_admin(current)

    padrao = [
        {"farmaco": "Dupilumabe", "apresentacao": "Seringa preenchida", "concentracao": "300 mg/2 mL", "forma_farmaceutica": "Solução injetável", "componente": "CEAF", "frequencia_dispensacao": "MENSAL"},
        {"farmaco": "Mepolizumabe", "apresentacao": "Frasco-ampola", "concentracao": "100 mg", "forma_farmaceutica": "Pó para solução injetável", "componente": "CEAF", "frequencia_dispensacao": "MENSAL"},
        {"farmaco": "Benralizumabe", "apresentacao": "Seringa preenchida", "concentracao": "30 mg/mL", "forma_farmaceutica": "Solução injetável", "componente": "CEAF", "frequencia_dispensacao": "MENSAL"},
        {"farmaco": "Budesonida + Formoterol", "apresentacao": "Cápsula inalante", "concentracao": "400 mcg + 12 mcg", "forma_farmaceutica": "Pó inalante", "componente": "CEAF", "frequencia_dispensacao": "MENSAL"},
        {"farmaco": "Tiotrópio", "apresentacao": "Cápsula inalante", "concentracao": "18 mcg", "forma_farmaceutica": "Pó inalante", "componente": "CEAF", "frequencia_dispensacao": "MENSAL"},
    ]

    criados = 0
    existentes = 0
    for item in padrao:
        existe = db.query(CatalogoMedicamento).filter(
            func.lower(CatalogoMedicamento.farmaco) == item["farmaco"].lower(),
            func.lower(CatalogoMedicamento.apresentacao) == item["apresentacao"].lower(),
        ).first()
        if existe:
            existentes += 1
            continue
        db.add(CatalogoMedicamento(**item, ativo=True))
        criados += 1

    db.commit()
    return {"mensagem": "Catálogo padrão processado", "criados": criados, "existentes": existentes}


@router.get("/agenda/dashboard")
def dashboard_agenda(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    hoje = date.today()
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    fim_semana = inicio_semana + timedelta(days=6)
    inicio_mes = hoje.replace(day=1)

    eventos_hoje = db.query(AgendaIntegrada).filter(AgendaIntegrada.data_evento == hoje).count()
    eventos_semana = db.query(AgendaIntegrada).filter(AgendaIntegrada.data_evento >= inicio_semana, AgendaIntegrada.data_evento <= fim_semana).count()
    eventos_mes = db.query(AgendaIntegrada).filter(AgendaIntegrada.data_evento >= inicio_mes).count()
    atrasados = db.query(AgendaIntegrada).filter(AgendaIntegrada.data_evento < hoje, AgendaIntegrada.status.in_(["agendado", "notificado", "reagendado", "AGENDADO"])).count()
    urgentes = db.query(AgendaIntegrada).filter(AgendaIntegrada.prioridade == "URGENTE").count()

    por_tipo = dict(
        db.query(AgendaIntegrada.tipo_evento, func.count(AgendaIntegrada.id))
        .group_by(AgendaIntegrada.tipo_evento)
        .all()
    )

    return {
        "eventos_hoje": eventos_hoje,
        "eventos_semana": eventos_semana,
        "eventos_mes": eventos_mes,
        "eventos_atrasados": atrasados,
        "eventos_urgentes": urgentes,
        "por_tipo_evento": por_tipo,
    }
