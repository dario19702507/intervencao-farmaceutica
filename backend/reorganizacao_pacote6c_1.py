from pathlib import Path
from datetime import datetime

BASE = Path.cwd()
ROUTERS = BASE / 'routers'
MAIN = BASE / 'main.py'
CONSULTORIO = ROUTERS / 'consultorio.py'
NOVO = ROUTERS / 'consultorio_clinico.py'
BACKUP_DIR = BASE / f"backup_reorganizacao_pacote6c_1_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
BACKUP_DIR.mkdir(exist_ok=True)

if not CONSULTORIO.exists():
    raise FileNotFoundError('routers/consultorio.py não encontrado')

(CONSULTORIO).replace(BACKUP_DIR / 'consultorio.py.bak')
# Regrava consultorio a partir do backup, pois replace move o arquivo
consultorio_text = (BACKUP_DIR / 'consultorio.py.bak').read_text(encoding='utf-8')
CONSULTORIO.write_text(consultorio_text, encoding='utf-8')

if MAIN.exists():
    MAIN.write_text(MAIN.read_text(encoding='utf-8'), encoding='utf-8')
    (BACKUP_DIR / 'main.py.bak').write_text(MAIN.read_text(encoding='utf-8'), encoding='utf-8')

novo_texto = r'''from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

# Pacote 6C-1
# Módulo provisório de Consultório Clínico.
# Nesta fase, importamos modelos/funções do consultorio.py para preservar compatibilidade.
# No pacote 6C-2, removeremos as rotas duplicadas do consultorio.py.

from routers.consultorio import (
    get_db_consultorio,
    get_current_user_consultorio,
    exigir_farmaceutico_ou_admin,
    calcular_idade,
    PacienteSimplificado,
    PacienteClinico,
    ProntuarioClinico,
    EvolucaoClinica,
    DesfechoClinico,
    AtendimentoRapido,
    ConversaoClinicoCreate,
    PacienteClinicoIdentificacaoUpdate,
    PacienteClinicoDadosClinicosUpdate,
    EvolucaoClinicaCreate,
    DesfechoClinicoCreate,
)

router = APIRouter(
    prefix="/consultorio",
    tags=["Consultório Clínico"]
)


@router.post("/converter-para-clinico/{paciente_simplificado_id}")
def converter_para_clinico(
    paciente_simplificado_id: int,
    dados: ConversaoClinicoCreate,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
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
        paciente_agenda_id=paciente.paciente_agenda_id,
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
    current=Depends(get_current_user_consultorio)
):
    exigir_farmaceutico_ou_admin(current)

    paciente = db.query(PacienteClinico).filter(
        PacienteClinico.id == paciente_id
    ).first()

    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente clínico não encontrado")

    for campo, valor in dados.model_dump(exclude_unset=True).items():
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
    current=Depends(get_current_user_consultorio)
):
    exigir_farmaceutico_ou_admin(current)

    paciente = db.query(PacienteClinico).filter(
        PacienteClinico.id == paciente_id
    ).first()

    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente clínico não encontrado")

    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(paciente, campo, valor)

    db.commit()
    db.refresh(paciente)

    return {
        "mensagem": "Perfil clínico atualizado com sucesso.",
        "paciente": paciente
    }


@router.post("/prontuario/{prontuario_id}/evolucao")
def criar_evolucao_clinica(
    prontuario_id: int,
    dados: EvolucaoClinicaCreate,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    exigir_farmaceutico_ou_admin(current)

    prontuario = db.query(ProntuarioClinico).filter(
        ProntuarioClinico.id == prontuario_id
    ).first()

    if not prontuario:
        raise HTTPException(status_code=404, detail="Prontuário não encontrado")

    nova_evolucao = EvolucaoClinica(
        prontuario_id=prontuario_id,
        **dados.model_dump()
    )

    db.add(nova_evolucao)
    db.commit()
    db.refresh(nova_evolucao)

    return {
        "mensagem": "Evolução clínica registrada com sucesso.",
        "evolucao": nova_evolucao
    }


@router.get("/prontuario/{prontuario_id}/evolucoes")
def listar_evolucoes_clinicas(
    prontuario_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    prontuario = db.query(ProntuarioClinico).filter(
        ProntuarioClinico.id == prontuario_id
    ).first()

    if not prontuario:
        raise HTTPException(status_code=404, detail="Prontuário não encontrado")

    evolucoes = db.query(EvolucaoClinica).filter(
        EvolucaoClinica.prontuario_id == prontuario_id
    ).order_by(EvolucaoClinica.data_evolucao.desc()).all()

    return {
        "prontuario_id": prontuario_id,
        "total_evolucoes": len(evolucoes),
        "evolucoes": evolucoes
    }


@router.post("/evolucao/{evolucao_id}/desfecho")
def criar_desfecho_clinico(
    evolucao_id: int,
    dados: DesfechoClinicoCreate,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    exigir_farmaceutico_ou_admin(current)

    evolucao = db.query(EvolucaoClinica).filter(
        EvolucaoClinica.id == evolucao_id
    ).first()

    if not evolucao:
        raise HTTPException(status_code=404, detail="Evolução não encontrada")

    novo_desfecho = DesfechoClinico(
        evolucao_id=evolucao_id,
        **dados.model_dump()
    )

    db.add(novo_desfecho)
    db.commit()
    db.refresh(novo_desfecho)

    return {
        "mensagem": "Desfecho clínico registrado com sucesso.",
        "desfecho": novo_desfecho
    }


@router.get("/evolucao/{evolucao_id}/desfechos")
def listar_desfechos_clinicos(
    evolucao_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    evolucao = db.query(EvolucaoClinica).filter(
        EvolucaoClinica.id == evolucao_id
    ).first()

    if not evolucao:
        raise HTTPException(status_code=404, detail="Evolução não encontrada")

    desfechos = db.query(DesfechoClinico).filter(
        DesfechoClinico.evolucao_id == evolucao_id
    ).order_by(DesfechoClinico.data_desfecho.desc()).all()

    return {
        "evolucao_id": evolucao_id,
        "total_desfechos": len(desfechos),
        "desfechos": desfechos
    }
'''

NOVO.write_text(novo_texto, encoding='utf-8')

main_text = MAIN.read_text(encoding='utf-8')
if 'from routers.consultorio_clinico import router as consultorio_clinico_router' not in main_text:
    marker = 'from routers.consultorio import router as consultorio_router\n'
    if marker in main_text:
        main_text = main_text.replace(marker, marker + 'from routers.consultorio_clinico import router as consultorio_clinico_router\n')
    else:
        main_text = 'from routers.consultorio_clinico import router as consultorio_clinico_router\n' + main_text

if 'app.include_router(consultorio_clinico_router)' not in main_text:
    marker = 'app.include_router(consultorio_router)\n'
    if marker in main_text:
        main_text = main_text.replace(marker, marker + 'app.include_router(consultorio_clinico_router)\n')
    else:
        main_text += '\napp.include_router(consultorio_clinico_router)\n'

MAIN.write_text(main_text, encoding='utf-8')

relatorio = f'''# Resultado - Reorganizacao Pacote 6C-1

Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

## Ações realizadas

- Backup de consultorio.py e main.py em `{BACKUP_DIR.name}`.
- Criado `routers/consultorio_clinico.py`.
- Incluído `consultorio_clinico_router` no `main.py`, se ainda não existia.
- Nenhuma rota foi removida de `consultorio.py` nesta fase.

## Validação

```bash
python -m py_compile routers/consultorio_clinico.py
python -m py_compile main.py
uvicorn main:app --reload
```

## Rotas migradas provisoriamente

- POST /consultorio/converter-para-clinico/{{paciente_simplificado_id}}
- PUT /consultorio/paciente-clinico/{{paciente_id}}/identificacao
- PUT /consultorio/paciente-clinico/{{paciente_id}}/dados-clinicos
- POST /consultorio/prontuario/{{prontuario_id}}/evolucao
- GET /consultorio/prontuario/{{prontuario_id}}/evolucoes
- POST /consultorio/evolucao/{{evolucao_id}}/desfecho
- GET /consultorio/evolucao/{{evolucao_id}}/desfechos

## Próximo passo

Após testar o Swagger e o frontend, executar o Pacote 6C-2 para remover as duplicidades do `consultorio.py`.
'''
(BASE / 'README_reorganizacao_pacote6c_1_resultado.md').write_text(relatorio, encoding='utf-8')
print(relatorio)
