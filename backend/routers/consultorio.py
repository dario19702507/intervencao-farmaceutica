from io import BytesIO
from dotenv import load_dotenv
load_dotenv()
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
import os
from sqlalchemy import text
from datetime import datetime, date, timedelta
from typing import Optional
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime, Text, ForeignKey, Boolean, Float, func
from collections import defaultdict
from openpyxl import Workbook
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
SECRET_KEY = os.getenv("SECRET_KEY", "troque-esta-chave-em-producao")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./intervencoes.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
BaseConsultorio = declarative_base()


def get_db_consultorio():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class PacienteSimplificado(BaseConsultorio):
    __tablename__ = "pacientes_simplificados"

    id = Column(Integer, primary_key=True, index=True)
    paciente_agenda_id = Column(Integer, nullable=True)
    nome = Column(String, nullable=False, index=True)
    data_nascimento = Column(Date, nullable=True)
    idade = Column(Integer, nullable=True)
    sexo = Column(String, nullable=True)
    telefone = Column(String, nullable=True)
    bairro = Column(String, nullable=True)
    observacoes = Column(Text, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)


class AtendimentoRapido(BaseConsultorio):
    __tablename__ = "atendimentos_rapidos"

    id = Column(Integer, primary_key=True, index=True)
    paciente_simplificado_id = Column(Integer, ForeignKey("pacientes_simplificados.id"), nullable=False)
    tipo_servico = Column(String, nullable=False)
    data_atendimento = Column(DateTime, default=datetime.utcnow)
    observacoes = Column(Text, nullable=True)
    convertido_para_consultorio = Column(Boolean, default=False)


class AfericaoPA(BaseConsultorio):
    __tablename__ = "afericoes_pa"

    id = Column(Integer, primary_key=True, index=True)
    atendimento_rapido_id = Column(Integer, ForeignKey("atendimentos_rapidos.id"), nullable=False)
    pressao_sistolica = Column(Integer, nullable=False)
    pressao_diastolica = Column(Integer, nullable=False)
    frequencia_cardiaca = Column(Integer, nullable=True)
    posicao_paciente = Column(String, nullable=True)
    braco_medido = Column(String, nullable=True)
    classificacao = Column(String, nullable=True)
    observacoes = Column(Text, nullable=True)


class GlicemiaCapilar(BaseConsultorio):
    __tablename__ = "glicemias_capilares"

    id = Column(Integer, primary_key=True, index=True)
    atendimento_rapido_id = Column(Integer, ForeignKey("atendimentos_rapidos.id"), nullable=False)
    valor_glicemia = Column(Integer, nullable=False)
    tipo_jejum = Column(String, nullable=True)
    classificacao = Column(String, nullable=True)
    observacoes = Column(Text, nullable=True)


class Bioimpedancia(BaseConsultorio):
    __tablename__ = "bioimpedancias"

    id = Column(Integer, primary_key=True, index=True)
    atendimento_rapido_id = Column(Integer, ForeignKey("atendimentos_rapidos.id"), nullable=False)

    peso = Column(Float, nullable=True)
    altura = Column(Float, nullable=True)
    imc = Column(Float, nullable=True)
    classificacao_imc = Column(String, nullable=True)

    percentual_gordura = Column(Float, nullable=True)
    massa_gordura_kg = Column(Float, nullable=True)

    percentual_massa_muscular = Column(Float, nullable=True)
    massa_muscular_kg = Column(Float, nullable=True)

    massa_magra_kg = Column(Float, nullable=True)

    gordura_visceral = Column(Float, nullable=True)
    classificacao_gordura_visceral = Column(String, nullable=True)

    metabolismo_basal = Column(Float, nullable=True)
    fator_atividade = Column(Float, nullable=True)
    gasto_energetico_total = Column(Float, nullable=True)

    idade_corporal = Column(Integer, nullable=True)
    diferenca_idade_corporal = Column(Integer, nullable=True)

    fmi = Column(Float, nullable=True)
    ffmi = Column(Float, nullable=True)
    relacao_gordura_musculo = Column(Float, nullable=True)

    risco_cardiometabolico = Column(String, nullable=True)
    alertas = Column(Text, nullable=True)

    classificacao = Column(String, nullable=True)
    observacoes = Column(Text, nullable=True)

class PicoFluxo(BaseConsultorio):
    __tablename__ = "picos_fluxo"

    id = Column(Integer, primary_key=True, index=True)
    atendimento_rapido_id = Column(Integer, ForeignKey("atendimentos_rapidos.id"), nullable=False)
    valor_medido = Column(Integer, nullable=False)
    valor_previsto = Column(Integer, nullable=True)
    percentual_previsto = Column(Float, nullable=True)
    classificacao = Column(String, nullable=True)
    observacoes = Column(Text, nullable=True)

class PacienteClinico(BaseConsultorio):
    __tablename__ = "pacientes_clinicos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False, index=True)
    data_nascimento = Column(Date, nullable=True)
    idade = Column(Integer, nullable=True)
    sexo = Column(String, nullable=True)
    telefone = Column(String, nullable=True)
    bairro = Column(String, nullable=True)
    endereco = Column(Text, nullable=True)
    cpf = Column(String, nullable=True)
    cns = Column(String, nullable=True)
    nome_mae = Column(String, nullable=True)
    origem = Column(String, default="conversao_servico_rapido")
    paciente_simplificado_origem_id = Column(Integer, ForeignKey("pacientes_simplificados.id"), nullable=True)
    paciente_agenda_id = Column(Integer, nullable=True)
    aceite_verbal = Column(Boolean, default=True)
    motivo_conversao = Column(Text, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    cid_principal = Column(String, nullable=True)
    cid_secundario = Column(String, nullable=True)
    comorbidades = Column(Text, nullable=True)
    alergias = Column(Text, nullable=True)
    tabagismo = Column(String, nullable=True)
    etilismo = Column(String, nullable=True)
    atividade_fisica = Column(String, nullable=True)
    historico_familiar = Column(Text, nullable=True)
    pessoa_com_deficiencia = Column(Boolean, default=False)
    tipo_deficiencia = Column(String, nullable=True)
    vacinacao_influenza = Column(Boolean, default=False)
    vacinacao_covid = Column(Boolean, default=False)
    adesao_terapeutica = Column(String, nullable=True)
    meta_pressao_arterial = Column(String, nullable=True)
    meta_glicemica = Column(String, nullable=True)
    meta_peso = Column(String, nullable=True)
    observacoes_clinicas = Column(Text, nullable=True)
    planos_cuidado = relationship("PlanoCuidado", back_populates="paciente", cascade="all, delete-orphan"
    )

class PlanoCuidado(BaseConsultorio):
    __tablename__ = "planos_cuidado"

    id = Column(Integer, primary_key=True, index=True)

    paciente_id = Column(
        Integer,
        ForeignKey("pacientes_clinicos.id"),
        nullable=False
    )

    criado_em = Column(
        DateTime,
        default=datetime.utcnow
    )

    criado_por = Column(String(150))

    problema_identificado = Column(Text)

    objetivo_terapeutico = Column(Text)

    intervencoes_planejadas = Column(Text)

    prazo_reavaliacao = Column(Date)

    status = Column(
        String(30),
        default="pendente"
    )

    observacoes = Column(Text)

    concluido_em = Column(DateTime)

    resultado = Column(Text)

    resultado_classificacao = Column(String(50))

    paciente = relationship(
        "PacienteClinico",
        back_populates="planos_cuidado"
    )    


class ProntuarioClinico(BaseConsultorio):
    __tablename__ = "prontuarios_clinicos"

    id = Column(Integer, primary_key=True, index=True)
    paciente_clinico_id = Column(Integer, ForeignKey("pacientes_clinicos.id"), nullable=False)
    status = Column(String, default="ativo")
    data_abertura = Column(DateTime, default=datetime.utcnow)
    observacoes = Column(Text, nullable=True)    

class EvolucaoClinica(BaseConsultorio):
    __tablename__ = "evolucoes_clinicas"

    id = Column(Integer, primary_key=True, index=True)
    prontuario_id = Column(Integer, ForeignKey("prontuarios_clinicos.id"), nullable=False)

    intervencao_id = Column(Integer, nullable=True)

    data_evolucao = Column(DateTime, default=datetime.utcnow)
    tipo_atendimento = Column(String, nullable=True)

    queixa_principal = Column(Text, nullable=True)
    historia_breve = Column(Text, nullable=True)

    avaliacao_farmaceutica = Column(Text, nullable=True)
    problemas_identificados = Column(Text, nullable=True)

    conduta = Column(Text, nullable=True)
    orientacoes_realizadas = Column(Text, nullable=True)
    plano_acompanhamento = Column(Text, nullable=True)

    necessidade_retorno = Column(Boolean, default=False)
    data_retorno_sugerida = Column(Date, nullable=True)

    observacoes = Column(Text, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)


class DesfechoClinico(BaseConsultorio):
    __tablename__ = "desfechos_clinicos"

    id = Column(Integer, primary_key=True, index=True)
    evolucao_id = Column(Integer, ForeignKey("evolucoes_clinicas.id"), nullable=False)

    data_desfecho = Column(DateTime, default=datetime.utcnow)

    melhora_clinica = Column(String, nullable=True)  # sim, parcial, nao
    adesao_tratamento = Column(String, nullable=True)  # boa, regular, ruim, nao_avaliada
    resolucao_problema = Column(Boolean, default=False)
    necessidade_encaminhamento = Column(Boolean, default=False)

    encaminhamento_realizado = Column(String, nullable=True)
    resultado_observado = Column(Text, nullable=True)
    observacoes = Column(Text, nullable=True)

    criado_em = Column(DateTime, default=datetime.utcnow)

class MedicamentoUso(BaseConsultorio):
    __tablename__ = "medicamentos_uso"

    id = Column(Integer, primary_key=True, index=True)
    paciente_clinico_id = Column(Integer, ForeignKey("pacientes_clinicos.id"), nullable=False)

    nome_medicamento = Column(String, nullable=False)
    dose = Column(String, nullable=True)
    via = Column(String, nullable=True)
    frequencia = Column(String, nullable=True)
    indicacao = Column(String, nullable=True)

    uso_continuo = Column(Boolean, default=True)
    adesao_referida = Column(String, nullable=True)
    observacoes = Column(Text, nullable=True)

    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)


class IntervencaoFarmacoterapia(BaseConsultorio):
    __tablename__ = "intervencoes_farmacoterapia"

    id = Column(Integer, primary_key=True, index=True)
    paciente_clinico_id = Column(Integer, ForeignKey("pacientes_clinicos.id"), nullable=False)
    medicamento_uso_id = Column(Integer, ForeignKey("medicamentos_uso.id"), nullable=True)

    tipo_intervencao = Column(String, nullable=False)
    descricao = Column(Text, nullable=True)
    conduta = Column(Text, nullable=True)
    aceita_pelo_paciente = Column(Boolean, default=False)
    necessidade_encaminhamento = Column(Boolean, default=False)
    observacoes = Column(Text, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)


class DesfechoIntervencaoFarmacoterapia(BaseConsultorio):
    __tablename__ = "desfechos_intervencoes_farmacoterapia"

    id = Column(Integer, primary_key=True, index=True)
    intervencao_id = Column(Integer, ForeignKey("intervencoes_farmacoterapia.id"), nullable=False)
    status_desfecho = Column(String, nullable=False)
    resultado_observado = Column(Text, nullable=True)
    necessidade_nova_intervencao = Column(Boolean, default=False)
    observacoes = Column(Text, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

class EvolucaoFarmaceutica(BaseConsultorio):
    __tablename__ = "evolucoes_farmaceuticas"

    id = Column(Integer, primary_key=True, index=True)
    paciente_simplificado_id = Column(Integer, ForeignKey("pacientes_simplificados.id"), nullable=False)

    subjetivo = Column(Text, nullable=True)
    objetivo = Column(Text, nullable=True)
    avaliacao = Column(Text, nullable=True)
    plano = Column(Text, nullable=True)

    prm = Column(Text, nullable=True)
    adesao = Column(String, nullable=True)
    metas_clinicas = Column(Text, nullable=True)
    orientacoes = Column(Text, nullable=True)
    encaminhamento = Column(Text, nullable=True)

    risco_clinico = Column(String, nullable=True)
    observacoes = Column(Text, nullable=True)

    criado_em = Column(DateTime, default=datetime.utcnow)


class UserConsultorio(BaseConsultorio):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    perfil = Column(String, nullable=True)
    categoria_profissional = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ResolucaoAlertaClinico(BaseConsultorio):
    __tablename__ = "resolucoes_alertas_clinicos"

    id = Column(Integer, primary_key=True, index=True)

    alerta_origem = Column(String, nullable=True)
    alerta_tipo = Column(String, nullable=True)
    alerta_chave = Column(String, nullable=False, index=True)

    paciente_id = Column(Integer, nullable=True)
    paciente_nome = Column(String, nullable=True)

    prioridade = Column(String, nullable=True)
    mensagem_alerta = Column(Text, nullable=True)

    desfecho = Column(String, nullable=False)
    observacoes = Column(Text, nullable=True)

    evolucao_id = Column(Integer, nullable=True)
    intervencao_id = Column(Integer, nullable=True)

    resolvido_por = Column(String, nullable=True)
    resolvido_em = Column(DateTime, default=datetime.utcnow)

class CapacidadeAgenda(BaseConsultorio):
    __tablename__ = "capacidade_agenda"

    id = Column(Integer, primary_key=True, index=True)

    servico_origem = Column(String, nullable=False)
    dia_semana = Column(Integer, nullable=False)

    capacidade_maxima = Column(Integer, nullable=False)

    ativo = Column(Boolean, default=True)

    observacoes = Column(Text, nullable=True)

    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow)

class NotificacaoAgenda(BaseConsultorio):
    __tablename__ = "notificacoes_agenda"

    id = Column(Integer, primary_key=True, index=True)

    agenda_id = Column(Integer, nullable=True)
    paciente_id = Column(Integer, nullable=True)
    paciente_nome = Column(String, nullable=True)
    telefone = Column(String, nullable=True)

    tipo_notificacao = Column(String, nullable=False)

    mensagem = Column(Text, nullable=False)

    data_programada = Column(Date, nullable=True)
    data_envio = Column(DateTime, nullable=True)

    status = Column(String, default="pendente")

    tentativa_envio = Column(Integer, default=0)
    erro_envio = Column(Text, nullable=True)
    usuario_atualizacao = Column(String, nullable=True)
    canal = Column(String, default="interno")

    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow)

class PacienteAgenda(BaseConsultorio):
    __tablename__ = "pacientes_agenda"

    id = Column(Integer, primary_key=True, index=True)

    nome = Column(String, nullable=False, index=True)
    cpf = Column(String, nullable=True, index=True)
    cns = Column(String, nullable=True, index=True)

    telefone = Column(String, nullable=True)
    telefone_alternativo = Column(String, nullable=True)

    municipio = Column(String, nullable=True)
    logradouro = Column(String, nullable=True)
    numero_residencia = Column(String, nullable=True)
    complemento_residencia = Column(String, nullable=True)

    origem = Column(String, default="manual")
    ativo = Column(Boolean, default=True)

    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow)

class AuditoriaSistema(BaseConsultorio):
    __tablename__ = "auditoria_sistema"

    id = Column(Integer, primary_key=True, index=True)
    usuario = Column(String, nullable=True)
    modulo = Column(String, nullable=False)
    acao = Column(String, nullable=False)
    registro_id = Column(Integer, nullable=True)
    descricao = Column(Text, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

class ConfiguracaoSistema(BaseConsultorio):
    __tablename__ = "configuracoes_sistema"

    id = Column(Integer, primary_key=True, index=True)
    chave = Column(String, unique=True, index=True, nullable=False)
    valor = Column(String, nullable=True)
    descricao = Column(Text, nullable=True)
    atualizado_em = Column(DateTime, default=datetime.utcnow)

class PacienteSimplificadoCreate(BaseModel):
    nome: str
    data_nascimento: Optional[date] = None
    idade: Optional[int] = None
    sexo: Optional[str] = None
    telefone: Optional[str] = None
    bairro: Optional[str] = None
    observacoes: Optional[str] = None


class AtendimentoRapidoCreate(BaseModel):
    paciente_simplificado_id: int
    tipo_servico: str
    observacoes: Optional[str] = None


class AfericaoPACreate(BaseModel):
    atendimento_rapido_id: int
    pressao_sistolica: int
    pressao_diastolica: int
    frequencia_cardiaca: Optional[int] = None
    posicao_paciente: Optional[str] = None
    braco_medido: Optional[str] = None
    observacoes: Optional[str] = None


class GlicemiaCapilarCreate(BaseModel):
    atendimento_rapido_id: int
    valor_glicemia: int
    tipo_jejum: Optional[str] = None
    observacoes: Optional[str] = None


class BioimpedanciaCreate(BaseModel):
    atendimento_rapido_id: int

    peso: Optional[float] = None
    altura: Optional[float] = None

    percentual_gordura: Optional[float] = None
    percentual_massa_muscular: Optional[float] = None

    gordura_visceral: Optional[float] = None
    metabolismo_basal: Optional[float] = None
    fator_atividade: Optional[float] = None

    idade_corporal: Optional[int] = None
    observacoes: Optional[str] = None

class PicoFluxoCreate(BaseModel):
    atendimento_rapido_id: int
    valor_medido: int
    valor_previsto: Optional[int] = None
    observacoes: Optional[str] = None

class ConversaoClinicoCreate(BaseModel):
    aceite_verbal: bool
    motivo_conversao: Optional[str] = None
    endereco: Optional[str] = None
    cpf: Optional[str] = None
    cns: Optional[str] = None
    nome_mae: Optional[str] = None
    observacoes_prontuario: Optional[str] = None

class PacienteClinicoIdentificacaoUpdate(BaseModel):
    cpf: Optional[str] = None
    cns: Optional[str] = None
    nome_mae: Optional[str] = None
    telefone: Optional[str] = None
    endereco: Optional[str] = None
    bairro: Optional[str] = None


class PacienteClinicoDadosClinicosUpdate(BaseModel):
    cid_principal: Optional[str] = None
    cid_secundario: Optional[str] = None
    comorbidades: Optional[str] = None
    alergias: Optional[str] = None
    tabagismo: Optional[str] = None
    etilismo: Optional[str] = None
    atividade_fisica: Optional[str] = None
    historico_familiar: Optional[str] = None
    pessoa_com_deficiencia: Optional[bool] = False
    tipo_deficiencia: Optional[str] = None
    vacinacao_influenza: Optional[bool] = False
    vacinacao_covid: Optional[bool] = False
    adesao_terapeutica: Optional[str] = None
    meta_pressao_arterial: Optional[str] = None
    meta_glicemica: Optional[str] = None
    meta_peso: Optional[str] = None
    observacoes_clinicas: Optional[str] = None

class EvolucaoClinicaCreate(BaseModel):
    tipo_atendimento: Optional[str] = None

    queixa_principal: Optional[str] = None
    historia_breve: Optional[str] = None

    avaliacao_farmaceutica: Optional[str] = None
    problemas_identificados: Optional[str] = None

    conduta: Optional[str] = None
    orientacoes_realizadas: Optional[str] = None
    plano_acompanhamento: Optional[str] = None

    necessidade_retorno: bool = False
    data_retorno_sugerida: Optional[date] = None

    observacoes: Optional[str] = None

class DesfechoClinicoCreate(BaseModel):
    melhora_clinica: Optional[str] = None
    adesao_tratamento: Optional[str] = None
    resolucao_problema: bool = False
    necessidade_encaminhamento: bool = False
    encaminhamento_realizado: Optional[str] = None
    resultado_observado: Optional[str] = None
    observacoes: Optional[str] = None

class MedicamentoUsoCreate(BaseModel):
    nome_medicamento: str
    dose: Optional[str] = None
    via: Optional[str] = None
    frequencia: Optional[str] = None
    indicacao: Optional[str] = None
    uso_continuo: bool = True
    adesao_referida: Optional[str] = None
    observacoes: Optional[str] = None    


class IntervencaoFarmacoterapiaCreate(BaseModel):
    medicamento_uso_id: Optional[int] = None
    tipo_intervencao: str
    descricao: Optional[str] = None
    conduta: Optional[str] = None
    aceita_pelo_paciente: bool = False
    necessidade_encaminhamento: bool = False
    observacoes: Optional[str] = None


class DesfechoIntervencaoFarmacoterapiaCreate(BaseModel):
    status_desfecho: str
    resultado_observado: Optional[str] = None
    necessidade_nova_intervencao: bool = False
    observacoes: Optional[str] = None

class EvolucaoFarmaceuticaCreate(BaseModel):
    paciente_simplificado_id: int
    subjetivo: Optional[str] = None
    objetivo: Optional[str] = None
    avaliacao: Optional[str] = None
    plano: Optional[str] = None
    prm: Optional[str] = None
    adesao: Optional[str] = None
    metas_clinicas: Optional[str] = None
    orientacoes: Optional[str] = None
    encaminhamento: Optional[str] = None
    risco_clinico: Optional[str] = None
    observacoes: Optional[str] = None

class ResolucaoAlertaClinicoCreate(BaseModel):
    alerta_origem: Optional[str] = None
    alerta_tipo: Optional[str] = None
    alerta_chave: str

    paciente_id: Optional[int] = None
    paciente_nome: Optional[str] = None

    prioridade: Optional[str] = None
    mensagem_alerta: Optional[str] = None

    desfecho: str
    observacoes: Optional[str] = None

    evolucao_id: Optional[int] = None
    intervencao_id: Optional[int] = None

class PlanoCuidadoCreate(BaseModel):
    paciente_id: int
    problema_identificado: str
    objetivo_terapeutico: str
    intervencoes_planejadas: str
    prazo_reavaliacao: Optional[date] = None
    observacoes: Optional[str] = None


class PlanoCuidadoUpdate(BaseModel):
    problema_identificado: Optional[str] = None
    objetivo_terapeutico: Optional[str] = None
    intervencoes_planejadas: Optional[str] = None
    prazo_reavaliacao: Optional[date] = None
    status: Optional[str] = None
    observacoes: Optional[str] = None


class PlanoCuidadoConclusao(BaseModel):
    resultado: str
    resultado_classificacao: str

class AgendaIntegrada(BaseConsultorio):
    __tablename__ = "agenda_integrada"

    id = Column(Integer, primary_key=True, index=True)

    servico_origem = Column(String, nullable=False)
    tipo_evento = Column(String, nullable=False)

    paciente_id = Column(Integer, nullable=True)
    paciente_nome = Column(String, nullable=False)
    telefone = Column(String, nullable=True)

    medicamento = Column(String, nullable=True)
    situacao_laudo = Column(String, nullable=True)

    data_evento = Column(Date, nullable=False)

    status = Column(String, default="agendado")

    data_status = Column(DateTime, nullable=True)
    usuario_status = Column(String, nullable=True)

    mensagem_notificacao = Column(Text, nullable=True)
    data_inicio_vigencia = Column(Date, nullable=True)
    data_fim_vigencia = Column(Date, nullable=True)

    renovado = Column(Boolean, default=False)
    data_renovacao = Column(Date, nullable=True)

    origem_importacao = Column(String, nullable=True)
    lote_importacao = Column(String, nullable=True)

    notificacao_penultimo_mes_enviada = Column(Boolean, default=False)
    notificacao_ultimo_mes_enviada = Column(Boolean, default=False)
    notificacao_atraso_disp_enviada = Column(Boolean, default=False)
    notificar_whatsapp = Column(Boolean, default=True)

    notificacao_vespera_enviada = Column(Boolean, default=False)
    notificacao_dia_enviada = Column(Boolean, default=False)
    notificacao_extra_enviada = Column(Boolean, default=False)

    notificado_em = Column(DateTime, nullable=True)

    referencia_tipo = Column(String, nullable=True)
    referencia_id = Column(Integer, nullable=True)

    observacoes = Column(Text, nullable=True)

    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow)

    evento_pai_id = Column(Integer, nullable=True)

BaseConsultorio.metadata.create_all(bind=engine)

class AgendaIntegradaCreate(BaseModel):
    servico_origem: str
    tipo_evento: str

    paciente_id: Optional[int] = None
    paciente_nome: str
    telefone: Optional[str] = None

    medicamento: Optional[str] = None
    situacao_laudo: Optional[str] = None

    data_evento: Optional[date] = None

    mensagem_notificacao: Optional[str] = None
    notificar_whatsapp: bool = True

    data_inicio_vigencia: Optional[date] = None
    data_fim_vigencia: Optional[date] = None

    renovado: bool = False
    data_renovacao: Optional[date] = None

    referencia_tipo: Optional[str] = None
    referencia_id: Optional[int] = None

    observacoes: Optional[str] = None

class AgendaIntegradaUpdate(BaseModel):
    servico_origem: Optional[str] = None
    tipo_evento: Optional[str] = None

    paciente_nome: Optional[str] = None
    telefone: Optional[str] = None

    medicamento: Optional[str] = None
    situacao_laudo: Optional[str] = None

    data_evento: Optional[date] = None

    data_inicio_vigencia: Optional[date] = None
    data_fim_vigencia: Optional[date] = None

    renovado: Optional[bool] = None
    data_renovacao: Optional[date] = None

    status: Optional[str] = None
    mensagem_notificacao: Optional[str] = None
    notificar_whatsapp: Optional[bool] = None
    observacoes: Optional[str] = None

class AgendaStatusUpdate(BaseModel):
    status: str
    observacoes: Optional[str] = None

class CapacidadeAgendaCreate(BaseModel):
    servico_origem: str
    dia_semana: int
    capacidade_maxima: int
    observacoes: Optional[str] = None


class CapacidadeAgendaUpdate(BaseModel):
    capacidade_maxima: Optional[int] = None
    ativo: Optional[bool] = None
    observacoes: Optional[str] = None

class NotificacaoAgendaUpdate(BaseModel):
    status: Optional[str] = None
    data_envio: Optional[datetime] = None
    erro_envio: Optional[str] = None
    canal: Optional[str] = None

class PacienteAgendaCreate(BaseModel):
    nome: str
    cpf: Optional[str] = None
    cns: Optional[str] = None
    telefone: Optional[str] = None
    telefone_alternativo: Optional[str] = None
    municipio: Optional[str] = None
    logradouro: Optional[str] = None
    numero_residencia: Optional[str] = None
    complemento_residencia: Optional[str] = None
    origem: Optional[str] = "manual"


class PacienteAgendaUpdate(BaseModel):
    nome: Optional[str] = None
    cpf: Optional[str] = None
    cns: Optional[str] = None
    telefone: Optional[str] = None
    telefone_alternativo: Optional[str] = None
    municipio: Optional[str] = None
    logradouro: Optional[str] = None
    numero_residencia: Optional[str] = None
    complemento_residencia: Optional[str] = None
    ativo: Optional[bool] = None

router = APIRouter(
    prefix="/consultorio",
    tags=["Consultório Farmacêutico"]
)

TIPOS_EVENTO_AGENDA = [
    "retirada_medicamento",
    "renovacao_laudo",
    "adequacao",
    "encerramento",
    "retorno_consultorio",
    "consulta_farmaceutica",
    "risco_interrupcao_tratamento",
]

STATUS_AGENDA = [
    "agendado",
    "notificado",
    "reagendado",
    "realizado",
    "cancelado",
    "renovacao_recomendada",
    "renovacao_urgente",
    "risco_interrupcao_tratamento",
]

SERVICOS_ORIGEM_AGENDA = [
    "dispensacao",
    "renovacao_laudo",
    "consultorio",
    "intervencao",
]

def get_current_user_consultorio(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db_consultorio)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")

        if not email:
            raise HTTPException(status_code=401, detail="Token inválido")

    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

    user = db.query(UserConsultorio).filter(
        UserConsultorio.email == email
    ).first()

    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")

    return user


def exigir_autenticado(user: UserConsultorio):
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Usuário não autenticado"
        )

def exigir_pode_registrar(user: UserConsultorio):

    if user.perfil in ["admin", "operador"]:
        return

    if user.categoria_profissional in [
        "Farmacêutico",
        "Docente",
        "Residente",
        "Estagiário"
    ]:
        return

    raise HTTPException(
        status_code=403,
        detail="Usuário sem permissão para registrar dados."
    )

def exigir_farmaceutico_ou_admin(user: UserConsultorio):
    if user.perfil == "admin":
        return

    if user.categoria_profissional in ["Farmacêutico", "Docente"]:
        return

    raise HTTPException(
        status_code=403,
        detail="Ação permitida apenas para farmacêutico, docente ou administrador."
    )


def exigir_admin(user: UserConsultorio):
    if user.perfil != "admin":
        raise HTTPException(
            status_code=403,
            detail="Ação restrita ao administrador."
        )

def calcular_idade(data_nascimento):
    if not data_nascimento:
        return None

    hoje = date.today()

    idade = hoje.year - data_nascimento.year

    if (
        (hoje.month, hoje.day)
        < (data_nascimento.month, data_nascimento.day)
    ):
        idade -= 1

    return idade


def calcular_risco_populacional(
    pa=None,
    glicemia=None,
    bio=None,
    pico=None,
    reincidencia_alertas=0,
    adesao=None,
):
    score = 0

    fatores = []

    # PRESSÃO ARTERIAL
    if pa:
        classificacao_pa = getattr(pa, "classificacao", None)

        if classificacao_pa == "pa_elevada":
            score += 1
            fatores.append("PA elevada")

        elif classificacao_pa == "hipertensao":
            score += 2
            fatores.append("Hipertensão")

        elif classificacao_pa == "crise_hipertensiva":
            score += 4
            fatores.append("Crise hipertensiva")

    # GLICEMIA
    if glicemia:
        classificacao_glicemia = getattr(
            glicemia,
            "classificacao",
            None
        )

        if classificacao_glicemia == "alterada":
            score += 1
            fatores.append("Glicemia alterada")

        elif classificacao_glicemia == "possivel_diabetes":
            score += 3
            fatores.append("Possível diabetes")

    # BIOIMPEDÂNCIA
    if bio:
        risco_cardiometabolico = getattr(
            bio,
            "risco_cardiometabolico",
            None
        )

        gordura_visceral = getattr(
            bio,
            "gordura_visceral",
            0
        ) or 0

        imc = getattr(bio, "imc", 0) or 0

        if risco_cardiometabolico == "moderado":
            score += 1
            fatores.append("Risco cardiometabólico moderado")

        elif risco_cardiometabolico == "alto":
            score += 3
            fatores.append("Risco cardiometabólico alto")

        if gordura_visceral >= 15:
            score += 2
            fatores.append("Gordura visceral elevada")

        if imc >= 35:
            score += 2
            fatores.append("Obesidade importante")

    # PICO DE FLUXO
    if pico:
        classificacao_pico = getattr(
            pico,
            "classificacao",
            None
        )

        if classificacao_pico == "zona_amarela":
            score += 1
            fatores.append("Pico de fluxo reduzido")

        elif classificacao_pico == "zona_vermelha":
            score += 3
            fatores.append("Pico de fluxo crítico")

    # REINCIDÊNCIA
    if reincidencia_alertas >= 3:
        score += 2
        fatores.append("Reincidência de alertas")

    # ADESÃO
    if adesao == "baixa":
        score += 2
        fatores.append("Baixa adesão")

    elif adesao == "moderada":
        score += 1
        fatores.append("Adesão moderada")

    # CLASSIFICAÇÃO FINAL
    if score <= 1:
        risco = "baixo"

    elif score <= 3:
        risco = "moderado"

    elif score <= 6:
        risco = "alto"

    else:
        risco = "muito_alto"

    return {
        "risco": risco,
        "score": score,
        "fatores": fatores,
    }

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

def gerar_alertas_renovacao_laudo(
    db: Session
):
    hoje = date.today()
    criados = 0
    atualizados = 0

    eventos = db.query(AgendaIntegrada).filter(
        AgendaIntegrada.servico_origem == "dispensacao",
        AgendaIntegrada.data_fim_vigencia.isnot(None),
        AgendaIntegrada.renovado == False
    ).all()

    for evento in eventos:
        dias_para_vencimento = (evento.data_fim_vigencia - hoje).days

        if dias_para_vencimento < 0:
            continue

        novo_status = None

        dias_alerta_renovacao = obter_configuracao_int(
            db,
            "dias_alerta_renovacao",
            60
        )

        dias_alerta_urgente = obter_configuracao_int(
            db,
            "dias_alerta_urgente",
            30
        )

        if dias_alerta_urgente < dias_para_vencimento <= dias_alerta_renovacao:
            novo_status = "renovacao_recomendada"

        elif 0 <= dias_para_vencimento <= dias_alerta_urgente:
            novo_status = "renovacao_urgente"

        if not novo_status:
            continue

        alerta_existente = db.query(AgendaIntegrada).filter(
            AgendaIntegrada.servico_origem == "renovacao_laudo",
            AgendaIntegrada.paciente_nome == evento.paciente_nome,
            AgendaIntegrada.medicamento == evento.medicamento,
            AgendaIntegrada.data_fim_vigencia == evento.data_fim_vigencia,
            AgendaIntegrada.status.in_([
                "renovacao_recomendada",
                "renovacao_urgente"
            ])
        ).first()

        if alerta_existente:
            if alerta_existente.status != novo_status:
                alerta_existente.status = novo_status
                alerta_existente.data_status = datetime.utcnow()
                alerta_existente.usuario_status = "sistema"
                alerta_existente.atualizado_em = datetime.utcnow()
                atualizados += 1

            continue

        novo_alerta = AgendaIntegrada(
            evento_pai_id=evento.id,
            servico_origem="renovacao_laudo",
            tipo_evento="renovacao_laudo",
            paciente_id=evento.paciente_id,
            paciente_nome=evento.paciente_nome,
            telefone=evento.telefone,
            medicamento=evento.medicamento,
            data_evento=hoje,
            data_inicio_vigencia=evento.data_inicio_vigencia,
            data_fim_vigencia=evento.data_fim_vigencia,
            situacao_laudo=evento.situacao_laudo,
            status=novo_status,
            data_status=datetime.utcnow(),
            usuario_status="sistema",
            notificar_whatsapp=True,
            observacoes=(
                f"Alerta automático de renovação gerado. "
                f"Vigência do laudo até {evento.data_fim_vigencia.strftime('%d/%m/%Y')}."
            )
        )

        db.add(novo_alerta)
        criados += 1

    db.commit()

    return {
        "mensagem": "Verificação de renovação de laudos concluída.",
        "alertas_criados": criados,
        "alertas_atualizados": atualizados
    }

def gerar_alertas_risco_interrupcao(
    db: Session
):
    hoje = date.today()
    criados = 0

    dispensacoes_realizadas = db.query(AgendaIntegrada).filter(
        AgendaIntegrada.servico_origem == "dispensacao",
        AgendaIntegrada.status == "realizado",
        AgendaIntegrada.data_fim_vigencia.isnot(None),
        AgendaIntegrada.renovado == False
    ).all()

    for evento in dispensacoes_realizadas:
        dias_para_vencimento = (
            evento.data_fim_vigencia - evento.data_evento
        ).days

        if not (0 <= dias_para_vencimento <= 30):
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
            tipo_evento="risco_interrupcao_tratamento",
            paciente_id=evento.paciente_id,
            paciente_nome=evento.paciente_nome,
            telefone=evento.telefone,
            medicamento=evento.medicamento,
            data_evento=hoje,
            data_inicio_vigencia=evento.data_inicio_vigencia,
            data_fim_vigencia=evento.data_fim_vigencia,
            situacao_laudo="risco_interrupcao_tratamento",
            status="risco_interrupcao_tratamento",
            data_status=datetime.utcnow(),
            usuario_status="sistema",
            notificar_whatsapp=True,
            observacoes=(
                "Alerta automático: dispensação realizada no último mês "
                "de vigência do laudo, sem renovação registrada."
            )
        )

        db.add(alerta)
        criados += 1

    db.commit()

    return {
        "mensagem": "Verificação de risco de interrupção concluída.",
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

def registrar_auditoria(
    db: Session,
    current,
    modulo: str,
    acao: str,
    registro_id: Optional[int] = None,
    descricao: Optional[str] = None
):
    usuario = (
        getattr(current, "nome", None)
        or getattr(current, "email", None)
        or "sistema"
    )

    auditoria = AuditoriaSistema(
        usuario=usuario,
        modulo=modulo,
        acao=acao,
        registro_id=registro_id,
        descricao=descricao,
        criado_em=datetime.utcnow()
    )

    db.add(auditoria)


def obter_configuracao(db: Session, chave: str, valor_padrao=None):
    config = db.query(ConfiguracaoSistema).filter(
        ConfiguracaoSistema.chave == chave
    ).first()

    if not config:
        return valor_padrao

    return config.valor


def obter_configuracao_int(db: Session, chave: str, valor_padrao: int):
    valor = obter_configuracao(db, chave, valor_padrao)

    try:
        return int(valor)
    except Exception:
        return valor_padrao


def criar_configuracoes_padrao(db: Session):
    configuracoes = [
        ("dias_alerta_renovacao", "60", "Dias antes do vencimento do laudo para alerta de renovação recomendada."),
        ("dias_alerta_urgente", "30", "Dias antes do vencimento do laudo para alerta urgente."),
        ("dias_alerta_disp_atrasada", "5", "Dias de atraso para reforço de alerta de dispensação."),
        ("whatsapp_habilitado", "false", "Habilita ou desabilita envio real via WhatsApp."),
    ]

    for chave, valor, descricao in configuracoes:
        existente = db.query(ConfiguracaoSistema).filter(
            ConfiguracaoSistema.chave == chave
        ).first()

        if not existente:
            db.add(ConfiguracaoSistema(
                chave=chave,
                valor=valor,
                descricao=descricao,
                atualizado_em=datetime.utcnow()
            ))

@router.get("/configuracoes")
def listar_configuracoes_sistema(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    criar_configuracoes_padrao(db)
    db.commit()

    configuracoes = db.query(ConfiguracaoSistema).order_by(
        ConfiguracaoSistema.chave.asc()
    ).all()

    return {
        "total": len(configuracoes),
        "configuracoes": configuracoes
    }

@router.get("/me")
def consultorio_me(
    current: UserConsultorio = Depends(get_current_user_consultorio)
):
    return {
        "id": current.id,
        "nome": current.nome,
        "email": current.email,
        "perfil": current.perfil,
        "categoria_profissional": current.categoria_profissional
    }


@router.get("/atendimento-rapido/{atendimento_id}/declaracao-pdf")
def gerar_declaracao_pdf(
    atendimento_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    atendimento = db.query(AtendimentoRapido).filter(
        AtendimentoRapido.id == atendimento_id
    ).first()

    if not atendimento:
        raise HTTPException(
            status_code=404,
            detail="Atendimento não encontrado"
        )

    paciente = db.query(PacienteSimplificado).filter(
        PacienteSimplificado.id == atendimento.paciente_simplificado_id
    ).first()

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    elementos = []

    elementos.append(
        Paragraph(
            "FARMÁCIA ESCOLA PROFª ANA MARIA CERVANTES BARAZA",
            styles["Title"]
        )
    )

    elementos.append(
        Paragraph(
            "Universidade Federal de Mato Grosso do Sul",
            styles["Normal"]
        )
    )

    elementos.append(Spacer(1, 18))

    elementos.append(
        Paragraph(
            "DECLARAÇÃO DE ATENDIMENTO",
            styles["Heading1"]
        )
    )

    elementos.append(Spacer(1, 20))

    nome_paciente = getattr(paciente, "nome", "Paciente")
    data_atendimento = (
        atendimento.data_atendimento.strftime("%d/%m/%Y")
        if atendimento.data_atendimento
        else "Não informada"
    )

    texto = f"""
    Declaramos para os devidos fins que o(a) paciente
    <b>{nome_paciente}</b>
    foi atendido(a) na Farmácia Escola Profª Ana Maria Cervantes Baraza,
    em {data_atendimento},
    referente ao serviço de
    <b>{atendimento.tipo_servico}</b>.
    """

    elementos.append(
        Paragraph(texto, styles["BodyText"])
    )

    elementos.append(Spacer(1, 40))

    if atendimento.observacoes:
        elementos.append(
            Paragraph(
                "<b>Observações:</b>",
                styles["Heading3"]
            )
        )

        elementos.append(
            Paragraph(
                atendimento.observacoes,
                styles["BodyText"]
            )
        )

        elementos.append(Spacer(1, 30))

    nome_profissional = getattr(
        current,
        "nome",
        "Farmacêutico responsável"
    )

    categoria = getattr(
        current,
        "categoria_profissional",
        "Farmacêutico"
    )

    crf = getattr(current, "crf", None)

    elementos.append(Spacer(1, 60))

    assinatura = [
        ["________________________________________"],
        [nome_profissional],
        [categoria],
        [crf if crf else "CRF: __________________"],
    ]

    tabela_assinatura = Table(
        assinatura,
        colWidths=[420]
    )

    tabela_assinatura.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 1), (0, 1), "Helvetica-Bold"),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))

    elementos.append(tabela_assinatura)

    doc.build(elementos)

    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition":
            "inline; filename=declaracao_atendimento.pdf"
        }
    )

@router.get("/dashboard-servicos")
def dashboard_servicos(
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    tipo_servico: Optional[str] = None,
    sexo: Optional[str] = None,
    bairro: Optional[str] = None,
    idade_min: Optional[int] = None,
    idade_max: Optional[int] = None,
    somente_risco: bool = False,
    db: Session = Depends(get_db_consultorio)
):
      
    query_atendimentos = db.query(AtendimentoRapido).join(
        PacienteSimplificado,
        PacienteSimplificado.id == AtendimentoRapido.paciente_simplificado_id
    )

    query_atendimentos = aplicar_filtros_atendimento(
        query_atendimentos,
        data_inicio,
        data_fim,
        tipo_servico,
        sexo,
        bairro,
        idade_min,
        idade_max
    )

    atendimentos_filtrados = query_atendimentos.all()
    ids_atendimentos = [a.id for a in atendimentos_filtrados]

    if not ids_atendimentos:
        return dashboard_vazio()

    total_atendimentos = len(ids_atendimentos)

    por_tipo = {}
    for atendimento in atendimentos_filtrados:
        tipo = atendimento.tipo_servico or "nao_informado"
        por_tipo[tipo] = por_tipo.get(tipo, 0) + 1

    query_pa = db.query(AfericaoPA).filter(AfericaoPA.atendimento_rapido_id.in_(ids_atendimentos))
    query_glicemia = db.query(GlicemiaCapilar).filter(GlicemiaCapilar.atendimento_rapido_id.in_(ids_atendimentos))
    query_bio = db.query(Bioimpedancia).filter(Bioimpedancia.atendimento_rapido_id.in_(ids_atendimentos))
    query_pico = db.query(PicoFluxo).filter(PicoFluxo.atendimento_rapido_id.in_(ids_atendimentos))

    if somente_risco:
        query_pa = query_pa.filter(AfericaoPA.classificacao.in_(["pa_elevada", "hipertensao", "crise_hipertensiva"]))
        query_glicemia = query_glicemia.filter(GlicemiaCapilar.classificacao.in_(["alterada", "possivel_diabetes"]))
        query_bio = query_bio.filter(Bioimpedancia.classificacao.in_(["sobrepeso", "obesidade_grau_1", "obesidade_grau_2", "obesidade_grau_3"]))
        query_pico = query_pico.filter(PicoFluxo.classificacao.in_(["zona_amarela", "zona_vermelha"]))

    pa_total = query_pa.count()
    pa_alterada = query_pa.filter(AfericaoPA.classificacao.in_(["pa_elevada", "hipertensao", "crise_hipertensiva"])).count()

    glicemia_total = query_glicemia.count()
    glicemia_alterada = query_glicemia.filter(GlicemiaCapilar.classificacao.in_(["alterada", "possivel_diabetes"])).count()

    bio_total = query_bio.count()
    bio_risco = query_bio.filter(Bioimpedancia.classificacao.in_(["sobrepeso", "obesidade_grau_1", "obesidade_grau_2", "obesidade_grau_3"])).count()

    pico_total = query_pico.count()
    pico_risco = query_pico.filter(PicoFluxo.classificacao.in_(["zona_amarela", "zona_vermelha"])).count()

    total_procedimentos = pa_total + glicemia_total + bio_total + pico_total

    return {
        "filtros_aplicados": {
            "data_inicio": data_inicio,
            "data_fim": data_fim,
            "tipo_servico": tipo_servico,
            "sexo": sexo,
            "bairro": bairro,
            "idade_min": idade_min,
            "idade_max": idade_max,
            "somente_risco": somente_risco
        },
        "total_atendimentos_rapidos": total_atendimentos,
        "total_procedimentos": total_procedimentos,
        "por_tipo_servico": por_tipo,
        "pressao_arterial": {
            "total": pa_total,
            "alterados": pa_alterada,
            "percentual_alterados": calcular_percentual(pa_alterada, pa_total)
        },
        "glicemia": {
            "total": glicemia_total,
            "alterados": glicemia_alterada,
            "percentual_alterados": calcular_percentual(glicemia_alterada, glicemia_total)
        },
        "bioimpedancia": {
            "total": bio_total,
            "risco": bio_risco,
            "percentual_risco": calcular_percentual(bio_risco, bio_total)
        },
        "pico_fluxo": {
            "total": pico_total,
            "risco": pico_risco,
            "percentual_risco": calcular_percentual(pico_risco, pico_total)
        },
        "alertas": {
            "pa_alterada": pa_alterada,
            "glicemia_alterada": glicemia_alterada,
            "bioimpedancia_risco": bio_risco,
            "pico_fluxo_risco": pico_risco,
            "total_alertas": pa_alterada + glicemia_alterada + bio_risco + pico_risco
        }
    }    


@router.get("/dashboard-serie-temporal")
def dashboard_serie_temporal(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    series = defaultdict(lambda: {
        "atendimentos": 0,
        "pa_alterada": 0,
        "glicemia_alterada": 0,
        "bioimpedancia_risco": 0,
        "pico_fluxo_risco": 0,
        "alertas_resolvidos": 0,
    })

    atendimentos = db.query(AtendimentoRapido).all()

    for a in atendimentos:
        if not a.data_atendimento:
            continue

        mes = a.data_atendimento.strftime("%Y-%m")
        series[mes]["atendimentos"] += 1

        pa = db.query(AfericaoPA).filter(
            AfericaoPA.atendimento_rapido_id == a.id
        ).first()

        if pa and pa.classificacao in [
            "pa_elevada",
            "hipertensao",
            "crise_hipertensiva"
        ]:
            series[mes]["pa_alterada"] += 1

        glicemia = db.query(GlicemiaCapilar).filter(
            GlicemiaCapilar.atendimento_rapido_id == a.id
        ).first()

        if glicemia and glicemia.classificacao in [
            "alterada",
            "possivel_diabetes"
        ]:
            series[mes]["glicemia_alterada"] += 1

        bio = db.query(Bioimpedancia).filter(
            Bioimpedancia.atendimento_rapido_id == a.id
        ).first()

        if bio and (
            bio.risco_cardiometabolico in ["moderado", "alto"]
            or bio.classificacao in [
                "sobrepeso",
                "obesidade_grau_1",
                "obesidade_grau_2",
                "obesidade_grau_3"
            ]
        ):
            series[mes]["bioimpedancia_risco"] += 1

        pico = db.query(PicoFluxo).filter(
            PicoFluxo.atendimento_rapido_id == a.id
        ).first()

        if pico and pico.classificacao in [
            "zona_amarela",
            "zona_vermelha"
        ]:
            series[mes]["pico_fluxo_risco"] += 1

    resolucoes = db.query(ResolucaoAlertaClinico).all()

    for r in resolucoes:
        if not r.resolvido_em:
            continue

        mes = r.resolvido_em.strftime("%Y-%m")
        series[mes]["alertas_resolvidos"] += 1

    resultado = []

    for mes in sorted(series.keys()):
        item = series[mes]

        total_alteracoes = (
            item["pa_alterada"]
            + item["glicemia_alterada"]
            + item["bioimpedancia_risco"]
            + item["pico_fluxo_risco"]
        )

        taxa_resolucao = (
            round(
                (item["alertas_resolvidos"] / total_alteracoes) * 100,
                2
            )
            if total_alteracoes > 0
            else 0
        )

        resultado.append({
            "mes": mes,
            "atendimentos": item["atendimentos"],
            "pa_alterada": item["pa_alterada"],
            "glicemia_alterada": item["glicemia_alterada"],
            "bioimpedancia_risco": item["bioimpedancia_risco"],
            "pico_fluxo_risco": item["pico_fluxo_risco"],
            "total_alteracoes": total_alteracoes,
            "alertas_resolvidos": item["alertas_resolvidos"],
            "taxa_resolucao": taxa_resolucao,
        })

    return resultado

@router.get("/classificacao-risco-populacional")
def classificacao_risco_populacional(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    pacientes = db.query(PacienteSimplificado).all()

    resultado = []

    for paciente in pacientes:
        atendimentos = db.query(AtendimentoRapido).filter(
            AtendimentoRapido.paciente_simplificado_id == paciente.id
        ).order_by(
            AtendimentoRapido.data_atendimento.desc()
        ).all()

        if not atendimentos:
            continue

        ultimo = atendimentos[0]

        pa = db.query(AfericaoPA).filter(
            AfericaoPA.atendimento_rapido_id == ultimo.id
        ).first()

        glicemia = db.query(GlicemiaCapilar).filter(
            GlicemiaCapilar.atendimento_rapido_id == ultimo.id
        ).first()

        bio = db.query(Bioimpedancia).filter(
            Bioimpedancia.atendimento_rapido_id == ultimo.id
        ).first()

        pico = db.query(PicoFluxo).filter(
            PicoFluxo.atendimento_rapido_id == ultimo.id
        ).first()

        reincidencia = max(len(atendimentos) - 1, 0)

        classificacao = calcular_risco_populacional(
            pa=pa,
            glicemia=glicemia,
            bio=bio,
            pico=pico,
            reincidencia_alertas=reincidencia,
        )

        resultado.append({
            "paciente_id": paciente.id,
            "nome": paciente.nome,
            "idade": paciente.idade,
            "sexo": paciente.sexo,

            "risco": classificacao["risco"],
            "score": classificacao["score"],
            "fatores": classificacao["fatores"],

            "ultimo_atendimento":
                ultimo.data_atendimento,

            "reincidencia_alertas":
                reincidencia,
        })

    ordem = {
        "muito_alto": 4,
        "alto": 3,
        "moderado": 2,
        "baixo": 1,
    }

    resultado = sorted(
        resultado,
        key=lambda x: (
            ordem.get(x["risco"], 0),
            x["score"]
        ),
        reverse=True
    )

    resumo = {
        "baixo": 0,
        "moderado": 0,
        "alto": 0,
        "muito_alto": 0,
    }

    for r in resultado:
        resumo[r["risco"]] += 1

    return {
        "total_pacientes": len(resultado),
        "resumo": resumo,
        "pacientes": resultado,
    }

@router.get("/triagem-risco")
def triagem_risco(
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    db: Session = Depends(get_db_consultorio)
):
    query_atendimentos = db.query(AtendimentoRapido).join(
        PacienteSimplificado,
        PacienteSimplificado.id == AtendimentoRapido.paciente_simplificado_id
    )

    if data_inicio:
        query_atendimentos = query_atendimentos.filter(
            AtendimentoRapido.data_atendimento >= data_inicio
        )

    if data_fim:
        query_atendimentos = query_atendimentos.filter(
            AtendimentoRapido.data_atendimento <= data_fim
        )

    atendimentos = query_atendimentos.order_by(
        AtendimentoRapido.data_atendimento.desc()
    ).all()

    pacientes_em_risco = []

    for atendimento in atendimentos:
        paciente = db.query(PacienteSimplificado).filter(
            PacienteSimplificado.id == atendimento.paciente_simplificado_id
        ).first()

        riscos = []

        pa = db.query(AfericaoPA).filter(
            AfericaoPA.atendimento_rapido_id == atendimento.id
        ).first()

        if pa and pa.classificacao in ["pa_elevada", "hipertensao", "crise_hipertensiva"]:
            riscos.append(f"Pressão arterial: {pa.classificacao}")

        glicemia = db.query(GlicemiaCapilar).filter(
            GlicemiaCapilar.atendimento_rapido_id == atendimento.id
        ).first()

        if glicemia and glicemia.classificacao in ["alterada", "possivel_diabetes"]:
            riscos.append(f"Glicemia: {glicemia.classificacao}")

        bio = db.query(Bioimpedancia).filter(
            Bioimpedancia.atendimento_rapido_id == atendimento.id
        ).first()

        if bio and bio.classificacao in [
            "sobrepeso",
            "obesidade_grau_1",
            "obesidade_grau_2",
            "obesidade_grau_3"
        ]:
            riscos.append(f"Bioimpedância/IMC: {bio.classificacao}")

        pico = db.query(PicoFluxo).filter(
            PicoFluxo.atendimento_rapido_id == atendimento.id
        ).first()

        if pico and pico.classificacao in ["zona_amarela", "zona_vermelha"]:
            riscos.append(f"Pico de fluxo: {pico.classificacao}")

        if riscos:
            prioridade = definir_prioridade(riscos)

            pacientes_em_risco.append({
                "paciente_id": paciente.id if paciente else None,
                "nome": paciente.nome if paciente else "Não informado",
                "idade": paciente.idade if paciente else None,
                "sexo": paciente.sexo if paciente else None,
                "bairro": paciente.bairro if paciente else None,
                "atendimento_id": atendimento.id,
                "data_atendimento": atendimento.data_atendimento,
                "tipo_servico": atendimento.tipo_servico,
                "riscos": riscos,
                "quantidade_riscos": len(riscos),
                "prioridade": prioridade,
                "sugestao": gerar_sugestao_conduta(prioridade)
            })

    return {
        "total_pacientes_risco": len(pacientes_em_risco),
        "pacientes": pacientes_em_risco
    }

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
    db.flush()
    db.refresh(agenda)

    registrar_auditoria(
        db=db,
        current=current,
        modulo="agenda",
        acao="criacao",
        registro_id=agenda.id,
        descricao=f"Evento criado para {agenda.paciente_nome}"
    )

    db.commit()
    db.refresh(agenda)

    return {
        "mensagem": "Agendamento criado com sucesso.",
        "agenda": agenda,
        "alerta_capacidade": alerta_capacidade
    }

@router.get("/agenda")
def listar_agenda(
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    query = db.query(AgendaIntegrada)

    if data_inicio:
        query = query.filter(
            AgendaIntegrada.data_evento >= data_inicio
        )

    if data_fim:
        query = query.filter(
            AgendaIntegrada.data_evento <= data_fim
        )

    if status:
        query = query.filter(
            AgendaIntegrada.status == status
        )

    eventos = query.order_by(
        AgendaIntegrada.data_evento.asc()
    ).all()

    return {
        "total": len(eventos),
        "eventos": eventos
    }

@router.get("/agenda/{agenda_id}/relacionados")
def buscar_eventos_relacionados(
    agenda_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    evento = db.query(AgendaIntegrada).filter(
        AgendaIntegrada.id == agenda_id
    ).first()

    if not evento:
        raise HTTPException(
            status_code=404,
            detail="Evento não encontrado"
        )

    relacionados = db.query(AgendaIntegrada).filter(
        AgendaIntegrada.evento_pai_id == agenda_id
    ).all()

    return {
        "evento_principal": evento,
        "relacionados": relacionados
    }

@router.get("/agenda/capacidade")
def listar_capacidade_agenda(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    capacidades = db.query(CapacidadeAgenda).order_by(
        CapacidadeAgenda.servico_origem.asc(),
        CapacidadeAgenda.dia_semana.asc()
    ).all()

    return {
        "total": len(capacidades),
        "capacidades": capacidades
    }

@router.get("/agenda/sugerir-datas")
def sugerir_datas_agenda(
    data_inicial: date,
    servico_origem: str,
    limite_dias: int = 15,
    quantidade_sugestoes: int = 5,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    sugestoes = []

    for i in range(0, limite_dias + 1):
        data_teste = data_inicial + timedelta(days=i)

        capacidade = calcular_capacidade_agenda(
            db=db,
            servico_origem=servico_origem,
            data_evento=data_teste
        )

        if (
            capacidade["capacidade_configurada"]
            and not capacidade["capacidade_atingida"]
        ):
            sugestoes.append({
                "data": data_teste,
                "servico_origem": servico_origem,
                **capacidade
            })

        if len(sugestoes) >= quantidade_sugestoes:
            break

    return {
        "data_inicial": data_inicial,
        "servico_origem": servico_origem,
        "total_sugestoes": len(sugestoes),
        "sugestoes": sugestoes
    }

@router.post("/agenda/capacidade")
def criar_capacidade_agenda(
    dados: CapacidadeAgendaCreate,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    capacidade = CapacidadeAgenda(
        servico_origem=dados.servico_origem,
        dia_semana=dados.dia_semana,
        capacidade_maxima=dados.capacidade_maxima,
        observacoes=dados.observacoes,
        ativo=True,
    )

    db.add(capacidade)
    db.commit()
    db.refresh(capacidade)

    return {
        "mensagem": "Capacidade criada com sucesso.",
        "capacidade": capacidade
    }

@router.put("/agenda/capacidade/{capacidade_id}")
def atualizar_capacidade_agenda(
    capacidade_id: int,
    dados: CapacidadeAgendaUpdate,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    capacidade = db.query(CapacidadeAgenda).filter(
        CapacidadeAgenda.id == capacidade_id
    ).first()

    if not capacidade:
        raise HTTPException(
            status_code=404,
            detail="Configuração de capacidade não encontrada"
        )

    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(capacidade, campo, valor)

    capacidade.atualizado_em = datetime.utcnow()

    db.commit()
    db.refresh(capacidade)

    return {
        "mensagem": "Capacidade atualizada com sucesso.",
        "capacidade": capacidade
    }

@router.get("/agenda/capacidade-dia")
def verificar_capacidade_dia(
    data_evento: date,
    servico_origem: str,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
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

    agendados = db.query(AgendaIntegrada).filter(
        AgendaIntegrada.servico_origem == servico_origem,
        AgendaIntegrada.data_evento == data_evento,
        AgendaIntegrada.status.in_(["agendado", "notificado", "reagendado"])
    ).count()

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
        "data": data_evento,
        "servico_origem": servico_origem,
        "dia_semana": dia_semana,
        "capacidade_configurada": capacidade is not None,
        "capacidade_maxima": capacidade_maxima,
        "agendados": agendados,
        "vagas_disponiveis": vagas_disponiveis,
        "capacidade_atingida": capacidade_atingida
    }

@router.get("/agenda/notificacoes-pendentes")
def notificacoes_pendentes_agenda(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    hoje = date.today()
    notificacoes = []

    eventos = db.query(AgendaIntegrada).filter(
        AgendaIntegrada.notificar_whatsapp == True,
        AgendaIntegrada.status.in_(["agendado", "notificado"])
    ).all()

    for evento in eventos:
        mensagem_base = (
            evento.mensagem_notificacao
            or f"Olá, {evento.paciente_nome}. Este é um lembrete da Farmácia Escola."
        )

        # Consultório, intervenção e dispensação: véspera
        if (
            evento.servico_origem in ["consultorio", "intervencao", "dispensacao"]
            and evento.data_evento
            and (evento.data_evento - hoje).days == 1
            and not evento.notificacao_vespera_enviada
        ):
            notificacoes.append({
                "agenda_id": evento.id,
                "paciente_nome": evento.paciente_nome,
                "telefone": evento.telefone,
                "servico_origem": evento.servico_origem,
                "tipo_evento": evento.tipo_evento,
                "tipo_notificacao": "vespera",
                "mensagem": (
                    f"Olá, {evento.paciente_nome}. Lembramos que você possui "
                    f"um compromisso agendado na Farmácia Escola amanhã "
                    f"({evento.data_evento.strftime('%d/%m/%Y')})."
                )
            })

        # Consultório, intervenção e dispensação: dia do evento
        if (
            evento.servico_origem in ["consultorio", "intervencao", "dispensacao"]
            and evento.data_evento == hoje
            and not evento.notificacao_dia_enviada
        ):
            notificacoes.append({
                "agenda_id": evento.id,
                "paciente_nome": evento.paciente_nome,
                "telefone": evento.telefone,
                "servico_origem": evento.servico_origem,
                "tipo_evento": evento.tipo_evento,
                "tipo_notificacao": "dia_evento",
                "mensagem": (
                    f"Olá, {evento.paciente_nome}. Lembramos que seu compromisso "
                    f"na Farmácia Escola está previsto para hoje."
                )
            })

        # Renovação: penúltimo mês
        if (
            evento.servico_origem == "renovacao_laudo"
            and evento.data_fim_vigencia
            and not evento.renovado
            and not evento.notificacao_penultimo_mes_enviada
        ):
            dias_para_fim = (evento.data_fim_vigencia - hoje).days

            if 31 <= dias_para_fim <= 60:
                notificacoes.append({
                    "agenda_id": evento.id,
                    "paciente_nome": evento.paciente_nome,
                    "telefone": evento.telefone,
                    "servico_origem": evento.servico_origem,
                    "tipo_evento": evento.tipo_evento,
                    "tipo_notificacao": "penultimo_mes_laudo",
                    "mensagem": (
                        f"Olá, {evento.paciente_nome}. Seu laudo possui vigência "
                        f"até {evento.data_fim_vigencia.strftime('%d/%m/%Y')}. "
                        f"Recomendamos iniciar a renovação para evitar interrupção "
                        f"no acesso ao medicamento."
                    )
                })

        # Renovação: último mês
        if (
            evento.servico_origem == "renovacao_laudo"
            and evento.data_fim_vigencia
            and not evento.renovado
            and not evento.notificacao_ultimo_mes_enviada
        ):
            dias_para_fim = (evento.data_fim_vigencia - hoje).days

            if 0 <= dias_para_fim <= 30:
                notificacoes.append({
                    "agenda_id": evento.id,
                    "paciente_nome": evento.paciente_nome,
                    "telefone": evento.telefone,
                    "servico_origem": evento.servico_origem,
                    "tipo_evento": evento.tipo_evento,
                    "tipo_notificacao": "ultimo_mes_laudo",
                    "mensagem": (
                        f"Olá, {evento.paciente_nome}. Atenção: seu laudo vence em "
                        f"{evento.data_fim_vigencia.strftime('%d/%m/%Y')}. "
                        f"Procure a Farmácia Escola para orientação sobre renovação."
                    )
                })

    return {
        "total": len(notificacoes),
        "notificacoes": notificacoes
    }

@router.put("/agenda/{agenda_id}")
def atualizar_agendamento(
    agenda_id: int,
    dados: AgendaIntegradaUpdate,
        db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    agenda = db.query(AgendaIntegrada).filter(
        AgendaIntegrada.id == agenda_id
    ).first()

    if not agenda:
        raise HTTPException(
            status_code=404,
            detail="Agendamento não encontrado"
        )

    for campo, valor in dados.model_dump(
        exclude_unset=True
    ).items():
        setattr(agenda, campo, valor)

    if dados.data_evento and dados.data_evento < date.today():
        raise HTTPException(
            status_code=400,
            detail="Não é permitido reagendar para data passada."
        )    

    agenda.atualizado_em = datetime.utcnow()

    alerta_capacidade = None

    data_para_validar = agenda.data_evento
    servico_para_validar = agenda.servico_origem

    if data_para_validar:
        capacidade = calcular_capacidade_agenda(
            db=db,
            servico_origem=servico_para_validar,
            data_evento=data_para_validar,
            ignorar_agenda_id=agenda.id
        )

        if capacidade["capacidade_atingida"]:
            alerta_capacidade = {
                "warning": True,
                "mensagem": "Capacidade diária atingida para este serviço e data.",
                "capacidade": capacidade
            }

    registrar_auditoria(
        db=db,
        current=current,
        modulo="agenda",
        acao="atualizacao",
        registro_id=agenda.id,
        descricao=f"Agendamento atualizado para {agenda.paciente_nome}"
    )

    db.commit()
    db.refresh(agenda)

    return {
        "mensagem": "Agendamento atualizado.",
        "agenda": agenda,
        "alerta_capacidade": alerta_capacidade
    }

@router.post("/agenda/{agenda_id}/status")
def atualizar_status_agenda(
    agenda_id: int,
    dados: AgendaStatusUpdate,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    agenda = db.query(AgendaIntegrada).filter(
        AgendaIntegrada.id == agenda_id
    ).first()

    if not agenda:
        raise HTTPException(
            status_code=404,
            detail="Agendamento não encontrado"
        )

    agenda.status = dados.status

    agenda.data_status = datetime.utcnow()

    try:
        agenda.usuario_status = getattr(current, "nome", None) or getattr(current, "email", None) or "sistema"
    except: agenda.usuario_status = "sistema"
    if dados.observacoes:
        agenda.observacoes = dados.observacoes

    agenda.atualizado_em = datetime.utcnow()

    proximo_agendamento = None

    servico_normalizado = (agenda.servico_origem or "").strip().lower()
    status_normalizado = (dados.status or "").strip().lower()

    if (
        servico_normalizado in ["dispensacao", "dispensação"]
        and status_normalizado == "realizado"
    ):
        proximo_agendamento = criar_proxima_dispensacao_automatica(
            db=db,
            agenda_atual=agenda
        )

    registrar_auditoria(
        db=db,
        current=current,
        modulo="agenda",
        acao="alteracao_status",
        registro_id=agenda.id,
        descricao=f"Status alterado para {agenda.status} - {agenda.paciente_nome}"
    )

    db.commit()
    db.refresh(agenda)

    return {
        "mensagem": "Status atualizado.",
        "status": agenda.status,
        "proximo_agendamento": (
            {
                "id": proximo_agendamento.id,
                "data_evento": proximo_agendamento.data_evento,
                "medicamento": proximo_agendamento.medicamento,
                "origem": getattr(proximo_agendamento, "_origem_automacao", "indefinida")
            }
            if proximo_agendamento
            else None
        ),
        "data_status": agenda.data_status,
        "usuario_status": agenda.usuario_status,
    }

@router.get("/agenda-retornos")
def agenda_retornos(
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    somente_pendentes: bool = True,
    db: Session = Depends(get_db_consultorio)
):
    query = db.query(EvolucaoClinica).filter(
        EvolucaoClinica.necessidade_retorno == True,
        EvolucaoClinica.data_retorno_sugerida.isnot(None)
    )

    if data_inicio:
        query = query.filter(EvolucaoClinica.data_retorno_sugerida >= data_inicio)

    if data_fim:
        query = query.filter(EvolucaoClinica.data_retorno_sugerida <= data_fim)

    evolucoes = query.order_by(
        EvolucaoClinica.data_retorno_sugerida.asc()
    ).all()

    retornos = []

    for evolucao in evolucoes:
        prontuario = db.query(ProntuarioClinico).filter(
            ProntuarioClinico.id == evolucao.prontuario_id
        ).first()

        paciente = None
        if prontuario:
            paciente = db.query(PacienteClinico).filter(
                PacienteClinico.id == prontuario.paciente_clinico_id
            ).first()

        desfechos = db.query(DesfechoClinico).filter(
            DesfechoClinico.evolucao_id == evolucao.id
        ).all()

        retorno_concluido = len(desfechos) > 0

        if somente_pendentes and retorno_concluido:
            continue

        retornos.append({
            "evolucao_id": evolucao.id,
            "prontuario_id": evolucao.prontuario_id,
            "paciente_id": paciente.id if paciente else None,
            "paciente_nome": paciente.nome if paciente else "Não informado",
            "telefone": paciente.telefone if paciente else None,
            "bairro": paciente.bairro if paciente else None,
            "data_retorno_sugerida": evolucao.data_retorno_sugerida,
            "tipo_atendimento": evolucao.tipo_atendimento,
            "plano_acompanhamento": evolucao.plano_acompanhamento,
            "retorno_concluido": retorno_concluido
        })

    return {
        "total": len(retornos),
        "somente_pendentes": somente_pendentes,
        "retornos": retornos
    }

@router.post("/agenda/gerar-alertas-renovacao")
def executar_alertas_renovacao_laudo(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    resultado = gerar_alertas_renovacao_laudo(db)

    return resultado

@router.post("/agenda/gerar-alertas-risco-interrupcao")
def executar_alertas_risco_interrupcao(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    return gerar_alertas_risco_interrupcao(db)

@router.get("/agenda/painel-pendencias")
def painel_pendencias_agenda(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    hoje = date.today()
    amanha = hoje + timedelta(days=1)

    risco_interrupcao = db.query(AgendaIntegrada).filter(
        AgendaIntegrada.status == "risco_interrupcao_tratamento"
    ).count()

    renovacoes_urgentes = db.query(AgendaIntegrada).filter(
        AgendaIntegrada.status == "renovacao_urgente"
    ).count()

    renovacoes_recomendadas = db.query(AgendaIntegrada).filter(
        AgendaIntegrada.status == "renovacao_recomendada"
    ).count()

    dispensacoes_atrasadas = db.query(AgendaIntegrada).filter(
        AgendaIntegrada.servico_origem == "dispensacao",
        AgendaIntegrada.status.in_(["agendado", "notificado", "reagendado"]),
        AgendaIntegrada.data_evento < hoje
    ).count()

    dispensacoes_amanha = db.query(AgendaIntegrada).filter(
        AgendaIntegrada.servico_origem == "dispensacao",
        AgendaIntegrada.status == "agendado",
        AgendaIntegrada.data_evento == amanha
    ).count()

    notificacoes_pendentes = db.query(NotificacaoAgenda).filter(
        NotificacaoAgenda.status == "pendente"
    ).count()

    total_critico = (
        risco_interrupcao
        + renovacoes_urgentes
        + dispensacoes_atrasadas
    )

    return {
        "resumo": {
            "risco_interrupcao": risco_interrupcao,
            "renovacoes_urgentes": renovacoes_urgentes,
            "renovacoes_recomendadas": renovacoes_recomendadas,
            "dispensacoes_atrasadas": dispensacoes_atrasadas,
            "dispensacoes_amanha": dispensacoes_amanha,
            "notificacoes_pendentes": notificacoes_pendentes,
            "total_critico": total_critico,
        }
    }


# Rota migrada para routers/pacientes.py removida no pacote 5B: linhas originais 4087-4124


# Rota migrada para routers/pacientes.py removida no pacote 5B: linhas originais 4125-4144


# Rota migrada para routers/pacientes.py removida no pacote 5B: linhas originais 4145-4177


# Rota migrada para routers/pacientes.py removida no pacote 5B: linhas originais 4178-4207


# Rota migrada para routers/pacientes.py removida no pacote 5B: linhas originais 4208-4238


# Rota migrada para routers/pacientes.py removida no pacote 5B: linhas originais 4239-4258


# Rota migrada para routers/pacientes.py removida no pacote 5B: linhas originais 4259-4325


# Rota migrada para routers/pacientes.py removida no pacote 5B: linhas originais 4326-4568



@router.get("/evolucao-risco-populacional")
def evolucao_risco_populacional(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    pacientes = db.query(PacienteSimplificado).all()

    resultado = []

    ordem_risco = {
        "baixo": 1,
        "moderado": 2,
        "alto": 3,
        "muito_alto": 4,
    }

    for paciente in pacientes:
        atendimentos = db.query(AtendimentoRapido).filter(
            AtendimentoRapido.paciente_simplificado_id == paciente.id
        ).order_by(
            AtendimentoRapido.data_atendimento.asc()
        ).all()

        if len(atendimentos) < 2:
            continue

        def gerar_classificacao(atendimento):
            pa = db.query(AfericaoPA).filter(
                AfericaoPA.atendimento_rapido_id == atendimento.id
            ).first()

            glicemia = db.query(GlicemiaCapilar).filter(
                GlicemiaCapilar.atendimento_rapido_id == atendimento.id
            ).first()

            bio = db.query(Bioimpedancia).filter(
                Bioimpedancia.atendimento_rapido_id == atendimento.id
            ).first()

            pico = db.query(PicoFluxo).filter(
                PicoFluxo.atendimento_rapido_id == atendimento.id
            ).first()

            return calcular_risco_populacional(
                pa=pa,
                glicemia=glicemia,
                bio=bio,
                pico=pico,
                reincidencia_alertas=max(
                    len(atendimentos) - 1,
                    0
                )
            )

        primeiro = gerar_classificacao(atendimentos[0])
        ultimo = gerar_classificacao(atendimentos[-1])

        score_inicial = primeiro["score"]
        score_atual = ultimo["score"]

        diferenca = score_atual - score_inicial

        if diferenca <= -2:
            tendencia = "melhora"

        elif diferenca >= 2:
            tendencia = "piora"

        else:
            tendencia = "estabilidade"

        resultado.append({
            "paciente_id": paciente.id,
            "nome": paciente.nome,

            "risco_inicial": primeiro["risco"],
            "score_inicial": score_inicial,

            "risco_atual": ultimo["risco"],
            "score_atual": score_atual,

            "diferenca_score": diferenca,

            "tendencia": tendencia,

            "fatores_atuais": ultimo["fatores"],

            "total_atendimentos":
                len(atendimentos),

            "primeiro_atendimento":
                atendimentos[0].data_atendimento,

            "ultimo_atendimento":
                atendimentos[-1].data_atendimento,
        })

    resumo = {
        "melhora": 0,
        "estabilidade": 0,
        "piora": 0,
    }

    for r in resultado:
        resumo[r["tendencia"]] += 1

    resultado = sorted(
        resultado,
        key=lambda x: (
            ordem_risco.get(x["risco_atual"], 0),
            x["score_atual"]
        ),
        reverse=True
    )

    return {
        "total_pacientes": len(resultado),
        "resumo": resumo,
        "pacientes": resultado,
    }


def historico_bioimpedancia_paciente(
    paciente_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    paciente = db.query(PacienteSimplificado).filter(
        PacienteSimplificado.id == paciente_id
    ).first()

    if not paciente:
        raise HTTPException(
            status_code=404,
            detail="Paciente simplificado não encontrado"
        )

    atendimentos = db.query(AtendimentoRapido).filter(
        AtendimentoRapido.paciente_simplificado_id == paciente_id
    ).order_by(
        AtendimentoRapido.data_atendimento.asc()
    ).all()

    historico = []

    for atendimento in atendimentos:
        bio = db.query(Bioimpedancia).filter(
            Bioimpedancia.atendimento_rapido_id == atendimento.id
        ).first()

        if not bio:
            continue

        historico.append({
            "atendimento_id": atendimento.id,
            "data": atendimento.data_atendimento,
            "peso": getattr(bio, "peso", None),
            "altura": getattr(bio, "altura", None),
            "imc": getattr(bio, "imc", None),
            "classificacao_imc": getattr(bio, "classificacao_imc", None),
            "percentual_gordura": getattr(bio, "percentual_gordura", None),
            "percentual_massa_muscular": getattr(bio, "percentual_massa_muscular", None),
            "gordura_visceral": getattr(bio, "gordura_visceral", None),
            "classificacao_gordura_visceral": getattr(
                bio,
                "classificacao_gordura_visceral",
                None
            ),
            "fmi": getattr(bio, "fmi", None),
            "ffmi": getattr(bio, "ffmi", None),
            "relacao_gordura_musculo": getattr(
                bio,
                "relacao_gordura_musculo",
                None
            ),
            "metabolismo_basal": getattr(bio, "metabolismo_basal", None),
            "idade_corporal": getattr(bio, "idade_corporal", None),
            "observacoes": getattr(bio, "observacoes", None),
        })

    return {
        "paciente": {
            "id": paciente.id,
            "nome": paciente.nome,
            "idade": paciente.idade,
            "sexo": paciente.sexo,
            "bairro": paciente.bairro,
        },
        "total_avaliacoes": len(historico),
        "historico": historico
    }


def laudo_bioimpedancia_pdf(
    bioimpedancia_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    bio = db.query(Bioimpedancia).filter(
        Bioimpedancia.id == bioimpedancia_id
    ).first()

    if not bio:
        raise HTTPException(
            status_code=404,
            detail="Registro de bioimpedância não encontrado"
        )

    atendimento = db.query(AtendimentoRapido).filter(
        AtendimentoRapido.id == bio.atendimento_rapido_id
    ).first()

    paciente = None

    if atendimento:
        paciente = db.query(PacienteSimplificado).filter(
            PacienteSimplificado.id == atendimento.paciente_simplificado_id
        ).first()

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    elementos = []

    elementos.append(Paragraph("FARMÁCIA ESCOLA", styles["Title"]))
    elementos.append(Paragraph("PROFª ANA MARIA CERVANTES BARAZA", styles["Heading2"]))
    elementos.append(Paragraph("Universidade Federal de Mato Grosso do Sul", styles["Normal"]))
    elementos.append(Spacer(1, 14))

    elementos.append(Paragraph("Laudo de Avaliação por Bioimpedância", styles["Title"]))
    elementos.append(Spacer(1, 12))

    dados_paciente = [
        ["Campo", "Informação"],
        ["Paciente", getattr(paciente, "nome", "Não informado")],
        ["Idade", getattr(paciente, "idade", "Não informada")],
        ["Sexo", getattr(paciente, "sexo", "Não informado")],
        ["Data do atendimento", atendimento.data_atendimento.strftime("%d/%m/%Y") if atendimento and atendimento.data_atendimento else "Não informada"],
    ]

    tabela_paciente = Table(dados_paciente, colWidths=[180, 320])
    tabela_paciente.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0f2f1")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("PADDING", (0, 0), (-1, -1), 7),
    ]))

    elementos.append(tabela_paciente)
    elementos.append(Spacer(1, 16))

    dados_bio = [
        ["Indicador", "Resultado"],
        ["Peso", f"{bio.peso or '—'} kg"],
        ["Altura", f"{bio.altura or '—'} m"],
        ["IMC", f"{bio.imc or '—'}"],
        ["Classificação IMC", bio.classificacao_imc or bio.classificacao or "Sem classificação"],
        ["Gordura corporal", f"{bio.percentual_gordura or '—'} %"],
        ["Massa de gordura", f"{bio.massa_gordura_kg or '—'} kg"],
        ["Massa muscular", f"{bio.percentual_massa_muscular or '—'} %"],
        ["Massa muscular estimada", f"{bio.massa_muscular_kg or '—'} kg"],
        ["Massa magra estimada", f"{bio.massa_magra_kg or '—'} kg"],
        ["Gordura visceral", bio.gordura_visceral or "—"],
        ["Classificação gordura visceral", bio.classificacao_gordura_visceral or "Sem classificação"],
        ["Metabolismo basal", f"{bio.metabolismo_basal or '—'} kcal"],
        ["Fator de atividade", bio.fator_atividade or "—"],
        ["Gasto energético total estimado", f"{bio.gasto_energetico_total or '—'} kcal/dia"],
        ["Idade corporal", bio.idade_corporal or "—"],
        ["Diferença idade corporal", bio.diferenca_idade_corporal or "—"],
        ["FMI", bio.fmi or "—"],
        ["FFMI", bio.ffmi or "—"],
        ["Relação gordura/músculo", bio.relacao_gordura_musculo or "—"],
        ["Risco cardiometabólico", bio.risco_cardiometabolico or "Não classificado"],
    ]

    tabela_bio = Table(dados_bio, colWidths=[240, 260])
    tabela_bio.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#fef3c7")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("PADDING", (0, 0), (-1, -1), 7),
    ]))

    elementos.append(Paragraph("Resultados da Bioimpedância", styles["Heading2"]))
    elementos.append(tabela_bio)
    elementos.append(Spacer(1, 16))

    elementos.append(Paragraph("Interpretação automática", styles["Heading2"]))

    interpretacao = []

    if bio.classificacao_imc:
        interpretacao.append(f"O IMC foi classificado como {bio.classificacao_imc}.")

    if bio.classificacao_gordura_visceral:
        interpretacao.append(
            f"A gordura visceral foi classificada como {bio.classificacao_gordura_visceral}."
        )

    if bio.risco_cardiometabolico:
        interpretacao.append(
            f"O risco cardiometabólico estimado foi classificado como {bio.risco_cardiometabolico}."
        )

    if bio.alertas:
        interpretacao.append(f"Alertas clínicos: {bio.alertas}.")

    if not interpretacao:
        interpretacao.append(
            "Não foram gerados alertas automáticos para este registro."
        )

    for texto in interpretacao:
        elementos.append(Paragraph(texto, styles["Normal"]))
        elementos.append(Spacer(1, 6))

    elementos.append(Spacer(1, 20))

    elementos.append(Paragraph("Observações", styles["Heading2"]))
    elementos.append(Paragraph(bio.observacoes or "Sem observações registradas.", styles["Normal"]))

    elementos.append(Spacer(1, 46))

    nome_profissional = getattr(current, "nome", "Farmacêutico responsável")
    categoria = getattr(current, "categoria_profissional", "Farmacêutico")
    crf = getattr(current, "crf", None) or "CRF: __________________"

    assinatura = [
        ["________________________________________"],
        [nome_profissional],
        [categoria],
        [crf],
    ]

    tabela_assinatura = Table(assinatura, colWidths=[420])
    tabela_assinatura.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 1), (0, 1), "Helvetica-Bold"),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))

    elementos.append(tabela_assinatura)

    doc.build(elementos)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "inline; filename=laudo_bioimpedancia.pdf"
        }
    )

@router.get("/relatorio-mensal")
def relatorio_mensal_consultorio(
    ano: int,
    mes: int,
    db: Session = Depends(get_db_consultorio)
):
    inicio = date(ano, mes, 1)

    if mes == 12:
        fim = date(ano + 1, 1, 1)
    else:
        fim = date(ano, mes + 1, 1)

    atendimentos_rapidos = db.query(AtendimentoRapido).filter(
        AtendimentoRapido.data_atendimento >= inicio,
        AtendimentoRapido.data_atendimento < fim
    ).all()

    ids_atendimentos = [a.id for a in atendimentos_rapidos]

    por_tipo_servico = {}
    for atendimento in atendimentos_rapidos:
        tipo = atendimento.tipo_servico or "nao_informado"
        por_tipo_servico[tipo] = por_tipo_servico.get(tipo, 0) + 1

    pa_total = db.query(AfericaoPA).filter(
        AfericaoPA.atendimento_rapido_id.in_(ids_atendimentos)
    ).count() if ids_atendimentos else 0

    pa_alterada = db.query(AfericaoPA).filter(
        AfericaoPA.atendimento_rapido_id.in_(ids_atendimentos),
        AfericaoPA.classificacao.in_(["pa_elevada", "hipertensao", "crise_hipertensiva"])
    ).count() if ids_atendimentos else 0

    glicemia_total = db.query(GlicemiaCapilar).filter(
        GlicemiaCapilar.atendimento_rapido_id.in_(ids_atendimentos)
    ).count() if ids_atendimentos else 0

    glicemia_alterada = db.query(GlicemiaCapilar).filter(
        GlicemiaCapilar.atendimento_rapido_id.in_(ids_atendimentos),
        GlicemiaCapilar.classificacao.in_(["alterada", "possivel_diabetes"])
    ).count() if ids_atendimentos else 0

    bio_total = db.query(Bioimpedancia).filter(
        Bioimpedancia.atendimento_rapido_id.in_(ids_atendimentos)
    ).count() if ids_atendimentos else 0

    bio_risco = db.query(Bioimpedancia).filter(
        Bioimpedancia.atendimento_rapido_id.in_(ids_atendimentos),
        Bioimpedancia.classificacao.in_([
            "sobrepeso",
            "obesidade_grau_1",
            "obesidade_grau_2",
            "obesidade_grau_3"
        ])
    ).count() if ids_atendimentos else 0

    pico_total = db.query(PicoFluxo).filter(
        PicoFluxo.atendimento_rapido_id.in_(ids_atendimentos)
    ).count() if ids_atendimentos else 0

    pico_risco = db.query(PicoFluxo).filter(
        PicoFluxo.atendimento_rapido_id.in_(ids_atendimentos),
        PicoFluxo.classificacao.in_(["zona_amarela", "zona_vermelha"])
    ).count() if ids_atendimentos else 0

    pacientes_convertidos = db.query(PacienteClinico).filter(
        PacienteClinico.criado_em >= inicio,
        PacienteClinico.criado_em < fim
    ).count()

    evolucoes = db.query(EvolucaoClinica).filter(
        EvolucaoClinica.data_evolucao >= inicio,
        EvolucaoClinica.data_evolucao < fim
    ).count()

    desfechos = db.query(DesfechoClinico).filter(
        DesfechoClinico.data_desfecho >= inicio,
        DesfechoClinico.data_desfecho < fim
    ).all()

    melhora_clinica = {}
    adesao_tratamento = {}

    resolvidos = 0
    encaminhamentos = 0

    for d in desfechos:
        melhora = d.melhora_clinica or "nao_informado"
        adesao = d.adesao_tratamento or "nao_informado"

        melhora_clinica[melhora] = melhora_clinica.get(melhora, 0) + 1
        adesao_tratamento[adesao] = adesao_tratamento.get(adesao, 0) + 1

        if d.resolucao_problema:
            resolvidos += 1

        if d.necessidade_encaminhamento:
            encaminhamentos += 1

    total_procedimentos = pa_total + glicemia_total + bio_total + pico_total
    total_alertas_clinicos = pa_alterada + glicemia_alterada + bio_risco + pico_risco

    return {
        "periodo": {
            "ano": ano,
            "mes": mes,
            "inicio": inicio,
            "fim": fim
        },
        "servicos_rapidos": {
            "total_atendimentos": len(atendimentos_rapidos),
            "total_procedimentos": total_procedimentos,
            "por_tipo_servico": por_tipo_servico,
            "pressao_arterial": {
                "total": pa_total,
                "alteradas": pa_alterada,
                "percentual_alteradas": calcular_percentual(pa_alterada, pa_total)
            },
            "glicemia": {
                "total": glicemia_total,
                "alteradas": glicemia_alterada,
                "percentual_alteradas": calcular_percentual(glicemia_alterada, glicemia_total)
            },
            "bioimpedancia": {
                "total": bio_total,
                "risco": bio_risco,
                "percentual_risco": calcular_percentual(bio_risco, bio_total)
            },
            "pico_fluxo": {
                "total": pico_total,
                "risco": pico_risco,
                "percentual_risco": calcular_percentual(pico_risco, pico_total)
            },
            "total_alertas_clinicos": total_alertas_clinicos
        },
        "consultorio_farmaceutico": {
            "pacientes_convertidos_no_mes": pacientes_convertidos,
            "evolucoes_registradas": evolucoes,
            "desfechos_registrados": len(desfechos),
            "melhora_clinica": melhora_clinica,
            "adesao_tratamento": adesao_tratamento,
            "problemas_resolvidos": resolvidos,
            "percentual_resolucao": calcular_percentual(resolvidos, len(desfechos)),
            "encaminhamentos": encaminhamentos,
            "percentual_encaminhamento": calcular_percentual(encaminhamentos, len(desfechos))
        }
    }

@router.get("/paciente-clinico/{paciente_clinico_id}/pdf")
def gerar_pdf_prontuario(
    paciente_clinico_id: int,
    db: Session = Depends(get_db_consultorio)
):
    paciente = db.query(PacienteClinico).filter(
        PacienteClinico.id == paciente_clinico_id
    ).first()

    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente clínico não encontrado")

    prontuario = db.query(ProntuarioClinico).filter(
        ProntuarioClinico.paciente_clinico_id == paciente.id
    ).first()

    evolucoes = []
    if prontuario:
        evolucoes = db.query(EvolucaoClinica).filter(
            EvolucaoClinica.prontuario_id == prontuario.id
        ).order_by(EvolucaoClinica.data_evolucao.desc()).all()

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    elementos = []

    elementos.append(Paragraph("Prontuário Clínico Farmacêutico", styles["Title"]))
    elementos.append(Spacer(1, 16))

    dados_paciente = [
        ["Nome", paciente.nome or ""],
        ["Idade", str(calcular_idade(paciente.data_nascimento) or "")],
        ["Sexo", paciente.sexo or ""],
        ["Telefone", paciente.telefone or ""],
        ["Bairro", paciente.bairro or ""],
        ["CPF", paciente.cpf or ""],
        ["CNS", paciente.cns or ""],
        ["Origem", paciente.origem or ""],
    ]

    tabela_paciente = Table(dados_paciente, colWidths=[120, 360])
    tabela_paciente.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e0f2f1")),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#064e3b")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))

    elementos.append(tabela_paciente)
    elementos.append(Spacer(1, 18))

    if prontuario:
        elementos.append(Paragraph("Dados do prontuário", styles["Heading2"]))
        elementos.append(Paragraph(f"Status: {prontuario.status or 'Não informado'}", styles["Normal"]))
        elementos.append(Paragraph(f"Abertura: {prontuario.data_abertura}", styles["Normal"]))
        elementos.append(Spacer(1, 14))

    elementos.append(Paragraph("Evoluções clínicas", styles["Heading2"]))
    elementos.append(Spacer(1, 8))

    if not evolucoes:
        elementos.append(Paragraph("Nenhuma evolução registrada.", styles["Normal"]))
    else:
        for evolucao in evolucoes:
            elementos.append(Paragraph(
                f"<b>{evolucao.tipo_atendimento or 'Evolução clínica'}</b>",
                styles["Heading3"]
            ))
            elementos.append(Paragraph(f"Data: {evolucao.data_evolucao}", styles["Normal"]))

            if evolucao.queixa_principal:
                elementos.append(Paragraph(f"<b>Queixa principal:</b> {evolucao.queixa_principal}", styles["Normal"]))

            if evolucao.avaliacao_farmaceutica:
                elementos.append(Paragraph(f"<b>Avaliação farmacêutica:</b> {evolucao.avaliacao_farmaceutica}", styles["Normal"]))

            if evolucao.problemas_identificados:
                elementos.append(Paragraph(f"<b>Problemas identificados:</b> {evolucao.problemas_identificados}", styles["Normal"]))

            if evolucao.conduta:
                elementos.append(Paragraph(f"<b>Conduta:</b> {evolucao.conduta}", styles["Normal"]))

            if evolucao.plano_acompanhamento:
                elementos.append(Paragraph(f"<b>Plano:</b> {evolucao.plano_acompanhamento}", styles["Normal"]))

            desfechos = db.query(DesfechoClinico).filter(
                DesfechoClinico.evolucao_id == evolucao.id
            ).order_by(DesfechoClinico.data_desfecho.desc()).all()

            if desfechos:
                elementos.append(Spacer(1, 6))
                elementos.append(Paragraph("<b>Desfechos:</b>", styles["Normal"]))

                for desfecho in desfechos:
                    texto = (
                        f"Melhora: {desfecho.melhora_clinica or 'não informado'} | "
                        f"Adesão: {desfecho.adesao_tratamento or 'não informado'} | "
                        f"Resolvido: {'Sim' if desfecho.resolucao_problema else 'Não'}"
                    )
                    elementos.append(Paragraph(texto, styles["Normal"]))

                    if desfecho.resultado_observado:
                        elementos.append(Paragraph(
                            f"Resultado observado: {desfecho.resultado_observado}",
                            styles["Normal"]
                        ))

            elementos.append(Spacer(1, 14))

    doc.build(elementos)

    buffer.seek(0)

    nome_arquivo = f"prontuario_paciente_{paciente.id}.pdf"

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename={nome_arquivo}"
        }
    )


@router.get("/paciente-clinico/{paciente_id}/sugestoes-plano-cuidado")
def sugestoes_plano_cuidado(
    paciente_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    paciente = db.query(PacienteClinico).filter(
        PacienteClinico.id == paciente_id
    ).first()

    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente clínico não encontrado")

    achados = []
    pontos_atencao = []
    prioridade = "baixa"

    avaliacao = avaliar_polifarmacia(
        paciente_id=paciente.id,
        db=db,
        current=current
    )

    evolucao = evolucao_farmacoterapeutica(
        paciente_id=paciente.id,
        db=db,
        current=current
    )

    if avaliacao.get("polifarmacia"):
        achados.append(
            f"Polifarmácia ({avaliacao.get('total_medicamentos')} medicamentos ativos)"
        )
        pontos_atencao.append("Avaliar necessidade de revisão farmacoterapêutica.")
        prioridade = "moderada"

    if avaliacao.get("risco") == "alto":
        achados.append("Risco farmacoterapêutico alto.")
        pontos_atencao.append("Priorizar revisão de segurança da farmacoterapia.")
        prioridade = "alta"

    if avaliacao.get("interacoes"):
        achados.append(
            "Possíveis interações relevantes: "
            + ", ".join(avaliacao.get("interacoes"))
        )
        pontos_atencao.append("Avaliar clinicamente possíveis interações medicamentosas.")
        prioridade = "alta"

    if avaliacao.get("duplicidades"):
        achados.append(
            "Possíveis duplicidades terapêuticas: "
            + ", ".join(avaliacao.get("duplicidades"))
        )
        pontos_atencao.append("Avaliar duplicidade terapêutica.")
        prioridade = "alta"

    if evolucao.get("baixa_adesao", 0) > 0:
        achados.append("Baixa adesão registrada.")
        pontos_atencao.append("Investigar barreiras de adesão e pactuar estratégias com o paciente.")
        prioridade = "alta"

    if evolucao.get("total_intervencoes", 0) >= 3:
        achados.append(
            f"{evolucao.get('total_intervencoes')} intervenções farmacoterapêuticas registradas."
        )
        pontos_atencao.append("Reavaliar efetividade das intervenções anteriores.")

    if evolucao.get("encaminhamentos", 0) > 0:
        achados.append("Há necessidade prévia de encaminhamento registrada.")
        pontos_atencao.append("Verificar se o encaminhamento foi realizado e acompanhado.")

    if not achados:
        achados.append("Nenhum achado crítico automático identificado.")
        pontos_atencao.append("Manter avaliação clínica individualizada.")

    return {
        "paciente_id": paciente.id,
        "paciente": paciente.nome,
        "prioridade": prioridade,
        "achados": achados,
        "pontos_atencao": pontos_atencao,
        "observacao": (
            "As sugestões não substituem o julgamento clínico. "
            "Devem ser interpretadas e validadas pelo farmacêutico."
        )
    }    


@router.get("/pacientes-clinicos")
def listar_pacientes_clinicos(
    db: Session = Depends(get_db_consultorio)
):
    pacientes = db.query(PacienteClinico).order_by(
        PacienteClinico.criado_em.desc()
    ).all()

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


@router.get("/relatorio-geral")
def relatorio_geral(
    db: Session = Depends(get_db_consultorio)
):
    total_pacientes = db.query(PacienteClinico).count()
    total_prontuarios = db.query(ProntuarioClinico).count()
    total_evolucoes = db.query(EvolucaoClinica).count()
    total_desfechos = db.query(DesfechoClinico).count()

    return {
        "pacientes_clinicos": total_pacientes,
        "prontuarios": total_prontuarios,
        "evolucoes": total_evolucoes,
        "desfechos": total_desfechos
    }

@router.post("/evolucao-farmaceutica")
def criar_evolucao_farmaceutica(
    dados: EvolucaoFarmaceuticaCreate,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    paciente = db.query(PacienteSimplificado).filter(
        PacienteSimplificado.id == dados.paciente_simplificado_id
    ).first()

    if not paciente:
        raise HTTPException(
            status_code=404,
            detail="Paciente não encontrado"
        )

    evolucao = EvolucaoFarmaceutica(**dados.dict())

    db.add(evolucao)
    db.commit()
    db.refresh(evolucao)

    return {
        "mensagem": "Evolução farmacêutica registrada com sucesso",
        "evolucao_id": evolucao.id
    }

{
  "paciente_simplificado_id": 1,
  "subjetivo": "Paciente relata dificuldade de adesão ao tratamento.",
  "objetivo": "Histórico recente com PA elevada e IMC aumentado.",
  "avaliacao": "Possível baixa adesão e risco cardiometabólico aumentado.",
  "plano": "Orientação farmacêutica, acompanhamento e reavaliação.",
  "prm": "Uso irregular de medicamento.",
  "adesao": "regular",
  "metas_clinicas": "Melhorar adesão e acompanhar PA.",
  "orientacoes": "Orientado sobre uso correto dos medicamentos.",
  "encaminhamento": "",
  "risco_clinico": "moderado",
  "observacoes": "Primeira evolução farmacêutica estruturada."
}

@router.get("/evolucao-farmaceutica/{evolucao_id}/pdf")
def evolucao_farmaceutica_pdf(
    evolucao_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    evolucao = db.query(EvolucaoFarmaceutica).filter(
        EvolucaoFarmaceutica.id == evolucao_id
    ).first()

    if not evolucao:
        raise HTTPException(status_code=404, detail="Evolução não encontrada")

    paciente = db.query(PacienteSimplificado).filter(
        PacienteSimplificado.id == evolucao.paciente_simplificado_id
    ).first()

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    elementos = []

    elementos.append(Paragraph("FARMÁCIA ESCOLA", styles["Title"]))
    elementos.append(Paragraph("Evolução Farmacêutica - Modelo SOAP", styles["Heading1"]))
    elementos.append(Spacer(1, 14))

    dados_paciente = [
        ["Paciente", getattr(paciente, "nome", "Não informado")],
        ["Idade", getattr(paciente, "idade", "Não informada")],
        ["Sexo", getattr(paciente, "sexo", "Não informado")],
        ["Data", evolucao.criado_em.strftime("%d/%m/%Y %H:%M") if evolucao.criado_em else "Não informada"],
    ]

    tabela_paciente = Table(dados_paciente, colWidths=[150, 350])
    tabela_paciente.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("PADDING", (0, 0), (-1, -1), 7),
    ]))

    elementos.append(tabela_paciente)
    elementos.append(Spacer(1, 16))

    secoes = [
        ("S - Subjetivo", evolucao.subjetivo),
        ("O - Objetivo", evolucao.objetivo),
        ("A - Avaliação farmacêutica", evolucao.avaliacao),
        ("P - Plano de cuidado", evolucao.plano),
        ("PRM/RNM", evolucao.prm),
        ("Adesão", evolucao.adesao),
        ("Metas clínicas", evolucao.metas_clinicas),
        ("Orientações", evolucao.orientacoes),
        ("Encaminhamento", evolucao.encaminhamento),
        ("Risco clínico", evolucao.risco_clinico),
        ("Observações", evolucao.observacoes),
    ]

    for titulo, texto in secoes:
        if texto:
            elementos.append(Paragraph(titulo, styles["Heading2"]))
            elementos.append(Paragraph(str(texto), styles["Normal"]))
            elementos.append(Spacer(1, 8))

    elementos.append(Spacer(1, 42))

    nome_profissional = getattr(current, "nome", "Farmacêutico responsável")
    categoria = getattr(current, "categoria_profissional", "Farmacêutico")
    crf = getattr(current, "crf", None) or "CRF: __________________"

    assinatura = [
        ["________________________________________"],
        [nome_profissional],
        [categoria],
        [crf],
    ]

    tabela_assinatura = Table(assinatura, colWidths=[420])
    tabela_assinatura.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 1), (0, 1), "Helvetica-Bold"),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))

    elementos.append(tabela_assinatura)

    doc.build(elementos)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "inline; filename=evolucao_farmaceutica.pdf"
        }
    )

@router.post("/plano-cuidado")
def criar_plano_cuidado(
    dados: PlanoCuidadoCreate,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    exigir_farmaceutico_ou_admin(current)

    paciente = db.query(PacienteClinico).filter(
        PacienteClinico.id == dados.paciente_id
    ).first()

    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente clínico não encontrado")

    plano = PlanoCuidado(
        paciente_id=dados.paciente_id,
        criado_por=getattr(current, "nome", None),
        problema_identificado=dados.problema_identificado,
        objetivo_terapeutico=dados.objetivo_terapeutico,
        intervencoes_planejadas=dados.intervencoes_planejadas,
        prazo_reavaliacao=dados.prazo_reavaliacao,
        observacoes=dados.observacoes,
        status="pendente",
    )

    db.add(plano)
    db.commit()
    db.refresh(plano)
    if plano.prazo_reavaliacao:
        agenda = AgendaIntegrada(
            servico_origem="consultorio",
            tipo_evento="retorno_plano_cuidado",

            paciente_id=paciente.id,
            paciente_nome=paciente.nome,
            telefone=paciente.telefone,

            data_evento=plano.prazo_reavaliacao,

            status="agendado",

            referencia_tipo="plano_cuidado",
            referencia_id=plano.id,

            observacoes=(
                f"Retorno programado para reavaliação do plano de cuidado #{plano.id}"
            )
        )

    db.add(agenda)
    db.commit()

    return {
        "mensagem": "Plano de cuidado criado com sucesso.",
        "plano": plano
    }


@router.get("/paciente-clinico/{paciente_id}/planos-cuidado")
def listar_planos_cuidado_paciente(
    paciente_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    paciente = db.query(PacienteClinico).filter(
        PacienteClinico.id == paciente_id
    ).first()

    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente clínico não encontrado")

    planos = db.query(PlanoCuidado).filter(
        PlanoCuidado.paciente_id == paciente_id
    ).order_by(
        PlanoCuidado.criado_em.desc()
    ).all()

    return {
        "paciente_id": paciente.id,
        "paciente": paciente.nome,
        "total": len(planos),
        "planos": planos
    }


@router.put("/plano-cuidado/{plano_id}")
def atualizar_plano_cuidado(
    plano_id: int,
    dados: PlanoCuidadoUpdate,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    exigir_farmaceutico_ou_admin(current)

    plano = db.query(PlanoCuidado).filter(
        PlanoCuidado.id == plano_id
    ).first()

    if not plano:
        raise HTTPException(status_code=404, detail="Plano de cuidado não encontrado")

    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(plano, campo, valor)

    if dados.prazo_reavaliacao:
        agenda = db.query(AgendaIntegrada).filter(
        AgendaIntegrada.referencia_tipo == "plano_cuidado",
        AgendaIntegrada.referencia_id == plano.id
    ).first()

    paciente = db.query(PacienteClinico).filter(
        PacienteClinico.id == plano.paciente_id
    ).first()

    if agenda:
        agenda.data_evento = dados.prazo_reavaliacao
        agenda.paciente_nome = paciente.nome if paciente else agenda.paciente_nome
        agenda.telefone = paciente.telefone if paciente else agenda.telefone
        agenda.status = "agendado"
        agenda.atualizado_em = datetime.utcnow()

    else:
        agenda = AgendaIntegrada(
            servico_origem="consultorio",
            tipo_evento="retorno_plano_cuidado",
            paciente_id=plano.paciente_id,
            paciente_nome=paciente.nome if paciente else "Não informado",
            telefone=paciente.telefone if paciente else None,
            data_evento=dados.prazo_reavaliacao,
            status="agendado",
            referencia_tipo="plano_cuidado",
            referencia_id=plano.id,
            observacoes=(
                f"Retorno programado para reavaliação do plano de cuidado #{plano.id}"
            )
        )

        db.add(agenda)
    
    db.commit()
    db.refresh(plano)

    return {
        "mensagem": "Plano de cuidado atualizado com sucesso.",
        "plano": plano
    }


@router.post("/plano-cuidado/{plano_id}/concluir")
def concluir_plano_cuidado(
    plano_id: int,
    dados: PlanoCuidadoConclusao,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    exigir_farmaceutico_ou_admin(current)

    plano = db.query(PlanoCuidado).filter(
        PlanoCuidado.id == plano_id
    ).first()

    if not plano:
        raise HTTPException(status_code=404, detail="Plano de cuidado não encontrado")

    plano.status = "concluido"
    plano.resultado = dados.resultado
    plano.resultado_classificacao = (dados.resultado_classificacao)
    plano.concluido_em = datetime.utcnow()

    agenda = db.query(AgendaIntegrada).filter(
        AgendaIntegrada.referencia_tipo == "plano_cuidado",
        AgendaIntegrada.referencia_id == plano.id
    ).first()

    if agenda:
        agenda.status = "realizado"
        agenda.atualizado_em = datetime.utcnow()
        agenda.observacoes = (
            (agenda.observacoes or "")
            + "\nPlano de cuidado concluído e agenda marcada como realizada."
        )

    db.commit()
    db.refresh(plano)

    return {
        "mensagem": "Plano de cuidado concluído com sucesso.",
        "plano": plano
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


def aplicar_filtros_atendimento(
    query,
    data_inicio: Optional[date],
    data_fim: Optional[date],
    tipo_servico: Optional[str],
    sexo: Optional[str],
    bairro: Optional[str],
    idade_min: Optional[int],
    idade_max: Optional[int]
):
    if data_inicio:
        query = query.filter(AtendimentoRapido.data_atendimento >= data_inicio)

    if data_fim:
        query = query.filter(AtendimentoRapido.data_atendimento <= data_fim)

    if tipo_servico:
        query = query.filter(AtendimentoRapido.tipo_servico == tipo_servico)

    if sexo:
        query = query.filter(PacienteSimplificado.sexo == sexo)

    if bairro:
        query = query.filter(PacienteSimplificado.bairro.ilike(f"%{bairro}%"))

    if idade_min is not None:
        query = query.filter(PacienteSimplificado.idade >= idade_min)

    if idade_max is not None:
        query = query.filter(PacienteSimplificado.idade <= idade_max)

    return query


def dashboard_vazio():
    return {
        "filtros_aplicados": {},
        "total_atendimentos_rapidos": 0,
        "total_procedimentos": 0,
        "por_tipo_servico": {},
        "pressao_arterial": {"total": 0, "alterados": 0, "percentual_alterados": 0},
        "glicemia": {"total": 0, "alterados": 0, "percentual_alterados": 0},
        "bioimpedancia": {"total": 0, "risco": 0, "percentual_risco": 0},
        "pico_fluxo": {"total": 0, "risco": 0, "percentual_risco": 0}
    }


def calcular_percentual(parte: int, total: int) -> float:
    if total == 0:
        return 0
    return round((parte / total) * 100, 2)


def classificar_pa(pas: int, pad: int) -> str:
    if pas >= 180 or pad >= 120:
        return "crise_hipertensiva"
    if pas >= 140 or pad >= 90:
        return "hipertensao"
    if pas >= 120 or pad >= 80:
        return "pa_elevada"
    return "normal"


def classificar_glicemia(valor: int, tipo_jejum: Optional[str]) -> str:
    if tipo_jejum and tipo_jejum.lower() == "jejum":
        if valor < 100:
            return "normal"
        if valor <= 125:
            return "alterada"
        return "possivel_diabetes"

    if valor < 140:
        return "normal"
    if valor <= 199:
        return "alterada"
    return "possivel_diabetes"


def classificar_pico_fluxo(percentual: float) -> str:
    if percentual >= 80:
        return "zona_verde"
    if percentual >= 50:
        return "zona_amarela"
    return "zona_vermelha"

@router.get("/fila-clinica")
def fila_clinica(
    db: Session = Depends(get_db_consultorio)
):
    pacientes = db.query(PacienteSimplificado).all()

    fila = []

    for paciente in pacientes:
        atendimentos = db.query(AtendimentoRapido).filter(
            AtendimentoRapido.paciente_simplificado_id == paciente.id
        ).order_by(AtendimentoRapido.data_atendimento.desc()).all()

        if not atendimentos:
            continue

        maior_prioridade = {
            "peso": 0,
            "prioridade": "ROTINA",
            "resultado": "Sem alteração relevante",
            "ultimo_atendimento": None,
        }

        for atendimento in atendimentos:
            pa = db.query(AfericaoPA).filter(
                AfericaoPA.atendimento_rapido_id == atendimento.id
            ).first()

            glicemia = db.query(GlicemiaCapilar).filter(
                GlicemiaCapilar.atendimento_rapido_id == atendimento.id
            ).first()

            if pa:
                s = pa.pressao_sistolica
                d = pa.pressao_diastolica

                if s >= 180 or d >= 110:
                    prioridade = {
                        "peso": 4,
                        "prioridade": "PRIORIDADE MÁXIMA",
                        "resultado": f"PA {s}/{d} mmHg",
                        "ultimo_atendimento": atendimento.data_atendimento,
                    }
                elif s >= 160 or d >= 100:
                    prioridade = {
                        "peso": 3,
                        "prioridade": "PRIORIDADE ALTA",
                        "resultado": f"PA {s}/{d} mmHg",
                        "ultimo_atendimento": atendimento.data_atendimento,
                    }
                elif s >= 140 or d >= 90:
                    prioridade = {
                        "peso": 2,
                        "prioridade": "PRIORIDADE MODERADA",
                        "resultado": f"PA {s}/{d} mmHg",
                        "ultimo_atendimento": atendimento.data_atendimento,
                    }
                else:
                    prioridade = {
                        "peso": 1,
                        "prioridade": "ROTINA",
                        "resultado": f"PA {s}/{d} mmHg",
                        "ultimo_atendimento": atendimento.data_atendimento,
                    }

                if prioridade["peso"] > maior_prioridade["peso"]:
                    maior_prioridade = prioridade

            if glicemia:
                g = glicemia.valor_glicemia

                if g >= 300:
                    prioridade = {
                        "peso": 4,
                        "prioridade": "PRIORIDADE MÁXIMA",
                        "resultado": f"Glicemia {g} mg/dL",
                        "ultimo_atendimento": atendimento.data_atendimento,
                    }
                elif g >= 200:
                    prioridade = {
                        "peso": 3,
                        "prioridade": "PRIORIDADE ALTA",
                        "resultado": f"Glicemia {g} mg/dL",
                        "ultimo_atendimento": atendimento.data_atendimento,
                    }
                else:
                    prioridade = {
                        "peso": 1,
                        "prioridade": "ROTINA",
                        "resultado": f"Glicemia {g} mg/dL",
                        "ultimo_atendimento": atendimento.data_atendimento,
                    }

                if prioridade["peso"] > maior_prioridade["peso"]:
                    maior_prioridade = prioridade

        fila.append({
            "paciente_id": paciente.id,
            "nome": paciente.nome,
            "telefone": paciente.telefone,
            "data_nascimento": paciente.data_nascimento,
            "prioridade": maior_prioridade["prioridade"],
            "peso": maior_prioridade["peso"],
            "resultado": maior_prioridade["resultado"],
            "ultimo_atendimento": maior_prioridade["ultimo_atendimento"],
        })

    fila.sort(key=lambda item: item["peso"], reverse=True)

    return fila


@router.get("/dashboard-epidemiologico")
def dashboard_epidemiologico(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    pacientes = db.query(PacienteClinico).all()

    total = len(pacientes)

    if total == 0:
        return {
            "total_pacientes": 0,
            "sexo": {},
            "faixa_etaria": {},
            "principais_cids": {},
            "bairros": {}
        }

    sexo = {}
    faixa_etaria = {}
    principais_cids = {}
    bairros = {}

    for p in pacientes:

        # SEXO
        sexo_key = p.sexo or "Não informado"
        sexo[sexo_key] = sexo.get(sexo_key, 0) + 1

        # IDADE
        idade = p.idade or 0

        if idade < 12:
            faixa = "0-11"
        elif idade < 18:
            faixa = "12-17"
        elif idade < 40:
            faixa = "18-39"
        elif idade < 60:
            faixa = "40-59"
        else:
            faixa = "60+"

        faixa_etaria[faixa] = faixa_etaria.get(faixa, 0) + 1

        # CID
        cid = p.cid_principal or "Não informado"
        principais_cids[cid] = principais_cids.get(cid, 0) + 1

        # BAIRRO
        bairro = p.bairro or "Não informado"
        bairros[bairro] = bairros.get(bairro, 0) + 1

    principais_cids = dict(
        sorted(
            principais_cids.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
    )

    bairros = dict(
        sorted(
            bairros.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
    )

    return {
        "total_pacientes": total,
        "sexo": sexo,
        "faixa_etaria": faixa_etaria,
        "principais_cids": principais_cids,
        "bairros": bairros
    }

@router.get("/dashboard-antropometrico")
def dashboard_antropometrico(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    registros = db.query(Bioimpedancia).all()

    total = len(registros)

    if total == 0:
        return {
            "total_avaliacoes": 0,
            "media_imc": 0,
            "media_peso": 0,
            "media_gordura_corporal": 0,
            "media_massa_muscular": 0,
            "media_gordura_visceral": 0,
            "classificacoes_imc": {},
            "classificacoes_gordura_visceral": {}
        }

    imcs = []
    pesos = []
    gorduras = []
    massas = []
    viscerais = []

    classificacoes_imc = {}
    classificacoes_gordura_visceral = {}

    for r in registros:
        if getattr(r, "imc", None) is not None:
            imcs.append(r.imc)

        if getattr(r, "peso", None) is not None:
            pesos.append(r.peso)

        if getattr(r, "percentual_gordura", None) is not None:
            gorduras.append(r.percentual_gordura)

        if getattr(r, "percentual_massa_muscular", None) is not None:
            massas.append(r.percentual_massa_muscular)

        if getattr(r, "gordura_visceral", None) is not None:
            viscerais.append(r.gordura_visceral)

        classe_imc = getattr(r, "classificacao_imc", None) or "não_classificado"
        classificacoes_imc[classe_imc] = classificacoes_imc.get(classe_imc, 0) + 1

        classe_visceral = (
            getattr(r, "classificacao_gordura_visceral", None)
            or "não_classificado"
        )

        classificacoes_gordura_visceral[classe_visceral] = (
            classificacoes_gordura_visceral.get(classe_visceral, 0) + 1
        )

    return {
        "total_avaliacoes": total,
        "media_imc": round(sum(imcs) / len(imcs), 2) if imcs else 0,
        "media_peso": round(sum(pesos) / len(pesos), 2) if pesos else 0,
        "media_gordura_corporal": round(sum(gorduras) / len(gorduras), 2) if gorduras else 0,
        "media_massa_muscular": round(sum(massas) / len(massas), 2) if massas else 0,
        "media_gordura_visceral": round(sum(viscerais) / len(viscerais), 2) if viscerais else 0,
        "classificacoes_imc": classificacoes_imc,
        "classificacoes_gordura_visceral": classificacoes_gordura_visceral
    }

@router.get("/dashboard-cardiovascular")
def dashboard_cardiovascular(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    afericoes = db.query(AfericaoPA).all()

    total = len(afericoes)

    if total == 0:
        return {
            "total_afericoes": 0,
            "media_pas": 0,
            "media_pad": 0,
            "classificacoes": {}
        }

    soma_pas = 0
    soma_pad = 0

    classificacoes = {
        "normal": 0,
        "pa_elevada": 0,
        "hipertensao": 0,
        "crise_hipertensiva": 0,
    }

    for a in afericoes:
        soma_pas += a.pressao_sistolica or 0
        soma_pad += a.pressao_diastolica or 0

        classe = a.classificacao or "não_classificado"
        classificacoes[classe] = classificacoes.get(classe, 0) + 1

    return {
        "total_afericoes": total,
        "media_pas": round(soma_pas / total, 2),
        "media_pad": round(soma_pad / total, 2),
        "classificacoes": classificacoes
    }

@router.get("/dashboard-glicemico")
def dashboard_glicemico(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    registros = db.query(GlicemiaCapilar).all()

    total = len(registros)

    if total == 0:
        return {
            "total_afericoes": 0,
            "media_glicemia": 0,
            "classificacoes": {},
            "tipos_jejum": {}
        }

    valores = []
    classificacoes = {}
    tipos_jejum = {}

    for r in registros:
        if getattr(r, "valor_glicemia", None) is not None:
            valores.append(r.valor_glicemia)

        classe = getattr(r, "classificacao", None) or "não_classificado"
        classificacoes[classe] = classificacoes.get(classe, 0) + 1

        tipo = getattr(r, "tipo_jejum", None) or "não_informado"
        tipos_jejum[tipo] = tipos_jejum.get(tipo, 0) + 1

    return {
        "total_afericoes": total,
        "media_glicemia": round(sum(valores) / len(valores), 2) if valores else 0,
        "classificacoes": classificacoes,
        "tipos_jejum": tipos_jejum
    }

@router.get("/dashboard-efetividade-cuidado")
def dashboard_efetividade_cuidado(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    planos = db.query(PlanoCuidado).all()

    total = len(planos)

    ativos = len([
        p for p in planos
        if p.status in ["pendente", "em_acompanhamento"]
    ])

    concluidos = len([
        p for p in planos
        if p.status == "concluido"
    ])

    cancelados = len([
        p for p in planos
        if p.status == "cancelado"
    ])

    atingidos = len([
        p for p in planos
        if p.resultado_classificacao == "atingido"
    ])

    parcialmente = len([
        p for p in planos
        if p.resultado_classificacao == "parcialmente_atingido"
    ])

    nao_atingidos = len([
        p for p in planos
        if p.resultado_classificacao == "nao_atingido"
    ])

    taxa_sucesso = (
        round((atingidos / concluidos) * 100, 2)
        if concluidos > 0
        else 0
    )

    distribuicao_problemas = {}

    for plano in planos:
        problema = (
            plano.problema_identificado
            or "Não informado"
        )

        distribuicao_problemas[problema] = (
            distribuicao_problemas.get(problema, 0) + 1
        )

    tempo_medio = 0

    tempos = []

    for plano in planos:
        if plano.concluido_em and plano.criado_em:
            dias = (
                plano.concluido_em.date()
                - plano.criado_em.date()
            ).days

            tempos.append(dias)

    if tempos:
        tempo_medio = round(
            sum(tempos) / len(tempos),
            1
        )

    return {
        "planos": {
            "total": total,
            "ativos": ativos,
            "concluidos": concluidos,
            "cancelados": cancelados,
        },

        "resultados": {
            "atingidos": atingidos,
            "parcialmente_atingidos": parcialmente,
            "nao_atingidos": nao_atingidos,
        },

        "taxa_sucesso": taxa_sucesso,

        "tempo_medio_conclusao_dias": tempo_medio,

        "problemas": distribuicao_problemas,
    }




