from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, time
from sqlalchemy.orm import Session

from database import engine

from models.consultorio_models import (
    BaseConsultorio,
    PacienteClinico,
    MedicamentoUso,
    CatalogoMedicamento,
    IntervencaoFarmacoterapia,
    DesfechoIntervencaoFarmacoterapia,
    UserConsultorio,
)
from schemas.consultorio_schemas import (
    MedicamentoUsoCreate,
    MedicamentoTrocaCreate,
    MedicamentoSuspensaoCreate,
    MedicamentoEncerramentoCreate,
    IntervencaoFarmacoterapiaCreate,
    DesfechoIntervencaoFarmacoterapiaCreate,
)
from services.farmacoterapia import (
    montar_avaliacao_polifarmacia,
    montar_evolucao_farmacoterapeutica,
    montar_sugestoes_plano_cuidado,
    montar_dashboard_farmacoterapeutico,
)
from routers.consultorio import (
    get_db_consultorio,
    get_current_user_consultorio,
    exigir_farmaceutico_ou_admin,
)

router = APIRouter(
    prefix="/consultorio",
    tags=["Farmacoterapia"]
)

BaseConsultorio.metadata.create_all(bind=engine)


def _adicionar_coluna_farmacoterapia_se_nao_existir(tabela: str, definicao_coluna: str) -> None:
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql(f"ALTER TABLE {tabela} ADD COLUMN {definicao_coluna}")
            conn.commit()
    except Exception:
        pass


# Garante compatibilidade com bancos já existentes antes do passo 14E.2B.
_adicionar_coluna_farmacoterapia_se_nao_existir("medicamentos_uso", "catalogo_medicamento_id INTEGER")
_adicionar_coluna_farmacoterapia_se_nao_existir("medicamentos_uso", "frequencia_uso VARCHAR")
_adicionar_coluna_farmacoterapia_se_nao_existir("medicamentos_uso", "horarios_uso TEXT")
_adicionar_coluna_farmacoterapia_se_nao_existir("medicamentos_uso", "uso_se_necessario BOOLEAN DEFAULT FALSE")
_adicionar_coluna_farmacoterapia_se_nao_existir("medicamentos_uso", "status_farmacoterapia VARCHAR DEFAULT 'EM_USO'")
_adicionar_coluna_farmacoterapia_se_nao_existir("medicamentos_uso", "data_status DATETIME")
_adicionar_coluna_farmacoterapia_se_nao_existir("medicamentos_uso", "motivo_status VARCHAR")
_adicionar_coluna_farmacoterapia_se_nao_existir("medicamentos_uso", "tipo_suspensao VARCHAR")
_adicionar_coluna_farmacoterapia_se_nao_existir("medicamentos_uso", "observacao_status TEXT")
_adicionar_coluna_farmacoterapia_se_nao_existir("medicamentos_uso", "substituido_por_medicamento_id INTEGER")
_adicionar_coluna_farmacoterapia_se_nao_existir("medicamentos_uso", "prm_relacionado_id INTEGER")
_adicionar_coluna_farmacoterapia_se_nao_existir("medicamentos_uso", "intervencao_relacionada_id INTEGER")
_adicionar_coluna_farmacoterapia_se_nao_existir("catalogo_medicamentos", "principio_ativo VARCHAR")
_adicionar_coluna_farmacoterapia_se_nao_existir("catalogo_medicamentos", "nome_comercial VARCHAR")
_adicionar_coluna_farmacoterapia_se_nao_existir("catalogo_medicamentos", "laboratorio VARCHAR")
_adicionar_coluna_farmacoterapia_se_nao_existir("catalogo_medicamentos", "registro_anvisa VARCHAR")
_adicionar_coluna_farmacoterapia_se_nao_existir("catalogo_medicamentos", "classe_terapeutica VARCHAR")

VIAS_ADMINISTRACAO = [
    "oral", "sublingual", "inalatória", "nasal", "oftálmica", "otológica",
    "tópica", "transdérmica", "subcutânea", "intramuscular", "intravenosa",
    "retal", "vaginal"
]

HORARIOS_PADRAO = [
    "06:00", "07:00", "08:00", "12:00", "14:00", "18:00", "20:00", "22:00",
    "ao acordar", "antes de dormir", "antes das refeições", "após refeições", "se necessário"
]

FREQUENCIAS_USO = [
    "1x ao dia", "2x ao dia", "3x ao dia", "4x ao dia", "a cada 6 horas",
    "a cada 8 horas", "a cada 12 horas", "semanal", "quinzenal", "mensal",
    "antes das refeições", "após refeições", "se necessário"
]


STATUS_FARMACOTERAPIA = ["EM_USO", "TROCADO", "SUSPENSO", "ENCERRADO"]
MOTIVOS_TROCA = [
    "INEFETIVIDADE", "REACAO_ADVERSA", "INTERACAO_MEDICAMENTOSA",
    "DESABASTECIMENTO", "AJUSTE_TERAPEUTICO", "SIMPLIFICACAO_ESQUEMA", "OUTRO"
]
MOTIVOS_SUSPENSAO = [
    "EVENTO_ADVERSO", "CONTRAINDICACAO", "FIM_DO_TRATAMENTO",
    "NAO_ADESAO", "DECISAO_MEDICA", "DECISAO_PACIENTE", "OUTRO"
]
MOTIVOS_ENCERRAMENTO = [
    "FIM_DO_TRATAMENTO", "TRATAMENTO_CONCLUIDO", "CURSO_CURTO_FINALIZADO", "OUTRO"
]
TIPOS_SUSPENSAO = ["TEMPORARIA", "DEFINITIVA"]


def _data_para_datetime(valor):
    if not valor:
        return datetime.utcnow()
    return datetime.combine(valor, time.min)


def _descricao_catalogo(medicamento: CatalogoMedicamento) -> str:
    partes = [
        medicamento.nome_comercial,
        medicamento.principio_ativo or medicamento.farmaco,
        medicamento.concentracao,
        medicamento.apresentacao,
        medicamento.forma_farmaceutica,
    ]
    return " - ".join([str(p) for p in partes if p])


def _normalizar_payload_medicamento(dados: MedicamentoUsoCreate, db: Session) -> dict:
    payload = dados.model_dump()
    nome = (payload.get("nome_medicamento") or "").strip()
    catalogo_id = payload.get("catalogo_medicamento_id")

    if catalogo_id:
        item = db.query(CatalogoMedicamento).filter(
            CatalogoMedicamento.id == catalogo_id,
            CatalogoMedicamento.ativo == True,
        ).first()
        if not item:
            raise HTTPException(status_code=404, detail="Medicamento do catálogo não encontrado")
        if not nome:
            nome = _descricao_catalogo(item) or item.farmaco

    if not nome:
        raise HTTPException(status_code=400, detail="Informe o medicamento ou selecione um item do catálogo")

    payload["nome_medicamento"] = nome

    if payload.get("frequencia_uso") and not payload.get("frequencia"):
        payload["frequencia"] = payload["frequencia_uso"]

    if payload.get("uso_se_necessario") and not payload.get("frequencia_uso"):
        payload["frequencia_uso"] = "se necessário"
        payload["frequencia"] = payload.get("frequencia") or "se necessário"

    return payload



@router.get("/farmacoterapia/opcoes")
def opcoes_farmacoterapia(current=Depends(get_current_user_consultorio)):
    return {
        "vias_administracao": VIAS_ADMINISTRACAO,
        "horarios_padrao": HORARIOS_PADRAO,
        "frequencias_uso": FREQUENCIAS_USO,
        "adesao_referida": ["boa", "regular", "ruim", "nao_avaliada"],
        "orientacao_catalogo": "Use catalogo_medicamento_id quando houver correspondência; mantenha nome_medicamento para registro manual quando necessário.",
        "status_farmacoterapia": STATUS_FARMACOTERAPIA,
        "motivos_troca": MOTIVOS_TROCA,
        "motivos_suspensao": MOTIVOS_SUSPENSAO,
        "motivos_encerramento": MOTIVOS_ENCERRAMENTO,
        "tipos_suspensao": TIPOS_SUSPENSAO,
    }

@router.get("/paciente-clinico/{paciente_id}/evolucao-farmacoterapeutica")
def evolucao_farmacoterapeutica(
    paciente_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    return montar_evolucao_farmacoterapeutica(
        paciente_id=paciente_id,
        db=db
    )


@router.get("/paciente-clinico/{paciente_id}/sugestoes-plano-cuidado")
def sugestoes_plano_cuidado(
    paciente_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    return montar_sugestoes_plano_cuidado(
        paciente_id=paciente_id,
        db=db
    )


@router.get("/dashboard-farmacoterapeutico")
def dashboard_farmacoterapeutico(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    return montar_dashboard_farmacoterapeutico(db=db)


@router.post("/paciente-clinico/{paciente_id}/medicamento")
def adicionar_medicamento_uso(
    paciente_id: int,
    dados: MedicamentoUsoCreate,
    db: Session = Depends(get_db_consultorio),
    current: UserConsultorio = Depends(get_current_user_consultorio)
):
    exigir_farmaceutico_ou_admin(current)

    paciente = db.query(PacienteClinico).filter(
        PacienteClinico.id == paciente_id
    ).first()

    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente clínico não encontrado")

    payload = _normalizar_payload_medicamento(dados, db)

    novo = MedicamentoUso(
        paciente_clinico_id=paciente_id,
        **payload
    )

    db.add(novo)
    db.commit()
    db.refresh(novo)

    return novo


@router.get("/paciente-clinico/{paciente_id}/medicamentos")
def listar_medicamentos_uso(
    paciente_id: int,
    db: Session = Depends(get_db_consultorio)
):
    medicamentos = db.query(MedicamentoUso).filter(
        MedicamentoUso.paciente_clinico_id == paciente_id,
        MedicamentoUso.ativo == True
    ).order_by(MedicamentoUso.criado_em.desc()).all()


    return medicamentos


@router.post("/medicamentos/{medicamento_id}/trocar")
def trocar_medicamento_uso(
    medicamento_id: int,
    dados: MedicamentoTrocaCreate,
    db: Session = Depends(get_db_consultorio),
    current: UserConsultorio = Depends(get_current_user_consultorio)
):
    exigir_farmaceutico_ou_admin(current)

    medicamento = db.query(MedicamentoUso).filter(MedicamentoUso.id == medicamento_id).first()
    if not medicamento:
        raise HTTPException(status_code=404, detail="Medicamento não encontrado")

    payload_novo = _normalizar_payload_medicamento(dados.novo_medicamento, db)
    novo = MedicamentoUso(
        paciente_clinico_id=medicamento.paciente_clinico_id,
        **payload_novo,
    )
    novo.status_farmacoterapia = "EM_USO"

    db.add(novo)
    db.flush()

    medicamento.status_farmacoterapia = "TROCADO"
    medicamento.data_status = _data_para_datetime(dados.data_troca)
    medicamento.motivo_status = dados.motivo_troca
    medicamento.observacao_status = dados.observacao
    medicamento.substituido_por_medicamento_id = novo.id
    medicamento.prm_relacionado_id = dados.prm_relacionado_id
    medicamento.intervencao_relacionada_id = dados.intervencao_relacionada_id

    db.commit()
    db.refresh(medicamento)
    db.refresh(novo)

    return {
        "mensagem": "Troca de medicamento registrada com sucesso.",
        "medicamento_anterior": medicamento,
        "medicamento_novo": novo,
    }


@router.post("/medicamentos/{medicamento_id}/suspender")
def suspender_medicamento_uso(
    medicamento_id: int,
    dados: MedicamentoSuspensaoCreate,
    db: Session = Depends(get_db_consultorio),
    current: UserConsultorio = Depends(get_current_user_consultorio)
):
    exigir_farmaceutico_ou_admin(current)

    medicamento = db.query(MedicamentoUso).filter(MedicamentoUso.id == medicamento_id).first()
    if not medicamento:
        raise HTTPException(status_code=404, detail="Medicamento não encontrado")

    medicamento.status_farmacoterapia = "SUSPENSO"
    medicamento.data_status = _data_para_datetime(dados.data_suspensao)
    medicamento.motivo_status = dados.motivo_suspensao
    medicamento.tipo_suspensao = dados.tipo_suspensao
    medicamento.observacao_status = dados.observacao
    medicamento.prm_relacionado_id = dados.prm_relacionado_id
    medicamento.intervencao_relacionada_id = dados.intervencao_relacionada_id

    db.commit()
    db.refresh(medicamento)

    return {"mensagem": "Suspensão de medicamento registrada com sucesso.", "medicamento": medicamento}


@router.post("/medicamentos/{medicamento_id}/encerrar")
def encerrar_medicamento_uso(
    medicamento_id: int,
    dados: MedicamentoEncerramentoCreate,
    db: Session = Depends(get_db_consultorio),
    current: UserConsultorio = Depends(get_current_user_consultorio)
):
    exigir_farmaceutico_ou_admin(current)

    medicamento = db.query(MedicamentoUso).filter(MedicamentoUso.id == medicamento_id).first()
    if not medicamento:
        raise HTTPException(status_code=404, detail="Medicamento não encontrado")

    medicamento.status_farmacoterapia = "ENCERRADO"
    medicamento.data_status = _data_para_datetime(dados.data_encerramento)
    medicamento.motivo_status = dados.motivo_encerramento
    medicamento.observacao_status = dados.observacao
    medicamento.prm_relacionado_id = dados.prm_relacionado_id
    medicamento.intervencao_relacionada_id = dados.intervencao_relacionada_id

    db.commit()
    db.refresh(medicamento)

    return {"mensagem": "Encerramento de medicamento registrado com sucesso.", "medicamento": medicamento}


@router.get("/paciente-clinico/{paciente_id}/avaliacao-polifarmacia")
def avaliar_polifarmacia(
    paciente_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    return montar_avaliacao_polifarmacia(
        paciente_id=paciente_id,
        db=db
    )


@router.post("/paciente-clinico/{paciente_id}/intervencao-farmacoterapia")
def adicionar_intervencao_farmacoterapia(
    paciente_id: int,
    dados: IntervencaoFarmacoterapiaCreate,
    db: Session = Depends(get_db_consultorio),
    current: UserConsultorio = Depends(get_current_user_consultorio)
):
    exigir_farmaceutico_ou_admin(current)

    paciente = db.query(PacienteClinico).filter(
        PacienteClinico.id == paciente_id
    ).first()

    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente clínico não encontrado")

    if dados.medicamento_uso_id:
        medicamento = db.query(MedicamentoUso).filter(
            MedicamentoUso.id == dados.medicamento_uso_id,
            MedicamentoUso.paciente_clinico_id == paciente_id
        ).first()

        if not medicamento:
            raise HTTPException(
                status_code=404,
                detail="Medicamento não encontrado para este paciente."
            )

    nova = IntervencaoFarmacoterapia(
        paciente_clinico_id=paciente_id,
        **dados.model_dump()
    )

    db.add(nova)
    db.commit()
    db.refresh(nova)

    return nova


@router.get("/paciente-clinico/{paciente_id}/intervencoes-farmacoterapia")
def listar_intervencoes_farmacoterapia(
    paciente_id: int,
    db: Session = Depends(get_db_consultorio),
    current: UserConsultorio = Depends(get_current_user_consultorio)
):
    intervencoes = db.query(IntervencaoFarmacoterapia).filter(
        IntervencaoFarmacoterapia.paciente_clinico_id == paciente_id
    ).order_by(IntervencaoFarmacoterapia.criado_em.desc()).all()

    return intervencoes


@router.post("/intervencao-farmacoterapia/{intervencao_id}/desfecho")
def adicionar_desfecho_intervencao_farmacoterapia(
    intervencao_id: int,
    dados: DesfechoIntervencaoFarmacoterapiaCreate,
    db: Session = Depends(get_db_consultorio),
    current: UserConsultorio = Depends(get_current_user_consultorio)
):
    exigir_farmaceutico_ou_admin(current)

    intervencao = db.query(IntervencaoFarmacoterapia).filter(
        IntervencaoFarmacoterapia.id == intervencao_id
    ).first()

    if not intervencao:
        raise HTTPException(status_code=404, detail="Intervenção não encontrada")

    novo = DesfechoIntervencaoFarmacoterapia(
        intervencao_id=intervencao_id,
        **dados.model_dump()
    )

    db.add(novo)
    db.commit()
    db.refresh(novo)

    return novo


@router.get("/intervencao-farmacoterapia/{intervencao_id}/desfechos")
def listar_desfechos_intervencao_farmacoterapia(
    intervencao_id: int,
    db: Session = Depends(get_db_consultorio),
    current: UserConsultorio = Depends(get_current_user_consultorio)
):
    desfechos = db.query(DesfechoIntervencaoFarmacoterapia).filter(
        DesfechoIntervencaoFarmacoterapia.intervencao_id == intervencao_id
    ).order_by(DesfechoIntervencaoFarmacoterapia.criado_em.desc()).all()

    return desfechos
