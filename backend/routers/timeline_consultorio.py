from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from database import SessionLocal
from auth import ALGORITHM, SECRET_KEY, oauth2_scheme
from models.consultorio_models import (
    PacienteClinico,
    AtendimentoRapido,
    AfericaoPA,
    GlicemiaCapilar,
    Bioimpedancia,
    PicoFluxo,
    ProntuarioClinico,
    EvolucaoClinica,
    DesfechoClinico,
    MedicamentoUso,
    IntervencaoFarmacoterapia,
    DesfechoIntervencaoFarmacoterapia,
    EvolucaoFarmaceutica,
    UserConsultorio,
)
from services.consultorio_helpers import calcular_idade


def get_db_consultorio():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user_consultorio(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db_consultorio),
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Token inválido")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

    user = db.query(UserConsultorio).filter(UserConsultorio.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    return user


router = APIRouter(prefix="/consultorio", tags=["Consultório Farmacêutico - Timeline"])


@router.get("/paciente-clinico/{paciente_clinico_id}/timeline")
def timeline_paciente_clinico(
    paciente_clinico_id: int,
    db: Session = Depends(get_db_consultorio)
):
    paciente = db.query(PacienteClinico).filter(
        PacienteClinico.id == paciente_clinico_id
    ).first()

    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente clínico não encontrado")

    timeline = []

    if paciente.paciente_simplificado_origem_id:
        atendimentos = db.query(AtendimentoRapido).filter(
            AtendimentoRapido.paciente_simplificado_id == paciente.paciente_simplificado_origem_id
        ).all()

        for atendimento in atendimentos:
            pa = db.query(AfericaoPA).filter(
                AfericaoPA.atendimento_rapido_id == atendimento.id
            ).first()

            if pa:
                timeline.append({
                    "tipo": "servico_rapido",
                    "subtipo": "pressao_arterial",
                    "data": atendimento.data_atendimento,
                    "titulo": "Aferição de pressão arterial",
                    "descricao": f"PA {pa.pressao_sistolica}/{pa.pressao_diastolica} mmHg - {pa.classificacao}",
                    "atendimento_id": atendimento.id,
                    "origem": "servicos_rapidos"
                })

            glicemia = db.query(GlicemiaCapilar).filter(
                GlicemiaCapilar.atendimento_rapido_id == atendimento.id
            ).first()

            if glicemia:
                timeline.append({
                    "tipo": "servico_rapido",
                    "subtipo": "glicemia_capilar",
                    "data": atendimento.data_atendimento,
                    "titulo": "Glicemia capilar",
                    "descricao": f"Glicemia {glicemia.valor_glicemia} mg/dL - {glicemia.classificacao}",
                    "atendimento_id": atendimento.id,
                    "origem": "servicos_rapidos"
                })

            bio = db.query(Bioimpedancia).filter(
                Bioimpedancia.atendimento_rapido_id == atendimento.id
            ).first()

            if bio:
                timeline.append({
                    "tipo": "servico_rapido",
                    "subtipo": "bioimpedancia",
                    "data": atendimento.data_atendimento,
                    "titulo": "Bioimpedância",
                    "descricao": (
                        f"IMC {bio.imc or '—'}"
                        f" - {bio.classificacao_imc or bio.classificacao or 'Sem classificação'}"
                        f" | GV {bio.gordura_visceral or '—'}"
                        f" - {bio.classificacao_gordura_visceral or 'Sem classificação'}"
                        f" | Risco {bio.risco_cardiometabolico or 'Não classificado'}"
                    ),
                    "atendimento_id": atendimento.id,
                    "origem": "servicos_rapidos"
                })

            pico = db.query(PicoFluxo).filter(
                PicoFluxo.atendimento_rapido_id == atendimento.id
            ).first()

            if pico:
                timeline.append({
                    "tipo": "servico_rapido",
                    "subtipo": "pico_fluxo",
                    "data": atendimento.data_atendimento,
                    "titulo": "Pico de fluxo expiratório",
                    "descricao": f"PFE {pico.valor_medido} L/min - {pico.classificacao}",
                    "atendimento_id": atendimento.id,
                    "origem": "servicos_rapidos"
                })

        evolucoes_farmaceuticas = db.query(EvolucaoFarmaceutica).filter(
            EvolucaoFarmaceutica.paciente_simplificado_id
            == paciente.paciente_simplificado_origem_id
        ).all()

        for evolucao_farmaceutica in evolucoes_farmaceuticas:
            timeline.append({
                "tipo": "evolucao_farmaceutica",
                "subtipo": "soap",
                "data": evolucao_farmaceutica.criado_em,
                "titulo": "Evolução farmacêutica SOAP",
                "descricao": (
                    evolucao_farmaceutica.avaliacao
                    or evolucao_farmaceutica.plano
                    or evolucao_farmaceutica.subjetivo
                    or "Evolução farmacêutica registrada."
                ),
                "evolucao_farmaceutica_id": evolucao_farmaceutica.id,
                "risco_clinico": evolucao_farmaceutica.risco_clinico,
                "adesao": evolucao_farmaceutica.adesao,
                "prm": evolucao_farmaceutica.prm,
                "origem": "cuidado_farmaceutico"
            })
            
    prontuario = db.query(ProntuarioClinico).filter(
        ProntuarioClinico.paciente_clinico_id == paciente.id
    ).first()

    if prontuario:
        timeline.append({
            "tipo": "prontuario",
            "subtipo": "abertura_prontuario",
            "data": prontuario.data_abertura,
            "titulo": "Abertura de prontuário clínico",
            "descricao": prontuario.observacoes or "Prontuário clínico aberto.",
            "prontuario_id": prontuario.id,
            "origem": "consultorio_farmaceutico"
        })

        evolucoes = db.query(EvolucaoClinica).filter(
            EvolucaoClinica.prontuario_id == prontuario.id
        ).all()

        for evolucao in evolucoes:
            timeline.append({
                "tipo": "evolucao",
                "subtipo": evolucao.tipo_atendimento,
                "data": evolucao.data_evolucao,
                "titulo": evolucao.tipo_atendimento or "Evolução clínica",
                "descricao": evolucao.avaliacao_farmaceutica or evolucao.conduta or evolucao.queixa_principal,
                "evolucao_id": evolucao.id,
                "intervencao_id": evolucao.intervencao_id,
                "origem": "consultorio_farmaceutico"
            })

            desfechos = db.query(DesfechoClinico).filter(
                DesfechoClinico.evolucao_id == evolucao.id
            ).all()

            for desfecho in desfechos:
                timeline.append({
                    "tipo": "desfecho",
                    "subtipo": desfecho.melhora_clinica,
                    "data": desfecho.data_desfecho,
                    "titulo": "Desfecho clínico",
                    "descricao": desfecho.resultado_observado or desfecho.observacoes,
                    "evolucao_id": evolucao.id,
                    "desfecho_id": desfecho.id,
                    "origem": "consultorio_farmaceutico"
                })

    timeline_ordenada = sorted(
        timeline,
        key=lambda item: item["data"] or datetime.min
    )

    return {
        "paciente": {
            "id": paciente.id,
            "nome": paciente.nome,
            "idade": calcular_idade(paciente.data_nascimento),
            "sexo": paciente.sexo,
            "bairro": paciente.bairro
        },
        "total_eventos": len(timeline_ordenada),
        "timeline": timeline_ordenada
    }


@router.get("/paciente-clinico/{paciente_id}/linha-tempo")
def linha_tempo_clinica(
    paciente_id: int,
    db: Session = Depends(get_db_consultorio),
    current: UserConsultorio = Depends(get_current_user_consultorio)
):
    paciente = db.query(PacienteClinico).filter(
        PacienteClinico.id == paciente_id
    ).first()

    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")

    eventos = []

    prontuario = db.query(ProntuarioClinico).filter(
        ProntuarioClinico.paciente_clinico_id == paciente_id
    ).first()

    if prontuario:
        evolucoes = db.query(EvolucaoClinica).filter(
            EvolucaoClinica.prontuario_id == prontuario.id
        ).all()

        for item in evolucoes:
            eventos.append({
                "tipo": "evolucao_clinica",
                "data": item.data_evolucao or item.criado_em,
                "titulo": item.tipo_atendimento or "Evolução clínica",
                "descricao": item.queixa_principal,
                "detalhes": {
                    "avaliacao": item.avaliacao_farmaceutica,
                    "conduta": item.conduta,
                    "orientacoes": item.orientacoes_realizadas,
                    "plano": item.plano_acompanhamento,
                }
            })

            desfechos_clinicos = db.query(DesfechoClinico).filter(
                DesfechoClinico.evolucao_id == item.id
            ).all()

            for desfecho in desfechos_clinicos:
                eventos.append({
                    "tipo": "desfecho_clinico",
                    "data": desfecho.data_desfecho or desfecho.criado_em,
                    "titulo": "Desfecho clínico",
                    "descricao": desfecho.resultado_observado or desfecho.observacoes,
                    "detalhes": {
                        "melhora": desfecho.melhora_clinica,
                        "adesao": desfecho.adesao_tratamento,
                        "resolvido": desfecho.resolucao_problema,
                        "encaminhamento": desfecho.necessidade_encaminhamento,
                    }
                })

    intervencoes = db.query(IntervencaoFarmacoterapia).filter(
        IntervencaoFarmacoterapia.paciente_clinico_id == paciente_id
    ).all()

    for item in intervencoes:
        eventos.append({
            "tipo": "intervencao_farmacoterapeutica",
            "data": item.criado_em,
            "titulo": item.tipo_intervencao,
            "descricao": item.descricao,
            "detalhes": {
                "conduta": item.conduta,
                "aceita": item.aceita_pelo_paciente,
                "encaminhamento": item.necessidade_encaminhamento,
                "observacoes": item.observacoes,
            }
        })

        desfechos = db.query(DesfechoIntervencaoFarmacoterapia).filter(
            DesfechoIntervencaoFarmacoterapia.intervencao_id == item.id
        ).all()

        for desfecho in desfechos:
            eventos.append({
                "tipo": "desfecho_clinico",
                "data": desfecho.criado_em,
                "titulo": desfecho.status_desfecho,
                "descricao": desfecho.resultado_observado or desfecho.observacoes,
                "detalhes": {
                    "nova_intervencao": desfecho.necessidade_nova_intervencao,
                }
            })

    medicamentos = db.query(MedicamentoUso).filter(
        MedicamentoUso.paciente_clinico_id == paciente_id,
        MedicamentoUso.ativo == True
    ).all()

    for item in medicamentos:
        descricao = " ".join(
            parte for parte in [item.dose, item.via, item.frequencia]
            if parte
        )

        eventos.append({
            "tipo": "farmacoterapia",
            "data": item.criado_em,
            "titulo": item.nome_medicamento,
            "descricao": descricao,
            "detalhes": {
                "indicacao": item.indicacao,
                "adesao": item.adesao_referida,
                "observacoes": item.observacoes,
            }
        })

    eventos_ordenados = sorted(
        eventos,
        key=lambda x: x.get("data") or datetime.min,
        reverse=True
    )

    return {
        "paciente": {
            "id": paciente.id,
            "nome": paciente.nome,
            "idade": paciente.idade,
            "sexo": paciente.sexo,
        },
        "total_eventos": len(eventos_ordenados),
        "eventos": eventos_ordenados,
    }
