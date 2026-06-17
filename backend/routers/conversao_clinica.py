from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from models.consultorio_models import (
    PacienteSimplificado,
    AtendimentoRapido,
    PacienteClinico,
    ProntuarioClinico,
    UserConsultorio,
)
from schemas.consultorio_schemas import (
    ConversaoClinicoCreate,
    PacienteClinicoIdentificacaoUpdate,
    PacienteClinicoDadosClinicosUpdate,
)
from services.consultorio_helpers import calcular_idade
from routers.consultorio import (
    get_db_consultorio,
    get_current_user_consultorio,
    exigir_farmaceutico_ou_admin,
)

router = APIRouter(
    prefix="/consultorio",
    tags=["Consultório - Conversão e Cadastro Clínico"]
)


@router.post("/converter-para-clinico/{paciente_simplificado_id}")
def converter_para_clinico(
    paciente_simplificado_id: int,
    dados: ConversaoClinicoCreate,
    db: Session = Depends(get_db_consultorio),
    current: UserConsultorio = Depends(get_current_user_consultorio)
):
    if not dados.aceite_verbal:
        raise HTTPException(
            status_code=400,
            detail="A conversão só pode ocorrer após aceite verbal do paciente."
        )

    exigir_farmaceutico_ou_admin(current)
    paciente = db.query(PacienteSimplificado).filter(
        PacienteSimplificado.id == paciente_simplificado_id
    ).first()

    if not paciente:
        raise HTTPException(
            status_code=404,
            detail="Paciente simplificado não encontrado"
        )

    paciente_clinico_existente = db.query(PacienteClinico).filter(
        PacienteClinico.paciente_simplificado_origem_id == paciente.id
    ).first()

    if paciente_clinico_existente:
        prontuario_existente = db.query(ProntuarioClinico).filter(
            ProntuarioClinico.paciente_clinico_id == paciente_clinico_existente.id
        ).first()

        return {
            "mensagem": "Paciente já convertido anteriormente.",
            "paciente_clinico": paciente_clinico_existente,
            "prontuario": prontuario_existente
        }

    novo_paciente = PacienteClinico(
        nome=paciente.nome,
        data_nascimento=paciente.data_nascimento,
        idade=calcular_idade(paciente.data_nascimento),
        sexo=paciente.sexo,
        telefone=paciente.telefone,
        bairro=paciente.bairro,
        endereco=dados.endereco,
        cpf=dados.cpf,
        cns=dados.cns,
        nome_mae=dados.nome_mae,
        paciente_simplificado_origem_id=paciente.id,
        aceite_verbal=dados.aceite_verbal,
        motivo_conversao=dados.motivo_conversao
    )

    db.add(novo_paciente)
    db.commit()
    db.refresh(novo_paciente)

    novo_prontuario = ProntuarioClinico(
        paciente_clinico_id=novo_paciente.id,
        observacoes=dados.observacoes_prontuario
    )

    db.add(novo_prontuario)

    atendimentos = db.query(AtendimentoRapido).filter(
        AtendimentoRapido.paciente_simplificado_id == paciente.id
    ).all()

    for atendimento in atendimentos:
        atendimento.convertido_para_consultorio = True

    db.commit()
    db.refresh(novo_prontuario)

    return {
        "mensagem": "Paciente convertido para acompanhamento clínico após aceite verbal.",
        "paciente_clinico": novo_paciente,
        "prontuario": novo_prontuario
    }


@router.put("/paciente-clinico/{paciente_id}/identificacao")
def atualizar_identificacao_paciente_clinico(
    paciente_id: int,
    dados: PacienteClinicoIdentificacaoUpdate,
    db: Session = Depends(get_db_consultorio),
    current: UserConsultorio = Depends(get_current_user_consultorio)
):
    exigir_farmaceutico_ou_admin(current)

    paciente = db.query(PacienteClinico).filter(
        PacienteClinico.id == paciente_id
    ).first()

    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente clínico não encontrado")

    for campo, valor in dados.model_dump().items():
        setattr(paciente, campo, valor)

    db.commit()
    db.refresh(paciente)

    return {
        "mensagem": "Identificação atualizada com sucesso.",
        "paciente": paciente
    }


@router.put("/paciente-clinico/{paciente_id}/dados-clinicos")
def atualizar_dados_clinicos_paciente(
    paciente_id: int,
    dados: PacienteClinicoDadosClinicosUpdate,
    db: Session = Depends(get_db_consultorio),
    current: UserConsultorio = Depends(get_current_user_consultorio)
):
    exigir_farmaceutico_ou_admin(current)

    paciente = db.query(PacienteClinico).filter(
        PacienteClinico.id == paciente_id
    ).first()

    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente clínico não encontrado")

    for campo, valor in dados.model_dump().items():
        setattr(paciente, campo, valor)

    db.commit()
    db.refresh(paciente)

    return {
        "mensagem": "Perfil clínico atualizado com sucesso.",
        "paciente": paciente
    }


@router.get("/pacientes-clinicos")
def listar_pacientes_clinicos(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db_consultorio)
):
    """Listagem paginada de pacientes clínicos.

    Mantida por compatibilidade com telas antigas, mas sem carregar a base
    inteira por padrão. Para uso operacional no consultório, prefira
    /pacientes-clinicos/buscar.
    """
    limit = max(1, min(limit, 100))
    offset = max(0, offset)

    query = db.query(PacienteClinico)
    total = query.count()
    pacientes = query.order_by(
        PacienteClinico.criado_em.desc()
    ).offset(offset).limit(limit).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "pacientes": pacientes
    }


@router.get("/pacientes-clinicos/buscar")
def buscar_pacientes_clinicos_direto(
    termo: str,
    limit: int = 30,
    db: Session = Depends(get_db_consultorio)
):
    """Busca direta para abrir prontuário no Consultório.

    Pesquisa por nome, CPF, CNS, telefone, bairro e nome da mãe, retornando
    poucos resultados para evitar carregar toda a lista de pacientes.
    """
    termo_limpo = (termo or "").strip()
    if len(termo_limpo) < 3:
        return {"total": 0, "pacientes": []}

    limit = max(1, min(limit, 50))
    like = f"%{termo_limpo}%"
    somente_digitos = "".join(ch for ch in termo_limpo if ch.isdigit())

    filtros = [
        PacienteClinico.nome.ilike(like),
        PacienteClinico.cpf.ilike(like),
        PacienteClinico.cns.ilike(like),
        PacienteClinico.telefone.ilike(like),
        PacienteClinico.bairro.ilike(like),
        PacienteClinico.nome_mae.ilike(like),
    ]

    if somente_digitos and somente_digitos != termo_limpo:
        like_digitos = f"%{somente_digitos}%"
        filtros.extend([
            PacienteClinico.cpf.ilike(like_digitos),
            PacienteClinico.cns.ilike(like_digitos),
            PacienteClinico.telefone.ilike(like_digitos),
        ])

    pacientes = db.query(PacienteClinico).filter(
        or_(*filtros)
    ).order_by(
        PacienteClinico.nome.asc()
    ).limit(limit).all()

    return {
        "total": len(pacientes),
        "pacientes": pacientes
    }


@router.get("/buscar-paciente")
def buscar_paciente(
    nome: Optional[str] = None,
    bairro: Optional[str] = None,
    db: Session = Depends(get_db_consultorio)
):
    query = db.query(PacienteClinico)

    if nome:
        query = query.filter(PacienteClinico.nome.ilike(f"%{nome}%"))

    if bairro:
        query = query.filter(PacienteClinico.bairro.ilike(f"%{bairro}%"))

    pacientes = query.all()

    return {
        "total": len(pacientes),
        "pacientes": pacientes
    }


@router.get("/paciente-clinico/{paciente_id}")
def detalhe_paciente_clinico(
    paciente_id: int,
    db: Session = Depends(get_db_consultorio)
):
    paciente = db.query(PacienteClinico).filter(
        PacienteClinico.id == paciente_id
    ).first()

    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")

    prontuario = db.query(ProntuarioClinico).filter(
        ProntuarioClinico.paciente_clinico_id == paciente.id
    ).first()

    return {
        "paciente": paciente,
        "prontuario": prontuario
    }
