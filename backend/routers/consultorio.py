from io import BytesIO
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

def classificar_imc(imc: float):
    if imc is None:
        return None
    if imc < 18.5:
        return "baixo_peso"
    if imc < 25:
        return "eutrofia"
    if imc < 30:
        return "sobrepeso"
    if imc < 35:
        return "obesidade_grau_1"
    if imc < 40:
        return "obesidade_grau_2"
    return "obesidade_grau_3"


def classificar_gordura_visceral(valor):
    if valor is None:
        return None
    if valor <= 9:
        return "normal"
    if valor <= 14:
        return "elevada"
    return "muito_elevada"


def calcular_bioimpedancia(dados: BioimpedanciaCreate, paciente=None):
    peso = dados.peso
    altura = dados.altura

    imc = None
    classificacao_imc = None
    massa_gordura_kg = None
    massa_muscular_kg = None
    massa_magra_kg = None
    fmi = None
    ffmi = None
    relacao_gordura_musculo = None
    gasto_energetico_total = None
    diferenca_idade_corporal = None

    alertas = []

    if peso and altura and altura > 0:
        altura_m = altura / 100 if altura > 3 else altura

        imc = round(peso / (altura_m ** 2), 2)
        classificacao_imc = classificar_imc(imc)

        if classificacao_imc in ["obesidade_grau_1", "obesidade_grau_2", "obesidade_grau_3"]:
            alertas.append("Obesidade pelo IMC")

        if dados.percentual_gordura is not None:
            massa_gordura_kg = round(peso * dados.percentual_gordura / 100, 2)
            massa_magra_kg = round(peso - massa_gordura_kg, 2)
            fmi = round(massa_gordura_kg / (altura_m ** 2), 2)
            ffmi = round(massa_magra_kg / (altura_m ** 2), 2)

        if dados.percentual_massa_muscular is not None:
            massa_muscular_kg = round(peso * dados.percentual_massa_muscular / 100, 2)

        if massa_gordura_kg is not None and massa_muscular_kg and massa_muscular_kg > 0:
            relacao_gordura_musculo = round(massa_gordura_kg / massa_muscular_kg, 2)

    classificacao_gordura_visceral = classificar_gordura_visceral(
        dados.gordura_visceral
    )

    if classificacao_gordura_visceral in ["elevada", "muito_elevada"]:
        alertas.append("Gordura visceral elevada")

    if dados.metabolismo_basal and dados.fator_atividade:
        gasto_energetico_total = round(
            dados.metabolismo_basal * dados.fator_atividade,
            2
        )

    if paciente and dados.idade_corporal is not None:
        idade_cronologica = calcular_idade(paciente.data_nascimento)

        if idade_cronologica is not None:
            diferenca_idade_corporal = dados.idade_corporal - idade_cronologica

            if diferenca_idade_corporal > 0:
                alertas.append("Idade corporal acima da idade cronológica")

    risco_cardiometabolico = "baixo"

    if "Gordura visceral elevada" in alertas or "Obesidade pelo IMC" in alertas:
        risco_cardiometabolico = "moderado"

    if classificacao_gordura_visceral == "muito_elevada":
        risco_cardiometabolico = "alto"

    return {
        "imc": imc,
        "classificacao_imc": classificacao_imc,
        "massa_gordura_kg": massa_gordura_kg,
        "massa_muscular_kg": massa_muscular_kg,
        "massa_magra_kg": massa_magra_kg,
        "classificacao_gordura_visceral": classificacao_gordura_visceral,
        "gasto_energetico_total": gasto_energetico_total,
        "diferenca_idade_corporal": diferenca_idade_corporal,
        "fmi": fmi,
        "ffmi": ffmi,
        "relacao_gordura_musculo": relacao_gordura_musculo,
        "risco_cardiometabolico": risco_cardiometabolico,
        "alertas": "; ".join(alertas) if alertas else None,
    }

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


@router.post("/paciente-simplificado")
def criar_paciente_simplificado(
    paciente: PacienteSimplificadoCreate,
    db: Session = Depends(get_db_consultorio),
    current: UserConsultorio = Depends(get_current_user_consultorio)
):
    exigir_pode_registrar(current)

    paciente_agenda = obter_ou_criar_paciente_agenda(
    db=db,
    nome=paciente.nome,
    telefone=paciente.telefone,
    origem="atendimento_rapido"
)

    novo = PacienteSimplificado(
    **paciente.model_dump(),
    paciente_agenda_id=paciente_agenda.id if paciente_agenda else None
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


@router.post("/atendimento-rapido")
def criar_atendimento_rapido(
    atendimento: AtendimentoRapidoCreate,
    db: Session = Depends(get_db_consultorio),
):
    paciente = db.query(PacienteSimplificado).filter(
        PacienteSimplificado.id == atendimento.paciente_simplificado_id
    ).first()

    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente simplificado não encontrado")

    novo = AtendimentoRapido(**atendimento.model_dump())
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


@router.post("/afericao-pa")
def registrar_afericao_pa(
    dados: AfericaoPACreate,
    db: Session = Depends(get_db_consultorio),
    current: UserConsultorio = Depends(get_current_user_consultorio)    
):
    exigir_pode_registrar(current)
    atendimento = db.query(AtendimentoRapido).filter(
        AtendimentoRapido.id == dados.atendimento_rapido_id
    ).first()

    if not atendimento:
        raise HTTPException(status_code=404, detail="Atendimento rápido não encontrado")

    novo = AfericaoPA(
        **dados.model_dump(),
        classificacao=classificar_pa(dados.pressao_sistolica, dados.pressao_diastolica)
    )

    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


@router.post("/glicemia")
def registrar_glicemia(
    dados: GlicemiaCapilarCreate,
    db: Session = Depends(get_db_consultorio),
    current: UserConsultorio = Depends(get_current_user_consultorio)
):
    exigir_pode_registrar(current)
    atendimento = db.query(AtendimentoRapido).filter(
    AtendimentoRapido.id == dados.atendimento_rapido_id
    ).first()

    if not atendimento:
        raise HTTPException(status_code=404, detail="Atendimento rápido não encontrado")

    novo = GlicemiaCapilar(
        **dados.model_dump(),
        classificacao=classificar_glicemia(dados.valor_glicemia, dados.tipo_jejum)
    )

    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


@router.post("/bioimpedancia")
def registrar_bioimpedancia(
    dados: BioimpedanciaCreate,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    atendimento = db.query(AtendimentoRapido).filter(
        AtendimentoRapido.id == dados.atendimento_rapido_id
    ).first()

    if not atendimento:
        raise HTTPException(
            status_code=404,
            detail="Atendimento não encontrado"
        )

    paciente = db.query(PacienteSimplificado).filter(
        PacienteSimplificado.id == atendimento.paciente_simplificado_id
    ).first()

    calculos = calcular_bioimpedancia(
        dados=dados,
        paciente=paciente
    )

    bio = Bioimpedancia(
        atendimento_rapido_id=dados.atendimento_rapido_id,

        peso=dados.peso,
        altura=dados.altura,

        imc=calculos["imc"],
        classificacao_imc=calculos["classificacao_imc"],

        percentual_gordura=dados.percentual_gordura,
        massa_gordura_kg=calculos["massa_gordura_kg"],

        percentual_massa_muscular=dados.percentual_massa_muscular,
        massa_muscular_kg=calculos["massa_muscular_kg"],

        massa_magra_kg=calculos["massa_magra_kg"],

        gordura_visceral=dados.gordura_visceral,
        classificacao_gordura_visceral=calculos["classificacao_gordura_visceral"],

        metabolismo_basal=dados.metabolismo_basal,
        fator_atividade=dados.fator_atividade,
        gasto_energetico_total=calculos["gasto_energetico_total"],

        idade_corporal=dados.idade_corporal,
        diferenca_idade_corporal=calculos["diferenca_idade_corporal"],

        fmi=calculos["fmi"],
        ffmi=calculos["ffmi"],
        relacao_gordura_musculo=calculos["relacao_gordura_musculo"],

        risco_cardiometabolico=calculos["risco_cardiometabolico"],
        alertas=calculos["alertas"],

        classificacao=calculos["classificacao_imc"],
        observacoes=dados.observacoes
    )

    db.add(bio)
    db.commit()
    db.refresh(bio)

    return {
        "mensagem": "Bioimpedância registrada com sucesso",
        "bioimpedancia_id": bio.id,
        "dados_calculados": {
            "imc": bio.imc,
            "classificacao_imc": bio.classificacao_imc,
            "massa_gordura_kg": bio.massa_gordura_kg,
            "massa_muscular_kg": bio.massa_muscular_kg,
            "massa_magra_kg": bio.massa_magra_kg,
            "classificacao_gordura_visceral": bio.classificacao_gordura_visceral,
            "gasto_energetico_total": bio.gasto_energetico_total,
            "fmi": bio.fmi,
            "ffmi": bio.ffmi,
            "risco_cardiometabolico": bio.risco_cardiometabolico,
            "alertas": bio.alertas
        }
    }

@router.post("/pico-fluxo")
def registrar_pico_fluxo(
    dados: PicoFluxoCreate,
    db: Session = Depends(get_db_consultorio),
    current: UserConsultorio = Depends(get_current_user_consultorio)
):
    exigir_pode_registrar(current)
    atendimento = db.query(AtendimentoRapido).filter(
        AtendimentoRapido.id == dados.atendimento_rapido_id
    ).first()

    if not atendimento:
        raise HTTPException(status_code=404, detail="Atendimento rápido não encontrado")

    percentual_previsto = None
    classificacao = None

    if dados.valor_previsto and dados.valor_previsto > 0:
        percentual_previsto = round((dados.valor_medido / dados.valor_previsto) * 100, 2)
        classificacao = classificar_pico_fluxo(percentual_previsto)

    novo = PicoFluxo(
        **dados.model_dump(),
        percentual_previsto=percentual_previsto,
        classificacao=classificacao
    )

    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


@router.get("/pacientes-simplificados")
def listar_pacientes_simplificados(
    db: Session = Depends(get_db_consultorio)
):
    return db.query(PacienteSimplificado).order_by(
        PacienteSimplificado.criado_em.desc()
    ).limit(100).all()


@router.get("/atendimentos-rapidos")
def listar_atendimentos_rapidos(
    db: Session = Depends(get_db_consultorio)
):
    return db.query(AtendimentoRapido).order_by(
        AtendimentoRapido.data_atendimento.desc()
    ).limit(100).all()

@router.get("/atendimento-rapido/{atendimento_id}/detalhes")
def detalhe_atendimento_rapido(
    atendimento_id: int,
    db: Session = Depends(get_db_consultorio)
):
    atendimento = db.query(AtendimentoRapido).filter(
        AtendimentoRapido.id == atendimento_id
    ).first()

    if not atendimento:
        raise HTTPException(status_code=404, detail="Atendimento rápido não encontrado")

    paciente = db.query(PacienteSimplificado).filter(
        PacienteSimplificado.id == atendimento.paciente_simplificado_id
    ).first()

    pa = db.query(AfericaoPA).filter(
        AfericaoPA.atendimento_rapido_id == atendimento.id
    ).first()

    glicemia = db.query(GlicemiaCapilar).filter(
        GlicemiaCapilar.atendimento_rapido_id == atendimento.id
    ).first()

    bioimpedancia = db.query(Bioimpedancia).filter(
        Bioimpedancia.atendimento_rapido_id == atendimento.id
    ).first()

    pico_fluxo = db.query(PicoFluxo).filter(
        PicoFluxo.atendimento_rapido_id == atendimento.id
    ).first()

    return {
        "atendimento": atendimento,
        "paciente": paciente,
        "procedimentos": {
            "pressao_arterial": pa,
            "glicemia": glicemia,
            "bioimpedancia": bioimpedancia,
            "pico_fluxo": pico_fluxo
        }
    }

@router.get("/paciente-simplificado/{paciente_id}")
def detalhe_paciente_simplificado(
    paciente_id: int,
    db: Session = Depends(get_db_consultorio)
):
    paciente = db.query(PacienteSimplificado).filter(
        PacienteSimplificado.id == paciente_id
    ).first()

    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente simplificado não encontrado")

    atendimentos = db.query(AtendimentoRapido).filter(
        AtendimentoRapido.paciente_simplificado_id == paciente.id
    ).order_by(AtendimentoRapido.data_atendimento.desc()).all()

    return {
        "paciente": paciente,
        "total_atendimentos": len(atendimentos),
        "atendimentos": atendimentos
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

@router.get("/dashboard-resolucao-alertas")
def dashboard_resolucao_alertas(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    alertas_response = alertas_clinicos_consolidados(
        db=db,
        current=current
    )

    resolucoes_response = listar_resolucoes_alertas_clinicos(
        db=db,
        current=current
    )

    alertas = alertas_response.get("alertas", [])
    resolucoes = resolucoes_response.get("resolucoes", [])

    total_alertas_gerados = len(alertas) + len(resolucoes)
    total_resolvidos = len(resolucoes)
    total_ativos = len(alertas)

    por_desfecho = {}
    por_prioridade = {}
    por_profissional = {}

    resolucoes_recentes = []

    for r in resolucoes:
        desfecho = r.get("desfecho") or "não_informado"
        prioridade = r.get("prioridade") or "sem_prioridade"
        profissional = r.get("resolvido_por") or "não_informado"

        por_desfecho[desfecho] = por_desfecho.get(desfecho, 0) + 1
        por_prioridade[prioridade] = por_prioridade.get(prioridade, 0) + 1
        por_profissional[profissional] = por_profissional.get(profissional, 0) + 1

        resolucoes_recentes.append({
            "paciente_nome": r.get("paciente_nome"),
            "desfecho": r.get("desfecho"),
            "prioridade": r.get("prioridade"),
            "mensagem_alerta": r.get("mensagem_alerta"),
            "resolvido_por": r.get("resolvido_por"),
            "resolvido_em": r.get("resolvido_em"),
        })

    resolucoes_recentes = sorted(
        resolucoes_recentes,
        key=lambda x: x.get("resolvido_em") or datetime.min,
        reverse=True
    )[:10]

    taxa_resolucao = (
        round((total_resolvidos / total_alertas_gerados) * 100, 2)
        if total_alertas_gerados > 0
        else 0
    )

    return {
        "total_alertas_gerados": total_alertas_gerados,
        "total_ativos": total_ativos,
        "total_resolvidos": total_resolvidos,
        "taxa_resolucao": taxa_resolucao,
        "por_desfecho": por_desfecho,
        "por_prioridade": por_prioridade,
        "por_profissional": por_profissional,
        "resolucoes_recentes": resolucoes_recentes,
    }

@router.get("/relatorio-resolucao-alertas-pdf")
def relatorio_resolucao_alertas_pdf(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    from fastapi.responses import StreamingResponse
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
    )
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus.flowables import PageBreak

    import io

    dashboard = dashboard_resolucao_alertas(
        db=db,
        current=current
    )

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30,
    )

    styles = getSampleStyleSheet()

    elementos = []

    titulo = Paragraph(
        "Relatório de Resolutividade Clínica",
        styles["Title"]
    )

    elementos.append(titulo)
    elementos.append(Spacer(1, 20))

    resumo_data = [
        ["Indicador", "Valor"],
        ["Alertas gerados", dashboard["total_alertas_gerados"]],
        ["Alertas ativos", dashboard["total_ativos"]],
        ["Alertas resolvidos", dashboard["total_resolvidos"]],
        ["Taxa de resolução (%)", dashboard["taxa_resolucao"]],
    ]

    tabela_resumo = Table(
        resumo_data,
        colWidths=[260, 180]
    )

    tabela_resumo.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

        ("GRID", (0, 0), (-1, -1), 1, colors.black),

        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),

        ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
    ]))

    elementos.append(tabela_resumo)
    elementos.append(Spacer(1, 24))

    elementos.append(
        Paragraph(
            "Resoluções recentes",
            styles["Heading2"]
        )
    )

    recentes = dashboard.get("resolucoes_recentes", [])

    if recentes:
        tabela_recentes = [
            [
                "Paciente",
                "Desfecho",
                "Prioridade",
                "Profissional",
            ]
        ]

        for r in recentes:
            tabela_recentes.append([
                r.get("paciente_nome") or "-",
                r.get("desfecho") or "-",
                r.get("prioridade") or "-",
                r.get("resolvido_por") or "-",
            ])

        tabela = Table(
            tabela_recentes,
            colWidths=[160, 120, 100, 120]
        )

        tabela.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

            ("GRID", (0, 0), (-1, -1), 1, colors.black),

            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),

            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
        ]))

        elementos.append(tabela)

    elementos.append(Spacer(1, 30))

    elementos.append(
        Paragraph(
            f"Relatório gerado em "
            f"{datetime.now().strftime('%d/%m/%Y %H:%M')}",
            styles["Italic"]
        )
    )

    doc.build(elementos)

    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                "inline; filename=relatorio_resolucao_alertas.pdf"
        }
    )

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

@router.post("/prontuario/{prontuario_id}/evolucao")
def criar_evolucao_clinica(
    prontuario_id: int,
    dados: EvolucaoClinicaCreate,
    db: Session = Depends(get_db_consultorio),
    current: UserConsultorio = Depends(get_current_user_consultorio)
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
    current: UserConsultorio = Depends(get_current_user_consultorio)
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

@router.post("/evolucao/{evolucao_id}/vincular-intervencao")
def vincular_intervencao(
    evolucao_id: int,
    intervencao_id: int,
    db: Session = Depends(get_db_consultorio),
    current: UserConsultorio = Depends(get_current_user_consultorio),
):
    exigir_farmaceutico_ou_admin(current)
    evolucao = db.query(EvolucaoClinica).filter(
        EvolucaoClinica.id == evolucao_id
    ).first()

    if not evolucao:
        raise HTTPException(status_code=404, detail="Evolução não encontrada")

    # 🔎 VALIDAR INTERVENÇÃO (NOVO)
    intervencao = db.execute(
        text("SELECT id FROM intervencoes WHERE id = :id"),
        {"id": intervencao_id}
    ).fetchone()

    if not intervencao:
        raise HTTPException(
            status_code=404,
            detail="Intervenção não encontrada no sistema"
        )

    # ✔️ Vincular
    evolucao.intervencao_id = intervencao_id

    db.commit()
    db.refresh(evolucao)

    return {
        "mensagem": "Intervenção validada e vinculada com sucesso.",
        "evolucao_id": evolucao_id,
        "intervencao_id": intervencao_id
    }

@router.post("/evolucao/{evolucao_id}/desfecho")
def criar_desfecho_clinico(
    evolucao_id: int,
    dados: DesfechoClinicoCreate,
    db: Session = Depends(get_db_consultorio),
):
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

@router.get("/alertas-pendentes")
def alertas_pendentes(
    db: Session = Depends(get_db_consultorio)
):
    hoje = date.today()

    alertas = []

    evolucoes_retorno = db.query(EvolucaoClinica).filter(
        EvolucaoClinica.necessidade_retorno == True,
        EvolucaoClinica.data_retorno_sugerida.isnot(None)
    ).all()

    for evolucao in evolucoes_retorno:
        desfecho = db.query(DesfechoClinico).filter(
            DesfechoClinico.evolucao_id == evolucao.id
        ).first()

        if desfecho:
            continue

        prontuario = db.query(ProntuarioClinico).filter(
            ProntuarioClinico.id == evolucao.prontuario_id
        ).first()

        paciente = None
        if prontuario:
            paciente = db.query(PacienteClinico).filter(
                PacienteClinico.id == prontuario.paciente_clinico_id
            ).first()

        dias = (evolucao.data_retorno_sugerida - hoje).days

        if dias < 0:
            tipo_alerta = "retorno_atrasado"
            prioridade = "alta"
            mensagem = f"Retorno atrasado há {abs(dias)} dia(s)."
        elif dias <= 7:
            tipo_alerta = "retorno_proximo"
            prioridade = "moderada"
            mensagem = f"Retorno previsto em {dias} dia(s)."
        else:
            continue

        alertas.append({
            "tipo_alerta": tipo_alerta,
            "prioridade": prioridade,
            "mensagem": mensagem,
            "paciente_id": paciente.id if paciente else None,
            "paciente_nome": paciente.nome if paciente else "Não informado",
            "telefone": paciente.telefone if paciente else None,
            "evolucao_id": evolucao.id,
            "prontuario_id": evolucao.prontuario_id,
            "data_retorno_sugerida": evolucao.data_retorno_sugerida
        })

    evolucoes_sem_desfecho = db.query(EvolucaoClinica).all()

    for evolucao in evolucoes_sem_desfecho:
        desfecho = db.query(DesfechoClinico).filter(
            DesfechoClinico.evolucao_id == evolucao.id
        ).first()

        if desfecho:
            continue

        prontuario = db.query(ProntuarioClinico).filter(
            ProntuarioClinico.id == evolucao.prontuario_id
        ).first()

        paciente = None
        if prontuario:
            paciente = db.query(PacienteClinico).filter(
                PacienteClinico.id == prontuario.paciente_clinico_id
            ).first()

        alertas.append({
            "tipo_alerta": "evolucao_sem_desfecho",
            "prioridade": "baixa",
            "mensagem": "Evolução clínica ainda sem desfecho registrado.",
            "paciente_id": paciente.id if paciente else None,
            "paciente_nome": paciente.nome if paciente else "Não informado",
            "telefone": paciente.telefone if paciente else None,
            "evolucao_id": evolucao.id,
            "prontuario_id": evolucao.prontuario_id,
            "data_retorno_sugerida": evolucao.data_retorno_sugerida
        })

    atendimentos_risco = db.query(AtendimentoRapido).filter(
        AtendimentoRapido.convertido_para_consultorio == False
    ).all()

    for atendimento in atendimentos_risco:
        riscos = []

        pa = db.query(AfericaoPA).filter(
            AfericaoPA.atendimento_rapido_id == atendimento.id
        ).first()

        if pa and pa.classificacao in ["pa_elevada", "hipertensao", "crise_hipertensiva"]:
            riscos.append("PA alterada")

        glicemia = db.query(GlicemiaCapilar).filter(
            GlicemiaCapilar.atendimento_rapido_id == atendimento.id
        ).first()

        if glicemia and glicemia.classificacao in ["alterada", "possivel_diabetes"]:
            riscos.append("Glicemia alterada")

        bio = db.query(Bioimpedancia).filter(
            Bioimpedancia.atendimento_rapido_id == atendimento.id
        ).first()

        if bio and bio.classificacao in [
            "sobrepeso",
            "obesidade_grau_1",
            "obesidade_grau_2",
            "obesidade_grau_3"
        ]:
            riscos.append("Bioimpedância/IMC em risco")

        pico = db.query(PicoFluxo).filter(
            PicoFluxo.atendimento_rapido_id == atendimento.id
        ).first()

        if pico and pico.classificacao in ["zona_amarela", "zona_vermelha"]:
            riscos.append("Pico de fluxo em risco")

        if not riscos:
            continue

        paciente = db.query(PacienteSimplificado).filter(
            PacienteSimplificado.id == atendimento.paciente_simplificado_id
        ).first()

        alertas.append({
            "tipo_alerta": "risco_nao_convertido",
            "prioridade": "moderada" if len(riscos) < 3 else "alta",
            "mensagem": "Paciente com risco identificado em serviço rápido ainda não convertido para acompanhamento clínico.",
            "paciente_simplificado_id": paciente.id if paciente else None,
            "paciente_nome": paciente.nome if paciente else "Não informado",
            "telefone": paciente.telefone if paciente else None,
            "atendimento_id": atendimento.id,
            "riscos": riscos
        })

    resumo = {
        "total_alertas": len(alertas),
        "alta": sum(1 for a in alertas if a["prioridade"] == "alta"),
        "moderada": sum(1 for a in alertas if a["prioridade"] == "moderada"),
        "baixa": sum(1 for a in alertas if a["prioridade"] == "baixa")
    }

    return {
        "resumo": resumo,
        "alertas": alertas
    }

@router.get("/agenda/notificacoes")
def buscar_notificacoes_agenda(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
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
        AgendaIntegrada.status == "agendado"
    ).all()

    consultas_amanha = db.query(AgendaIntegrada).filter(
        AgendaIntegrada.servico_origem == "consultorio",
        AgendaIntegrada.data_evento == amanha,
        AgendaIntegrada.status == "agendado"
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

@router.post("/agenda/notificacoes/gerar")
def executar_geracao_notificacoes_agenda(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    return gerar_notificacoes_agenda(db)

@router.get("/agenda/notificacoes/listar")
def listar_notificacoes_agenda(
    status: Optional[str] = None,
    tipo_notificacao: Optional[str] = None,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
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
        NotificacaoAgenda.criado_em.desc()
    ).all()

    return {
        "total": len(notificacoes),
        "notificacoes": notificacoes
    }


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

@router.post("/agenda/pacientes")
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
    db.commit()
    db.refresh(paciente)

    return {
        "mensagem": "Paciente cadastrado com sucesso.",
        "paciente": paciente
    }

@router.get("/agenda/pacientes")
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

@router.get("/agenda/pacientes/buscar")
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

@router.put("/agenda/pacientes/{paciente_id}")
def atualizar_paciente_agenda(
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

    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(paciente, campo, valor)

    paciente.atualizado_em = datetime.utcnow()

    db.commit()
    db.refresh(paciente)

    return {
        "mensagem": "Paciente atualizado com sucesso.",
        "paciente": paciente
    }

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

    notificacoes_pendentes = sum(
        1 for n in notificacoes if n.status == "pendente"
    )

    notificacoes_enviadas = sum(
        1 for n in notificacoes if n.status == "enviada"
    )

    notificacoes_erro = sum(
        1 for n in notificacoes if n.status == "erro"
    )

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

    from datetime import datetime

    def ordenar_data(item):
        data = item.get("data")

        if isinstance(data, str):
            try:
                return datetime.strptime(data, "%Y-%m-%d")
            except:
                return datetime.min

        if isinstance(data, datetime):
            return data

        return datetime.min

    timeline = sorted(
        timeline,
        key=ordenar_data,
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

@router.get("/alertas-clinicos-consolidados")
def alertas_clinicos_consolidados(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    alertas = []

    # 1. Alertas já existentes: retornos, evoluções sem desfecho e risco não convertido
    alertas_pendentes_response = alertas_pendentes(db=db)

    for alerta in alertas_pendentes_response.get("alertas", []):
        alertas.append({
            "origem": "alertas_pendentes",
            "tipo": alerta.get("tipo_alerta"),
            "prioridade": alerta.get("prioridade"),
            "mensagem": alerta.get("mensagem"),
            "paciente_id": alerta.get("paciente_id") or alerta.get("paciente_simplificado_id"),
            "paciente_nome": alerta.get("paciente_nome"),
            "telefone": alerta.get("telefone"),
            "data": alerta.get("data_retorno_sugerida"),
            "referencia": alerta,
        })

    # 2. Triagem de risco dos serviços rápidos
    triagem_response = triagem_risco(db=db)

    for paciente in triagem_response.get("pacientes", []):
        alertas.append({
            "origem": "triagem_risco",
            "tipo": "risco_servico_rapido",
            "prioridade": paciente.get("prioridade"),
            "mensagem": paciente.get("sugestao"),
            "paciente_id": paciente.get("paciente_id"),
            "paciente_nome": paciente.get("nome"),
            "telefone": None,
            "data": paciente.get("data_atendimento"),
            "referencia": paciente,
        })

    # 3. Bioimpedância expandida
    bio_registros = db.query(Bioimpedancia).all()

    for bio in bio_registros:
        if bio.risco_cardiometabolico in ["moderado", "alto"]:
            atendimento = db.query(AtendimentoRapido).filter(
                AtendimentoRapido.id == bio.atendimento_rapido_id
            ).first()

            paciente = None

            if atendimento:
                paciente = db.query(PacienteSimplificado).filter(
                    PacienteSimplificado.id == atendimento.paciente_simplificado_id
                ).first()

            prioridade = "alta" if bio.risco_cardiometabolico == "alto" else "moderada"

            alertas.append({
                "origem": "bioimpedancia",
                "tipo": "risco_cardiometabolico",
                "prioridade": prioridade,
                "mensagem": (
                    f"Bioimpedância com risco cardiometabólico "
                    f"{bio.risco_cardiometabolico}."
                ),
                "paciente_id": paciente.id if paciente else None,
                "paciente_nome": paciente.nome if paciente else "Não informado",
                "telefone": paciente.telefone if paciente else None,
                "data": atendimento.data_atendimento if atendimento else None,
                "referencia": {
                    "bioimpedancia_id": bio.id,
                    "imc": bio.imc,
                    "classificacao_imc": bio.classificacao_imc,
                    "gordura_visceral": bio.gordura_visceral,
                    "classificacao_gordura_visceral": bio.classificacao_gordura_visceral,
                    "alertas": bio.alertas,
                },
            })

    # 4. Evoluções farmacêuticas SOAP
    evolucoes = db.query(EvolucaoFarmaceutica).all()

    for evolucao in evolucoes:
        paciente = db.query(PacienteSimplificado).filter(
            PacienteSimplificado.id == evolucao.paciente_simplificado_id
        ).first()

        if evolucao.risco_clinico == "alto":
            alertas.append({
                "origem": "evolucao_farmaceutica",
                "tipo": "risco_clinico_alto",
                "prioridade": "alta",
                "mensagem": "Evolução farmacêutica com risco clínico alto.",
                "paciente_id": paciente.id if paciente else None,
                "paciente_nome": paciente.nome if paciente else "Não informado",
                "telefone": paciente.telefone if paciente else None,
                "data": evolucao.criado_em,
                "referencia": {
                    "evolucao_id": evolucao.id,
                    "avaliacao": evolucao.avaliacao,
                    "plano": evolucao.plano,
                },
            })

        if evolucao.adesao == "ruim":
            alertas.append({
                "origem": "evolucao_farmaceutica",
                "tipo": "baixa_adesao",
                "prioridade": "moderada",
                "mensagem": "Baixa adesão registrada em evolução farmacêutica.",
                "paciente_id": paciente.id if paciente else None,
                "paciente_nome": paciente.nome if paciente else "Não informado",
                "telefone": paciente.telefone if paciente else None,
                "data": evolucao.criado_em,
                "referencia": {
                    "evolucao_id": evolucao.id,
                    "adesao": evolucao.adesao,
                },
            })

        if evolucao.prm:
            alertas.append({
                "origem": "evolucao_farmaceutica",
                "tipo": "prm_rnm",
                "prioridade": "moderada",
                "mensagem": f"PRM/RNM registrado: {evolucao.prm}",
                "paciente_id": paciente.id if paciente else None,
                "paciente_nome": paciente.nome if paciente else "Não informado",
                "telefone": paciente.telefone if paciente else None,
                "data": evolucao.criado_em,
                "referencia": {
                    "evolucao_id": evolucao.id,
                    "prm": evolucao.prm,
                },
            })
        
            # 5. Polifarmácia e risco farmacoterapêutico
    pacientes_clinicos = db.query(PacienteClinico).all()

    for paciente_clinico in pacientes_clinicos:
        avaliacao = avaliar_polifarmacia(
            paciente_id=paciente_clinico.id,
            db=db,
            current=current
        )

        if (
            avaliacao.get("polifarmacia")
            or avaliacao.get("risco") in ["moderado", "alto"]
            or avaliacao.get("interacoes")
            or avaliacao.get("duplicidades")
        ):
            prioridade = "moderada"

            if avaliacao.get("risco") == "alto":
                prioridade = "alta"

            alertas.append({
                "origem": "polifarmacia",
                "tipo": "risco_farmacoterapeutico",
                "prioridade": prioridade,
                "mensagem": avaliacao.get("interpretacao"),
                "paciente_id": (
                    paciente_clinico.paciente_simplificado_origem_id
                    or paciente_clinico.id
                ),
                "paciente_nome": paciente_clinico.nome,
                "telefone": paciente_clinico.telefone,
                "data": datetime.utcnow(),
                "referencia": avaliacao,
            })

                # 6. Evolução farmacoterapêutica longitudinal
    pacientes_clinicos = db.query(PacienteClinico).all()

    for paciente_clinico in pacientes_clinicos:
        evolucao = evolucao_farmacoterapeutica(
            paciente_id=paciente_clinico.id,
            db=db,
            current=current
        )

        tendencia = evolucao.get("tendencia")
        risco = evolucao.get("risco_farmacoterapeutico_atual")
        baixa_adesao = evolucao.get("baixa_adesao", 0)
        total_intervencoes = evolucao.get("total_intervencoes", 0)
        encaminhamentos = evolucao.get("encaminhamentos", 0)

        gerar_alerta = False
        prioridade = "moderada"
        motivos = []

        if risco == "alto":
            gerar_alerta = True
            prioridade = "alta"
            motivos.append("risco farmacoterapêutico alto")

        if tendencia in ["maior_complexidade", "risco_por_adesao"]:
            gerar_alerta = True
            prioridade = "alta"
            motivos.append(f"tendência farmacoterapêutica: {tendencia}")

        if baixa_adesao > 0:
            gerar_alerta = True
            motivos.append("baixa adesão registrada")

        if total_intervencoes >= 3:
            gerar_alerta = True
            motivos.append("múltiplas intervenções farmacoterapêuticas")

        if encaminhamentos > 0:
            gerar_alerta = True
            motivos.append("encaminhamento farmacoterapêutico necessário")

        if not gerar_alerta:
            continue

        alertas.append({
            "origem": "evolucao_farmacoterapeutica",
            "tipo": "tendencia_farmacoterapeutica",
            "prioridade": prioridade,
            "mensagem": (
                "Paciente com necessidade de revisão farmacoterapêutica: "
                + "; ".join(motivos)
                + "."
            ),
            "paciente_id": (
                paciente_clinico.paciente_simplificado_origem_id
                or paciente_clinico.id
            ),
            "paciente_nome": paciente_clinico.nome,
            "telefone": paciente_clinico.telefone,
            "data": datetime.utcnow(),
            "referencia": evolucao,
        })

    # Consolidação de alertas por paciente
    def normalizar_data_para_comparacao(valor):
        if valor is None:
            return datetime.min

        if isinstance(valor, datetime):
            return valor

        if isinstance(valor, date):
            return datetime.combine(valor, datetime.min.time())

        return datetime.min

    alertas_por_paciente = {}

    for alerta in alertas:
        paciente_id = alerta.get("paciente_id")
        chave = paciente_id or alerta.get("paciente_nome")

        if not chave:
            continue

        if chave not in alertas_por_paciente:
            alertas_por_paciente[chave] = {
                "origem": "consolidado",
                "tipo": "alerta_consolidado_paciente",
                "alerta_chave": f"consolidado-{chave}",
                "prioridade": alerta.get("prioridade"),
                "mensagem": "Paciente com múltiplos alertas clínicos/farmacoterapêuticos.",
                "paciente_id": alerta.get("paciente_id"),
                "paciente_nome": alerta.get("paciente_nome"),
                "telefone": alerta.get("telefone"),
                "data": alerta.get("data"),
                "referencia": {
                    "motivos": [],
                    "alertas_originais": [],
                },
            }

        item = alertas_por_paciente[chave]

        prioridade_atual = item.get("prioridade")
        nova_prioridade = alerta.get("prioridade")

        pesos = {
            "muito_alta": 4,
            "alta": 3,
            "moderada": 2,
            "baixa": 1,
            None: 0,
        }

        if pesos.get(nova_prioridade, 0) > pesos.get(prioridade_atual, 0):
            item["prioridade"] = nova_prioridade

        data_alerta = normalizar_data_para_comparacao(
            alerta.get("data")
        )

        data_item = normalizar_data_para_comparacao(
            item.get("data")
        )

        if alerta.get("data") and data_alerta > data_item:
            item["data"] = alerta.get("data")

        motivo = alerta.get("mensagem") or alerta.get("tipo")

        if motivo and motivo not in item["referencia"]["motivos"]:
            item["referencia"]["motivos"].append(motivo)

        item["referencia"]["alertas_originais"].append(alerta)

    alertas = list(alertas_por_paciente.values())

    for alerta in alertas:
        motivos = alerta["referencia"].get("motivos", [])

        alerta["mensagem"] = (
            "Paciente com "
            f"{len(motivos)} alerta(s) consolidado(s): "
            + "; ".join(motivos[:4])
        )

        if len(motivos) > 4:
            alerta["mensagem"] += f"; e mais {len(motivos) - 4}."

    ordem_prioridade = {
        "muito_alta": 4,
        "alta": 3,
        "moderada": 2,
        "baixa": 1,
        None: 0,
    }

    def normalizar_data_alerta(valor):
        if valor is None:
            return datetime.min

        if isinstance(valor, datetime):
            return valor

        if isinstance(valor, date):
            return datetime.combine(valor, datetime.min.time())

        return datetime.min


    alertas = sorted(
        alertas,
        key=lambda a: (
            ordem_prioridade.get(a.get("prioridade"), 0),
            normalizar_data_alerta(a.get("data"))
        ),
        reverse=True
    )

    resumo = {
        "total": len(alertas),
        "muito_alta": sum(1 for a in alertas if a.get("prioridade") == "muito_alta"),
        "alta": sum(1 for a in alertas if a.get("prioridade") == "alta"),
        "moderada": sum(1 for a in alertas if a.get("prioridade") == "moderada"),
        "baixa": sum(1 for a in alertas if a.get("prioridade") == "baixa"),
    }

    for alerta in alertas:
        if not alerta.get("alerta_chave"):
            alerta["alerta_chave"] = (
                f"{alerta.get('origem')}-"
                f"{alerta.get('tipo')}-"
                f"{alerta.get('paciente_id') or alerta.get('paciente_nome')}"
            )

    return {
        "resumo": resumo,
        "alertas": alertas
    }

@router.post("/alertas-clinicos/resolver")
def resolver_alerta_clinico(
    dados: ResolucaoAlertaClinicoCreate,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    resolucao_existente = db.query(ResolucaoAlertaClinico).filter(
        ResolucaoAlertaClinico.alerta_chave == dados.alerta_chave
    ).first()

    if resolucao_existente:
        resolucao_existente.desfecho = dados.desfecho
        resolucao_existente.observacoes = dados.observacoes
        resolucao_existente.evolucao_id = dados.evolucao_id
        resolucao_existente.intervencao_id = dados.intervencao_id
        resolucao_existente.resolvido_por = getattr(current, "nome", None)
        resolucao_existente.resolvido_em = datetime.utcnow()

        db.commit()
        db.refresh(resolucao_existente)

        return {
            "mensagem": "Resolução do alerta atualizada com sucesso.",
            "resolucao_id": resolucao_existente.id
        }

    nova = ResolucaoAlertaClinico(
        **dados.model_dump(),
        resolvido_por=getattr(current, "nome", None),
        resolvido_em=datetime.utcnow()
    )

    db.add(nova)
    db.commit()
    db.refresh(nova)

    return {
        "mensagem": "Alerta clínico resolvido com sucesso.",
        "resolucao_id": nova.id
    }


@router.get("/alertas-clinicos/resolucoes")
def listar_resolucoes_alertas_clinicos(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    resolucoes = db.query(ResolucaoAlertaClinico).order_by(
        ResolucaoAlertaClinico.resolvido_em.desc()
    ).all()

    return {
        "total": len(resolucoes),
        "resolucoes": [
            {
                "id": r.id,
                "alerta_origem": r.alerta_origem,
                "alerta_tipo": r.alerta_tipo,
                "alerta_chave": r.alerta_chave,
                "paciente_id": r.paciente_id,
                "paciente_nome": r.paciente_nome,
                "prioridade": r.prioridade,
                "mensagem_alerta": r.mensagem_alerta,
                "desfecho": r.desfecho,
                "observacoes": r.observacoes,
                "evolucao_id": r.evolucao_id,
                "intervencao_id": r.intervencao_id,
                "resolvido_por": r.resolvido_por,
                "resolvido_em": r.resolvido_em,
            }
            for r in resolucoes
        ]
    }

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

@router.get("/paciente-simplificado/{paciente_id}/bioimpedancia-historico")
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

@router.get("/paciente-simplificado/{paciente_id}/bioimpedancia-comparativo")
def comparativo_bioimpedancia_paciente(
    paciente_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    historico_response = historico_bioimpedancia_paciente(
        paciente_id=paciente_id,
        db=db,
        current=current
    )

    historico = historico_response.get("historico", [])

    if len(historico) < 2:
        return {
            "comparativo_disponivel": False,
            "mensagem": "São necessárias pelo menos duas avaliações de bioimpedância para comparação.",
            "comparacoes": [],
            "resumo": "Histórico insuficiente",
            "favoraveis": 0,
            "desfavoraveis": 0
        }

    primeira = historico[0]
    ultima = historico[-1]

    campos = [
        ("peso", "Peso", "menor_melhor"),
        ("imc", "IMC", "menor_melhor"),
        ("percentual_gordura", "% gordura corporal", "menor_melhor"),
        ("percentual_massa_muscular", "% massa muscular", "maior_melhor"),
        ("gordura_visceral", "Gordura visceral", "menor_melhor"),
        ("fmi", "FMI", "menor_melhor"),
        ("ffmi", "FFMI", "maior_melhor"),
    ]

    comparacoes = []
    favoraveis = 0
    desfavoraveis = 0

    for chave, rotulo, regra in campos:
        valor_inicial = primeira.get(chave)
        valor_final = ultima.get(chave)

        if valor_inicial is None or valor_final is None:
            continue

        try:
            diferenca = round(float(valor_final) - float(valor_inicial), 2)
        except:
            continue

        if diferenca > 0:
            tendencia = "aumento"
        elif diferenca < 0:
            tendencia = "redução"
        else:
            tendencia = "estável"

        avaliacao = "neutra"

        if regra == "menor_melhor":
            if diferenca < 0:
                avaliacao = "favoravel"
                favoraveis += 1
            elif diferenca > 0:
                avaliacao = "desfavoravel"
                desfavoraveis += 1

        if regra == "maior_melhor":
            if diferenca > 0:
                avaliacao = "favoravel"
                favoraveis += 1
            elif diferenca < 0:
                avaliacao = "desfavoravel"
                desfavoraveis += 1

        comparacoes.append({
            "indicador": rotulo,
            "valor_inicial": valor_inicial,
            "valor_final": valor_final,
            "diferenca": diferenca,
            "tendencia": tendencia,
            "avaliacao": avaliacao
        })

    if favoraveis > desfavoraveis:
        resumo = "Evolução favorável"
    elif desfavoraveis > favoraveis:
        resumo = "Evolução desfavorável"
    else:
        resumo = "Evolução parcialmente favorável"

    return {
        "comparativo_disponivel": True,
        "data_inicial": primeira.get("data"),
        "data_final": ultima.get("data"),
        "resumo": resumo,
        "favoraveis": favoraveis,
        "desfavoraveis": desfavoraveis,
        "comparacoes": comparacoes
    }


@router.get("/bioimpedancia/{bioimpedancia_id}/laudo-pdf")
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

@router.get("/paciente-simplificado/{paciente_id}/pressao-historico")
def historico_pressao_paciente(
    paciente_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    paciente = db.query(PacienteSimplificado).filter(
        PacienteSimplificado.id == paciente_id
    ).first()

    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente simplificado não encontrado")

    atendimentos = db.query(AtendimentoRapido).filter(
        AtendimentoRapido.paciente_simplificado_id == paciente_id
    ).order_by(AtendimentoRapido.data_atendimento.asc()).all()

    historico = []

    for atendimento in atendimentos:
        pa = db.query(AfericaoPA).filter(
            AfericaoPA.atendimento_rapido_id == atendimento.id
        ).first()

        if not pa:
            continue

        historico.append({
            "atendimento_id": atendimento.id,
            "data": atendimento.data_atendimento,
            "pressao_sistolica": getattr(pa, "pressao_sistolica", None),
            "pressao_diastolica": getattr(pa, "pressao_diastolica", None),
            "frequencia_cardiaca": getattr(pa, "frequencia_cardiaca", None),
            "classificacao": getattr(pa, "classificacao", None),
            "observacoes": getattr(pa, "observacoes", None),
        })

    return {
        "paciente": {
            "id": paciente.id,
            "nome": paciente.nome,
            "idade": paciente.idade,
            "sexo": paciente.sexo,
            "bairro": paciente.bairro,
        },
        "total_afericoes": len(historico),
        "historico": historico
    }

@router.get("/paciente-simplificado/{paciente_id}/glicemia-historico")
def historico_glicemia_paciente(
    paciente_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    paciente = db.query(PacienteSimplificado).filter(
        PacienteSimplificado.id == paciente_id
    ).first()

    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente simplificado não encontrado")

    atendimentos = db.query(AtendimentoRapido).filter(
        AtendimentoRapido.paciente_simplificado_id == paciente_id
    ).order_by(AtendimentoRapido.data_atendimento.asc()).all()

    historico = []

    for atendimento in atendimentos:
        glicemia = db.query(GlicemiaCapilar).filter(
            GlicemiaCapilar.atendimento_rapido_id == atendimento.id
        ).first()

        if not glicemia:
            continue

        historico.append({
            "atendimento_id": atendimento.id,
            "data": atendimento.data_atendimento,
            "valor_glicemia": getattr(glicemia, "valor_glicemia", None),
            "tipo_jejum": getattr(glicemia, "tipo_jejum", None),
            "classificacao": getattr(glicemia, "classificacao", None),
            "observacoes": getattr(glicemia, "observacoes", None),
        })

    return {
        "paciente": {
            "id": paciente.id,
            "nome": paciente.nome,
            "idade": paciente.idade,
            "sexo": paciente.sexo,
            "bairro": paciente.bairro,
        },
        "total_afericoes": len(historico),
        "historico": historico
    }

@router.get("/paciente-simplificado/{paciente_id}/pico-fluxo-historico")
def historico_pico_fluxo_paciente(
    paciente_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    paciente = db.query(PacienteSimplificado).filter(
        PacienteSimplificado.id == paciente_id
    ).first()

    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente simplificado não encontrado")

    atendimentos = db.query(AtendimentoRapido).filter(
        AtendimentoRapido.paciente_simplificado_id == paciente_id
    ).order_by(AtendimentoRapido.data_atendimento.asc()).all()

    historico = []

    for atendimento in atendimentos:
        pico = db.query(PicoFluxo).filter(
            PicoFluxo.atendimento_rapido_id == atendimento.id
        ).first()

        if not pico:
            continue

        historico.append({
            "atendimento_id": atendimento.id,
            "data": atendimento.data_atendimento,
            "valor_medido": getattr(pico, "valor_medido", None),
            "valor_previsto": getattr(pico, "valor_previsto", None),
            "percentual_previsto": getattr(pico, "percentual_previsto", None),
            "classificacao": getattr(pico, "classificacao", None),
            "observacoes": getattr(pico, "observacoes", None),
        })

    return {
        "paciente": {
            "id": paciente.id,
            "nome": paciente.nome,
            "idade": paciente.idade,
            "sexo": paciente.sexo,
            "bairro": paciente.bairro,
        },
        "total_afericoes": len(historico),
        "historico": historico
    }

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

@router.get("/evolucao/{evolucao_id}/desfechos")
def listar_desfechos_clinicos(
    evolucao_id: int,
    db: Session = Depends(get_db_consultorio)
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

@router.get("/dashboard-desfechos")
def dashboard_desfechos(
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    db: Session = Depends(get_db_consultorio)
):
    query = db.query(DesfechoClinico)

    if data_inicio:
        query = query.filter(DesfechoClinico.data_desfecho >= data_inicio)

    if data_fim:
        query = query.filter(DesfechoClinico.data_desfecho <= data_fim)

    desfechos = query.all()

    total_desfechos = len(desfechos)

    melhora_clinica = {}
    adesao_tratamento = {}

    resolvidos = 0
    nao_resolvidos = 0
    encaminhamentos = 0

    for d in desfechos:
        melhora = d.melhora_clinica or "nao_informado"
        adesao = d.adesao_tratamento or "nao_informado"

        melhora_clinica[melhora] = melhora_clinica.get(melhora, 0) + 1
        adesao_tratamento[adesao] = adesao_tratamento.get(adesao, 0) + 1

        if d.resolucao_problema:
            resolvidos += 1
        else:
            nao_resolvidos += 1

        if d.necessidade_encaminhamento:
            encaminhamentos += 1

    return {
        "filtros_aplicados": {
            "data_inicio": data_inicio,
            "data_fim": data_fim
        },
        "total_desfechos": total_desfechos,
        "melhora_clinica": melhora_clinica,
        "adesao_tratamento": adesao_tratamento,
        "resolucao_problema": {
            "resolvidos": resolvidos,
            "nao_resolvidos": nao_resolvidos,
            "percentual_resolucao": calcular_percentual(resolvidos, total_desfechos)
        },
        "encaminhamentos": {
            "total": encaminhamentos,
            "percentual_encaminhamento": calcular_percentual(encaminhamentos, total_desfechos)
        }
    }

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

@router.get("/paciente-clinico/{paciente_clinico_id}/prontuario-longitudinal-pdf")
def gerar_pdf_prontuario_longitudinal(
    paciente_clinico_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    paciente = db.query(PacienteClinico).filter(
        PacienteClinico.id == paciente_clinico_id
    ).first()

    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente clínico não encontrado")

    prontuario = db.query(ProntuarioClinico).filter(
        ProntuarioClinico.paciente_clinico_id == paciente.id
    ).first()

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()
    elementos = []

    def texto(valor):
        return str(valor) if valor not in [None, ""] else "Não informado"

    def adicionar_titulo(titulo):
        elementos.append(Spacer(1, 14))
        elementos.append(Paragraph(titulo, styles["Heading2"]))
        elementos.append(Spacer(1, 6))

    def adicionar_tabela(linhas, col1=150, col2=360):
        tabela = Table(linhas, colWidths=[col1, col2])
        tabela.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e0f2f1")),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        elementos.append(tabela)

    elementos.append(Paragraph("Prontuário Longitudinal Farmacêutico", styles["Title"]))
    elementos.append(Paragraph("Farmácia Escola Profª Ana Maria Cervantes Baraza", styles["Normal"]))
    elementos.append(Spacer(1, 14))

    adicionar_titulo("1. Identificação completa")
    adicionar_tabela([
        ["Nome", texto(paciente.nome)],
        ["Data de nascimento", texto(paciente.data_nascimento)],
        ["Idade", texto(calcular_idade(paciente.data_nascimento) or paciente.idade)],
        ["Sexo", texto(paciente.sexo)],
        ["Telefone", texto(paciente.telefone)],
        ["CPF", texto(paciente.cpf)],
        ["CNS", texto(paciente.cns)],
        ["Nome da mãe", texto(paciente.nome_mae)],
        ["Endereço", texto(paciente.endereco)],
        ["Bairro", texto(paciente.bairro)],
        ["Origem", texto(paciente.origem)],
    ])

    adicionar_titulo("2. Perfil clínico ampliado")
    adicionar_tabela([
        ["CID principal", texto(paciente.cid_principal)],
        ["CID secundário", texto(paciente.cid_secundario)],
        ["Comorbidades", texto(paciente.comorbidades)],
        ["Alergias", texto(paciente.alergias)],
        ["Tabagismo", texto(paciente.tabagismo)],
        ["Etilismo", texto(paciente.etilismo)],
        ["Atividade física", texto(paciente.atividade_fisica)],
        ["Histórico familiar", texto(paciente.historico_familiar)],
        ["Pessoa com deficiência", "Sim" if paciente.pessoa_com_deficiencia else "Não"],
        ["Tipo de deficiência", texto(paciente.tipo_deficiencia)],
        ["Vacinação influenza", "Sim" if paciente.vacinacao_influenza else "Não"],
        ["Vacinação COVID-19", "Sim" if paciente.vacinacao_covid else "Não"],
        ["Adesão terapêutica", texto(paciente.adesao_terapeutica)],
        ["Meta pressórica", texto(paciente.meta_pressao_arterial)],
        ["Meta glicêmica", texto(paciente.meta_glicemica)],
        ["Meta de peso", texto(paciente.meta_peso)],
        ["Observações clínicas", texto(paciente.observacoes_clinicas)],
    ])

    adicionar_titulo("3. Dados do prontuário")
    if prontuario:
        adicionar_tabela([
            ["Status", texto(prontuario.status)],
            ["Data de abertura", texto(prontuario.data_abertura)],
            ["Observações", texto(prontuario.observacoes)],
        ])
    else:
        elementos.append(Paragraph("Prontuário clínico não localizado.", styles["Normal"]))

    eventos_timeline = []

    adicionar_titulo("4. Histórico de serviços rápidos")

    if paciente.paciente_simplificado_origem_id:
        atendimentos = db.query(AtendimentoRapido).filter(
            AtendimentoRapido.paciente_simplificado_id == paciente.paciente_simplificado_origem_id
        ).order_by(AtendimentoRapido.data_atendimento.asc()).all()

        if not atendimentos:
            elementos.append(Paragraph("Nenhum serviço rápido registrado.", styles["Normal"]))
        else:
            for atendimento in atendimentos:
                elementos.append(Paragraph(
                    f"<b>Atendimento em {atendimento.data_atendimento}</b> — {texto(atendimento.tipo_servico)}",
                    styles["Heading3"]
                ))

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

                if pa:
                    adicionar_tabela([
                        ["Pressão arterial", f"{pa.pressao_sistolica}/{pa.pressao_diastolica} mmHg"],
                        ["Frequência cardíaca", texto(pa.frequencia_cardiaca)],
                        ["Classificação", texto(pa.classificacao)],
                        ["Observações", texto(pa.observacoes)],
                    ])
                    eventos_timeline.append([atendimento.data_atendimento, "Serviço rápido", "Pressão arterial", f"{pa.pressao_sistolica}/{pa.pressao_diastolica} mmHg - {texto(pa.classificacao)}"])

                if glicemia:
                    adicionar_tabela([
                        ["Glicemia capilar", f"{glicemia.valor_glicemia} mg/dL"],
                        ["Tipo de jejum", texto(glicemia.tipo_jejum)],
                        ["Classificação", texto(glicemia.classificacao)],
                        ["Observações", texto(glicemia.observacoes)],
                    ])
                    eventos_timeline.append([atendimento.data_atendimento, "Serviço rápido", "Glicemia capilar", f"{glicemia.valor_glicemia} mg/dL - {texto(glicemia.classificacao)}"])

                if bio:
                    adicionar_tabela([
                        ["Peso", texto(bio.peso)],
                        ["Altura", texto(bio.altura)],
                        ["IMC", texto(bio.imc)],
                        ["Classificação IMC", texto(bio.classificacao_imc or bio.classificacao)],
                        ["Gordura corporal (%)", texto(bio.percentual_gordura)],
                        ["Massa muscular (%)", texto(bio.percentual_massa_muscular)],
                        ["Gordura visceral", texto(bio.gordura_visceral)],
                        ["Classificação gordura visceral", texto(bio.classificacao_gordura_visceral)],
                        ["Risco cardiometabólico", texto(bio.risco_cardiometabolico)],
                        ["Alertas", texto(bio.alertas)],
                        ["Observações", texto(bio.observacoes)],
                    ])
                    eventos_timeline.append([atendimento.data_atendimento, "Serviço rápido", "Bioimpedância", f"IMC {texto(bio.imc)} - Risco {texto(bio.risco_cardiometabolico)}"])

                if pico:
                    adicionar_tabela([
                        ["Pico de fluxo medido", texto(pico.valor_medido)],
                        ["Valor previsto", texto(pico.valor_previsto)],
                        ["Percentual previsto", texto(pico.percentual_previsto)],
                        ["Classificação", texto(pico.classificacao)],
                        ["Observações", texto(pico.observacoes)],
                    ])
                    eventos_timeline.append([atendimento.data_atendimento, "Serviço rápido", "Pico de fluxo", f"{pico.valor_medido} L/min - {texto(pico.classificacao)}"])

                elementos.append(Spacer(1, 8))
    else:
        elementos.append(Paragraph("Paciente não possui vínculo com cadastro simplificado.", styles["Normal"]))

    adicionar_titulo("5. Evoluções farmacêuticas SOAP")

    if paciente.paciente_simplificado_origem_id:
        evolucoes_farmaceuticas = db.query(EvolucaoFarmaceutica).filter(
            EvolucaoFarmaceutica.paciente_simplificado_id == paciente.paciente_simplificado_origem_id
        ).order_by(EvolucaoFarmaceutica.criado_em.asc()).all()
    else:
        evolucoes_farmaceuticas = []

    if not evolucoes_farmaceuticas:
        elementos.append(Paragraph("Nenhuma evolução farmacêutica SOAP registrada.", styles["Normal"]))
    else:
        for e in evolucoes_farmaceuticas:
            elementos.append(Paragraph(f"<b>Evolução em {e.criado_em}</b>", styles["Heading3"]))
            adicionar_tabela([
                ["S - Subjetivo", texto(e.subjetivo)],
                ["O - Objetivo", texto(e.objetivo)],
                ["A - Avaliação", texto(e.avaliacao)],
                ["P - Plano", texto(e.plano)],
                ["PRM/RNM", texto(e.prm)],
                ["Adesão", texto(e.adesao)],
                ["Metas clínicas", texto(e.metas_clinicas)],
                ["Orientações", texto(e.orientacoes)],
                ["Encaminhamento", texto(e.encaminhamento)],
                ["Risco clínico", texto(e.risco_clinico)],
                ["Observações", texto(e.observacoes)],
            ])
            eventos_timeline.append([e.criado_em, "Cuidado farmacêutico", "Evolução SOAP", texto(e.avaliacao or e.plano or e.subjetivo)])

    adicionar_titulo("6. Evoluções clínicas do consultório")

    if prontuario:
        evolucoes = db.query(EvolucaoClinica).filter(
            EvolucaoClinica.prontuario_id == prontuario.id
        ).order_by(EvolucaoClinica.data_evolucao.asc()).all()
    else:
        evolucoes = []

    if not evolucoes:
        elementos.append(Paragraph("Nenhuma evolução clínica registrada.", styles["Normal"]))
    else:
        for e in evolucoes:
            elementos.append(Paragraph(f"<b>{texto(e.tipo_atendimento)} — {e.data_evolucao}</b>", styles["Heading3"]))
            adicionar_tabela([
                ["Queixa principal", texto(e.queixa_principal)],
                ["História breve", texto(e.historia_breve)],
                ["Avaliação farmacêutica", texto(e.avaliacao_farmaceutica)],
                ["Problemas identificados", texto(e.problemas_identificados)],
                ["Conduta", texto(e.conduta)],
                ["Orientações realizadas", texto(e.orientacoes_realizadas)],
                ["Plano de acompanhamento", texto(e.plano_acompanhamento)],
                ["Necessidade de retorno", "Sim" if e.necessidade_retorno else "Não"],
                ["Data de retorno sugerida", texto(e.data_retorno_sugerida)],
                ["Observações", texto(e.observacoes)],
            ])
            eventos_timeline.append([e.data_evolucao, "Consultório", texto(e.tipo_atendimento or "Evolução clínica"), texto(e.avaliacao_farmaceutica or e.conduta or e.queixa_principal)])

            desfechos = db.query(DesfechoClinico).filter(
                DesfechoClinico.evolucao_id == e.id
            ).order_by(DesfechoClinico.data_desfecho.asc()).all()

            for d in desfechos:
                elementos.append(Paragraph("<b>Desfecho clínico vinculado</b>", styles["Heading3"]))
                adicionar_tabela([
                    ["Data", texto(d.data_desfecho)],
                    ["Melhora clínica", texto(d.melhora_clinica)],
                    ["Adesão ao tratamento", texto(d.adesao_tratamento)],
                    ["Resolução do problema", "Sim" if d.resolucao_problema else "Não"],
                    ["Necessidade de encaminhamento", "Sim" if d.necessidade_encaminhamento else "Não"],
                    ["Encaminhamento realizado", texto(d.encaminhamento_realizado)],
                    ["Resultado observado", texto(d.resultado_observado)],
                    ["Observações", texto(d.observacoes)],
                ])
                eventos_timeline.append([d.data_desfecho, "Desfecho", "Desfecho clínico", texto(d.resultado_observado or d.observacoes)])

    adicionar_titulo("7. Farmacoterapia em uso")

    medicamentos = db.query(MedicamentoUso).filter(
        MedicamentoUso.paciente_clinico_id == paciente.id
    ).order_by(MedicamentoUso.criado_em.asc()).all()

    if not medicamentos:
        elementos.append(Paragraph("Nenhum medicamento em uso registrado.", styles["Normal"]))
    else:
        for m in medicamentos:
            adicionar_tabela([
                ["Medicamento", texto(m.nome_medicamento)],
                ["Dose", texto(m.dose)],
                ["Via", texto(m.via)],
                ["Frequência", texto(m.frequencia)],
                ["Indicação", texto(m.indicacao)],
                ["Uso contínuo", "Sim" if m.uso_continuo else "Não"],
                ["Adesão referida", texto(m.adesao_referida)],
                ["Ativo", "Sim" if m.ativo else "Não"],
                ["Observações", texto(m.observacoes)],
            ])
            eventos_timeline.append([m.criado_em, "Farmacoterapia", texto(m.nome_medicamento), f"{texto(m.dose)} {texto(m.via)} {texto(m.frequencia)}"])

    adicionar_titulo("8. Avaliação farmacoterapêutica automatizada")

    avaliacao_polifarmacia = avaliar_polifarmacia(
        paciente_id=paciente.id,
        db=db,
        current=current
    )

    adicionar_tabela([
        ["Medicamentos ativos", texto(avaliacao_polifarmacia.get("total_medicamentos"))],
        ["Polifarmácia", "Sim" if avaliacao_polifarmacia.get("polifarmacia") else "Não"],
        ["Risco farmacoterapêutico", texto(avaliacao_polifarmacia.get("risco"))],
        ["Score", texto(avaliacao_polifarmacia.get("score"))],
        ["Interpretação", texto(avaliacao_polifarmacia.get("interpretacao"))],
    ])

    adicionar_tabela([
        ["Alertas", "; ".join(avaliacao_polifarmacia.get("alertas", [])) or "Nenhum alerta"],
        ["Recomendações", "; ".join(avaliacao_polifarmacia.get("recomendacoes", [])) or "Nenhuma recomendação"],
        ["Interações", "; ".join(avaliacao_polifarmacia.get("interacoes", [])) or "Nenhuma interação identificada"],
        ["Duplicidades", "; ".join(avaliacao_polifarmacia.get("duplicidades", [])) or "Nenhuma duplicidade identificada"],
        ["Medicamentos potencialmente inapropriados", "; ".join(avaliacao_polifarmacia.get("potencialmente_inapropriados", [])) or "Nenhum identificado"],
    ])

    adicionar_titulo("9. Intervenções farmacoterapêuticas")

    intervencoes = db.query(IntervencaoFarmacoterapia).filter(
        IntervencaoFarmacoterapia.paciente_clinico_id == paciente.id
    ).order_by(IntervencaoFarmacoterapia.criado_em.asc()).all()

    if not intervencoes:
        elementos.append(Paragraph("Nenhuma intervenção farmacoterapêutica registrada.", styles["Normal"]))
    else:
        for i in intervencoes:
            elementos.append(Paragraph(f"<b>{texto(i.tipo_intervencao)} — {i.criado_em}</b>", styles["Heading3"]))
            adicionar_tabela([
                ["Tipo de intervenção", texto(i.tipo_intervencao)],
                ["Descrição", texto(i.descricao)],
                ["Conduta", texto(i.conduta)],
                ["Aceita pelo paciente", "Sim" if i.aceita_pelo_paciente else "Não"],
                ["Necessidade de encaminhamento", "Sim" if i.necessidade_encaminhamento else "Não"],
                ["Observações", texto(i.observacoes)],
            ])
            eventos_timeline.append([i.criado_em, "Intervenção farmacoterapêutica", texto(i.tipo_intervencao), texto(i.descricao or i.conduta)])

            desfechos_i = db.query(DesfechoIntervencaoFarmacoterapia).filter(
                DesfechoIntervencaoFarmacoterapia.intervencao_id == i.id
            ).order_by(DesfechoIntervencaoFarmacoterapia.criado_em.asc()).all()

            for d in desfechos_i:
                elementos.append(Paragraph("<b>Desfecho da intervenção</b>", styles["Heading3"]))
                adicionar_tabela([
                    ["Status", texto(d.status_desfecho)],
                    ["Resultado observado", texto(d.resultado_observado)],
                    ["Necessidade de nova intervenção", "Sim" if d.necessidade_nova_intervencao else "Não"],
                    ["Observações", texto(d.observacoes)],
                ])
                eventos_timeline.append([d.criado_em, "Desfecho", "Desfecho da intervenção", texto(d.status_desfecho)])

    adicionar_titulo("10. Linha do tempo longitudinal consolidada")

    eventos_timeline = sorted(eventos_timeline, key=lambda x: x[0] or datetime.min)

    if not eventos_timeline:
        elementos.append(Paragraph("Nenhum evento longitudinal consolidado.", styles["Normal"]))
    else:
        tabela_eventos = [["Data", "Origem", "Evento", "Descrição"]]

        for data, origem, evento, descricao in eventos_timeline:
            data_txt = data.strftime("%d/%m/%Y %H:%M") if data else "-"
            tabela_eventos.append([data_txt, origem, evento, descricao])

        tabela = Table(tabela_eventos, colWidths=[80, 100, 120, 230], repeatRows=1)
        tabela.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 5),
        ]))
        elementos.append(tabela)

    adicionar_titulo("11. Síntese farmacêutica")
    elementos.append(Paragraph(
        "Este prontuário longitudinal consolida dados cadastrais, perfil clínico ampliado, "
        "serviços rápidos, evoluções farmacêuticas, evoluções clínicas, farmacoterapia, "
        "intervenções e desfechos registrados no sistema. A interpretação clínica deve "
        "considerar a qualidade, completude e atualização dos registros.",
        styles["Normal"]
    ))

    elementos.append(Spacer(1, 36))

    nome_profissional = getattr(current, "nome", "Farmacêutico responsável")
    categoria = getattr(current, "categoria_profissional", "Farmacêutico")
    crf = getattr(current, "crf", None) or "CRF: __________________"

    assinatura = Table([
        ["________________________________________"],
        [nome_profissional],
        [categoria],
        [crf],
    ], colWidths=[420])

    assinatura.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 1), (0, 1), "Helvetica-Bold"),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))

    elementos.append(assinatura)

    doc.build(elementos)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition":
            f"inline; filename=prontuario_longitudinal_{paciente.id}.pdf"
        }
    )

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

@router.get("/paciente-clinico/{paciente_id}/evolucao-farmacoterapeutica")
def evolucao_farmacoterapeutica(
    paciente_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    paciente = db.query(PacienteClinico).filter(
        PacienteClinico.id == paciente_id
    ).first()

    if not paciente:
        raise HTTPException(
            status_code=404,
            detail="Paciente clínico não encontrado"
        )

    medicamentos = db.query(MedicamentoUso).filter(
        MedicamentoUso.paciente_clinico_id == paciente.id
    ).order_by(
        MedicamentoUso.criado_em.asc()
    ).all()

    intervencoes = db.query(IntervencaoFarmacoterapia).filter(
        IntervencaoFarmacoterapia.paciente_clinico_id == paciente.id
    ).order_by(
        IntervencaoFarmacoterapia.criado_em.asc()
    ).all()

    eventos = []

    for m in medicamentos:
        eventos.append({
            "data": m.criado_em,
            "tipo": "medicamento",
            "titulo": m.nome_medicamento,
            "descricao": f"{m.dose or ''} {m.via or ''} {m.frequencia or ''}",
            "adesao": m.adesao_referida,
            "ativo": m.ativo,
        })

    for i in intervencoes:
        eventos.append({
            "data": i.criado_em,
            "tipo": "intervencao",
            "titulo": i.tipo_intervencao,
            "descricao": i.descricao or i.conduta,
            "aceita": i.aceita_pelo_paciente,
            "encaminhamento": i.necessidade_encaminhamento,
        })

        desfechos = db.query(DesfechoIntervencaoFarmacoterapia).filter(
            DesfechoIntervencaoFarmacoterapia.intervencao_id == i.id
        ).order_by(
            DesfechoIntervencaoFarmacoterapia.criado_em.asc()
        ).all()

        for d in desfechos:
            eventos.append({
                "data": d.criado_em,
                "tipo": "desfecho_intervencao",
                "titulo": d.status_desfecho,
                "descricao": d.resultado_observado or d.observacoes,
                "nova_intervencao": d.necessidade_nova_intervencao,
            })

    eventos = sorted(
        eventos,
        key=lambda x: x.get("data") or datetime.min
    )

    total_medicamentos = len([
        m for m in medicamentos
        if m.ativo
    ])

    total_intervencoes = len(intervencoes)

    intervencoes_aceitas = len([
        i for i in intervencoes
        if i.aceita_pelo_paciente
    ])

    encaminhamentos = len([
        i for i in intervencoes
        if i.necessidade_encaminhamento
    ])

    adesoes = [
        (m.adesao_referida or "").lower()
        for m in medicamentos
        if m.adesao_referida
    ]

    baixa_adesao = sum(
        1 for a in adesoes
        if a in ["baixa", "ruim", "irregular"]
    )

    boa_adesao = sum(
        1 for a in adesoes
        if a in ["boa", "regular", "adequada"]
    )

    avaliacao_atual = avaliar_polifarmacia(
        paciente_id=paciente.id,
        db=db,
        current=current
    )

    tendencia = "estável"

    if total_medicamentos >= 8:
        tendencia = "maior_complexidade"

    elif total_medicamentos >= 5:
        tendencia = "polifarmacia"

    if baixa_adesao > 0:
        tendencia = "risco_por_adesao"

    if total_intervencoes > 0 and intervencoes_aceitas >= total_intervencoes:
        tendencia = "resposta_favoravel"

    interpretacao = (
        f"Paciente em uso de {total_medicamentos} medicamento(s) ativo(s), "
        f"com {total_intervencoes} intervenção(ões) farmacoterapêutica(s) registrada(s). "
        f"Tendência farmacoterapêutica atual: {tendencia}."
    )

    return {
        "paciente_id": paciente.id,
        "paciente": paciente.nome,

        "total_medicamentos_ativos": total_medicamentos,
        "total_intervencoes": total_intervencoes,
        "intervencoes_aceitas": intervencoes_aceitas,
        "encaminhamentos": encaminhamentos,

        "baixa_adesao": baixa_adesao,
        "boa_adesao": boa_adesao,

        "risco_farmacoterapeutico_atual":
            avaliacao_atual.get("risco"),

        "score_farmacoterapeutico_atual":
            avaliacao_atual.get("score"),

        "polifarmacia":
            avaliacao_atual.get("polifarmacia"),

        "tendencia": tendencia,
        "interpretacao": interpretacao,

        "eventos": eventos,
    }

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

@router.get("/dashboard-farmacoterapeutico")
def dashboard_farmacoterapeutico(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    pacientes = db.query(PacienteClinico).all()

    total_pacientes = len(pacientes)
    total_medicamentos_ativos = 0
    pacientes_polifarmacia = 0

    risco = {
        "baixo": 0,
        "moderado": 0,
        "alto": 0,
    }

    tendencias = {}
    baixa_adesao = 0
    boa_adesao = 0
    total_intervencoes = 0
    intervencoes_aceitas = 0
    encaminhamentos = 0

    for paciente in pacientes:
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

        total_medicamentos_ativos += avaliacao.get(
            "total_medicamentos",
            0
        )

        if avaliacao.get("polifarmacia"):
            pacientes_polifarmacia += 1

        risco_atual = avaliacao.get("risco") or "baixo"
        risco[risco_atual] = risco.get(risco_atual, 0) + 1

        tendencia = evolucao.get("tendencia") or "estável"
        tendencias[tendencia] = tendencias.get(tendencia, 0) + 1

        baixa_adesao += evolucao.get("baixa_adesao", 0)
        boa_adesao += evolucao.get("boa_adesao", 0)

        total_intervencoes += evolucao.get("total_intervencoes", 0)
        intervencoes_aceitas += evolucao.get("intervencoes_aceitas", 0)
        encaminhamentos += evolucao.get("encaminhamentos", 0)

    media_medicamentos = (
        round(total_medicamentos_ativos / total_pacientes, 2)
        if total_pacientes > 0
        else 0
    )

    taxa_polifarmacia = (
        round((pacientes_polifarmacia / total_pacientes) * 100, 2)
        if total_pacientes > 0
        else 0
    )

    taxa_aceitacao = (
        round((intervencoes_aceitas / total_intervencoes) * 100, 2)
        if total_intervencoes > 0
        else 0
    )

    taxa_encaminhamento = (
        round((encaminhamentos / total_intervencoes) * 100, 2)
        if total_intervencoes > 0
        else 0
    )

    return {
        "total_pacientes": total_pacientes,
        "total_medicamentos_ativos": total_medicamentos_ativos,
        "media_medicamentos_por_paciente": media_medicamentos,

        "pacientes_polifarmacia": pacientes_polifarmacia,
        "taxa_polifarmacia": taxa_polifarmacia,

        "risco_farmacoterapeutico": risco,
        "tendencias": tendencias,

        "adesao": {
            "baixa_adesao": baixa_adesao,
            "boa_adesao": boa_adesao,
        },

        "intervencoes": {
            "total": total_intervencoes,
            "aceitas": intervencoes_aceitas,
            "encaminhamentos": encaminhamentos,
            "taxa_aceitacao": taxa_aceitacao,
            "taxa_encaminhamento": taxa_encaminhamento,
        }
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

@router.get("/paciente-simplificado/{paciente_id}/historico")
def historico_paciente_simplificado(
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
        AtendimentoRapido.data_atendimento.desc()
    ).all()

    historico = []

    for atendimento in atendimentos:
        pa = db.query(AfericaoPA).filter(
            AfericaoPA.atendimento_rapido_id == atendimento.id
        ).first()

        glicemia = db.query(GlicemiaCapilar).filter(
            GlicemiaCapilar.atendimento_rapido_id == atendimento.id
        ).first()

        bioimpedancia = db.query(Bioimpedancia).filter(
            Bioimpedancia.atendimento_rapido_id == atendimento.id
        ).first()

        pico_fluxo = db.query(PicoFluxo).filter(
            PicoFluxo.atendimento_rapido_id == atendimento.id
        ).first()

        historico.append({
            "atendimento_id": atendimento.id,
            "data_atendimento": atendimento.data_atendimento,
            "tipo_servico": atendimento.tipo_servico,
            "observacoes": atendimento.observacoes,
            "procedimentos": {
                "pressao_arterial": {
                    "id": pa.id,
                    "pressao_sistolica": pa.pressao_sistolica,
                    "pressao_diastolica": pa.pressao_diastolica,
                    "frequencia_cardiaca": pa.frequencia_cardiaca,
                    "classificacao": pa.classificacao,
                    "observacoes": pa.observacoes,
                } if pa else None,

                "glicemia": {
                    "id": glicemia.id,
                    "valor_glicemia": glicemia.valor_glicemia,
                    "tipo_jejum": glicemia.tipo_jejum,
                    "classificacao": glicemia.classificacao,
                    "observacoes": glicemia.observacoes,
                } if glicemia else None,

                "bioimpedancia": {
                    "id": bioimpedancia.id,
                    "peso": bioimpedancia.peso,
                    "altura": bioimpedancia.altura,
                    "imc": bioimpedancia.imc,
                    "classificacao_imc": bioimpedancia.classificacao_imc,
                    "percentual_gordura": bioimpedancia.percentual_gordura,
                    "massa_gordura_kg": bioimpedancia.massa_gordura_kg,
                    "percentual_massa_muscular": bioimpedancia.percentual_massa_muscular,
                    "massa_muscular_kg": bioimpedancia.massa_muscular_kg,
                    "massa_magra_kg": bioimpedancia.massa_magra_kg,
                    "gordura_visceral": bioimpedancia.gordura_visceral,
                    "classificacao_gordura_visceral": bioimpedancia.classificacao_gordura_visceral,
                    "metabolismo_basal": bioimpedancia.metabolismo_basal,
                    "fator_atividade": bioimpedancia.fator_atividade,
                    "gasto_energetico_total": bioimpedancia.gasto_energetico_total,
                    "idade_corporal": bioimpedancia.idade_corporal,
                    "diferenca_idade_corporal": bioimpedancia.diferenca_idade_corporal,
                    "fmi": bioimpedancia.fmi,
                    "ffmi": bioimpedancia.ffmi,
                    "relacao_gordura_musculo": bioimpedancia.relacao_gordura_musculo,
                    "risco_cardiometabolico": bioimpedancia.risco_cardiometabolico,
                    "alertas": bioimpedancia.alertas,
                    "classificacao": bioimpedancia.classificacao,
                    "observacoes": bioimpedancia.observacoes,
                } if bioimpedancia else None,

                "pico_fluxo": {
                    "id": pico_fluxo.id,
                    "valor_medido": pico_fluxo.valor_medido,
                    "valor_previsto": pico_fluxo.valor_previsto,
                    "percentual_previsto": pico_fluxo.percentual_previsto,
                    "classificacao": pico_fluxo.classificacao,
                    "observacoes": pico_fluxo.observacoes,
                } if pico_fluxo else None,
            }
        })

    return {
        "paciente": {
            "id": paciente.id,
            "nome": paciente.nome,
            "idade": paciente.idade,
            "sexo": paciente.sexo,
            "telefone": paciente.telefone,
            "bairro": paciente.bairro,
        },
        "total_atendimentos": len(historico),
        "historico": historico
    }


   
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

    novo = MedicamentoUso(
        paciente_clinico_id=paciente_id,
        **dados.model_dump()
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

@router.get("/paciente-clinico/{paciente_id}/avaliacao-polifarmacia")
def avaliar_polifarmacia(
    paciente_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    paciente = db.query(PacienteClinico).filter(
        PacienteClinico.id == paciente_id
    ).first()

    if not paciente:
        raise HTTPException(
            status_code=404,
            detail="Paciente clínico não encontrado"
        )

    medicamentos = db.query(MedicamentoUso).filter(
        MedicamentoUso.paciente_clinico_id == paciente.id,
        MedicamentoUso.ativo == True
    ).all()

    total_medicamentos = len(medicamentos)

    polifarmacia = total_medicamentos >= 5

    lista_medicamentos = []

    for m in medicamentos:
        lista_medicamentos.append({
            "id": m.id,
            "medicamento": m.nome_medicamento,
            "dose": m.dose,
            "via": m.via,
            "frequencia": m.frequencia,
            "indicacao": m.indicacao,
            "adesao": m.adesao_referida,
        })

    risco = "baixo"
    score = 0
    alertas = []
    recomendacoes = []

    if total_medicamentos >= 5:
        risco = "moderado"
        score += 2

        alertas.append(
            "Paciente em polifarmácia (≥5 medicamentos)."
        )

        recomendacoes.append(
            "Realizar revisão farmacoterapêutica periódica."
        )

    if total_medicamentos >= 8:
        risco = "alto"
        score += 2

        alertas.append(
            "Elevado número de medicamentos em uso."
        )

    nomes = [
        (m.nome_medicamento or "").lower()
        for m in medicamentos
    ]

    duplicidades = []

    for nome in nomes:
        if nomes.count(nome) > 1 and nome not in duplicidades:
            duplicidades.append(nome)

    if duplicidades:
        risco = "alto"
        score += 2

        alertas.append(
            f"Possível duplicidade terapêutica: {', '.join(duplicidades)}"
        )

        recomendacoes.append(
            "Avaliar duplicidade terapêutica."
        )

    pares_risco = [
        ("diclofenaco", "losartana"),
        ("ibuprofeno", "enalapril"),
        ("sinvastatina", "claritromicina"),
        ("varfarina", "amoxicilina"),
        ("metformina", "alcool"),
    ]

    interacoes = []

    for a, b in pares_risco:
        if a in nomes and b in nomes:
            interacoes.append(f"{a} + {b}")

    if interacoes:
        risco = "alto"
        score += 3

        alertas.append(
            f"Possíveis interações relevantes: {', '.join(interacoes)}"
        )

        recomendacoes.append(
            "Avaliar risco de interação medicamentosa."
        )

    medicamentos_pim = [
        "diazepam",
        "clonazepam",
        "amitriptilina",
        "carisoprodol",
        "prometazina",
    ]

    potencialmente_inapropriados = []

    for nome in nomes:
        if nome in medicamentos_pim:
            potencialmente_inapropriados.append(nome)

    if potencialmente_inapropriados:
        score += 2

        if risco != "alto":
            risco = "moderado"

        alertas.append(
            "Medicamentos potencialmente inapropriados para uso prolongado."
        )

        recomendacoes.append(
            "Avaliar necessidade e segurança dos medicamentos potencialmente inapropriados."
        )

    if not alertas:
        alertas.append(
            "Nenhum risco farmacoterapêutico relevante identificado automaticamente."
        )

    if not recomendacoes:
        recomendacoes.append(
            "Manter acompanhamento farmacoterapêutico."
        )

    interpretacao = (
        f"Paciente em uso de {total_medicamentos} medicamento(s) ativos. "
        f"Classificação automatizada de risco farmacoterapêutico: {risco}."
    )

    return {
        "paciente_id": paciente.id,
        "paciente": paciente.nome,

        "total_medicamentos": total_medicamentos,

        "polifarmacia": polifarmacia,

        "risco": risco,
        "score": score,

        "medicamentos": lista_medicamentos,

        "alertas": alertas,
        "recomendacoes": recomendacoes,

        "duplicidades": duplicidades,
        "interacoes": interacoes,

        "potencialmente_inapropriados":
            potencialmente_inapropriados,

        "interpretacao":
            interpretacao,
    }

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

@router.get("/paciente-simplificado/{paciente_id}/evolucoes")
def listar_evolucoes_farmaceuticas(
    paciente_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    evolucoes = db.query(EvolucaoFarmaceutica).filter(
        EvolucaoFarmaceutica.paciente_simplificado_id == paciente_id
    ).order_by(
        EvolucaoFarmaceutica.criado_em.desc()
    ).all()

    return [
        {
            "id": e.id,
            "subjetivo": e.subjetivo,
            "objetivo": e.objetivo,
            "avaliacao": e.avaliacao,
            "plano": e.plano,
            "prm": e.prm,
            "adesao": e.adesao,
            "metas_clinicas": e.metas_clinicas,
            "orientacoes": e.orientacoes,
            "encaminhamento": e.encaminhamento,
            "risco_clinico": e.risco_clinico,
            "observacoes": e.observacoes,
            "criado_em": e.criado_em,
        }
        for e in evolucoes
    ]

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

def definir_prioridade(riscos: list[str]) -> str:
    texto = " ".join(riscos).lower()

    if "crise_hipertensiva" in texto or "zona_vermelha" in texto:
        return "muito_alta"

    if len(riscos) >= 3:
        return "alta"

    if len(riscos) == 2:
        return "moderada"

    return "baixa"


def gerar_sugestao_conduta(prioridade: str) -> str:
    if prioridade == "muito_alta":
        return "Avaliar necessidade de encaminhamento imediato conforme protocolo local."

    if prioridade == "alta":
        return "Considerar conversão para consulta farmacêutica e acompanhamento clínico."

    if prioridade == "moderada":
        return "Orientar o paciente e avaliar necessidade de novo atendimento ou consulta farmacêutica."

    return "Registrar orientação breve e considerar acompanhamento se houver recorrência."

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

@router.get("/indicadores-cientificos")
def indicadores_cientificos(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    pacientes = db.query(PacienteClinico).all()
    afericoes_pa = db.query(AfericaoPA).all()
    glicemias = db.query(GlicemiaCapilar).all()
    bioimpedancias = db.query(Bioimpedancia).all()
    intervencoes = db.query(IntervencaoFarmacoterapia).all()

    sexo = {}

    for p in pacientes:
        sexo_key = getattr(p, "sexo", None) or "Não informado"
        sexo[sexo_key] = sexo.get(sexo_key, 0) + 1

    pas = [
        getattr(a, "pressao_sistolica", None)
        for a in afericoes_pa
        if getattr(a, "pressao_sistolica", None) is not None
    ]

    pad = [
        getattr(a, "pressao_diastolica", None)
        for a in afericoes_pa
        if getattr(a, "pressao_diastolica", None) is not None
    ]

    glicemia_valores = [
        getattr(g, "valor_glicemia", None)
        for g in glicemias
        if getattr(g, "valor_glicemia", None) is not None
    ]

    imcs = [
        getattr(b, "imc", None)
        for b in bioimpedancias
        if getattr(b, "imc", None) is not None
    ]

    intervencoes_aceitas = sum(
        1 for i in intervencoes
        if getattr(i, "aceita_pelo_paciente", False)
    )

    encaminhamentos = sum(
        1 for i in intervencoes
        if getattr(i, "necessidade_encaminhamento", False)
    )

    return {
        "assistencial": {
            "total_pacientes_clinicos": len(pacientes),
            "total_afericoes_pa": len(afericoes_pa),
            "total_glicemias": len(glicemias),
            "total_bioimpedancias": len(bioimpedancias),
            "total_intervencoes": len(intervencoes),
        },
        "perfil_pacientes": {
            "sexo": sexo
        },
        "cardiovascular": {
            "media_pas": round(sum(pas) / len(pas), 2) if pas else 0,
            "media_pad": round(sum(pad) / len(pad), 2) if pad else 0,
        },
        "glicemico": {
            "media_glicemia": round(sum(glicemia_valores) / len(glicemia_valores), 2)
            if glicemia_valores else 0,
        },
        "antropometrico": {
            "media_imc": round(sum(imcs) / len(imcs), 2) if imcs else 0,
        },
        "intervencoes_farmaceuticas": {
            "intervencoes_aceitas": intervencoes_aceitas,
            "encaminhamentos": encaminhamentos,
            "taxa_aceitacao": round(
                (intervencoes_aceitas / len(intervencoes)) * 100,
                2
            ) if intervencoes else 0,
            "taxa_encaminhamento": round(
                (encaminhamentos / len(intervencoes)) * 100,
                2
            ) if intervencoes else 0,
        }
    }    
@router.get("/serie-temporal-cientifica")
def serie_temporal_cientifica(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    afericoes_pa = db.query(AfericaoPA).all()
    glicemias = db.query(GlicemiaCapilar).all()
    bioimpedancias = db.query(Bioimpedancia).all()
    intervencoes = db.query(IntervencaoFarmacoterapia).all()

    series = defaultdict(lambda: {
        "afericoes_pa": 0,
        "glicemias": 0,
        "bioimpedancias": 0,
        "intervencoes": 0,
    })

    def obter_mes(data):
        if not data:
            return "Sem data"

        try:
            return data.strftime("%Y-%m")
        except:
            return "Sem data"

    for a in afericoes_pa:
        mes = obter_mes(getattr(a, "data_afericao", None))
        series[mes]["afericoes_pa"] += 1

    for g in glicemias:
        mes = obter_mes(getattr(g, "data_afericao", None))
        series[mes]["glicemias"] += 1

    for b in bioimpedancias:
        mes = obter_mes(getattr(b, "data_avaliacao", None))
        series[mes]["bioimpedancias"] += 1

    for i in intervencoes:
        mes = obter_mes(getattr(i, "created_at", None))
        series[mes]["intervencoes"] += 1

    resultado = []

    for mes in sorted(series.keys()):
        resultado.append({
            "mes": mes,
            **series[mes]
        })

    return resultado

@router.get("/exportacao-cientifica-excel")
def exportacao_cientifica_excel(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    wb = Workbook()

    # ABA 1 — INDICADORES
    ws = wb.active
    ws.title = "Indicadores"

    indicadores = indicadores_cientificos(
        db=db,
        current=current
    )

    ws.append(["Categoria", "Indicador", "Valor"])

    for categoria, dados in indicadores.items():
        if isinstance(dados, dict):
            for indicador, valor in dados.items():
                if isinstance(valor, dict):
                    for subindicador, subvalor in valor.items():
                        ws.append([
                            categoria,
                            f"{indicador} - {subindicador}",
                            subvalor
                        ])
                else:
                    ws.append([
                        categoria,
                        indicador,
                        valor
                    ])

    # ABA 2 — SÉRIE TEMPORAL
    ws2 = wb.create_sheet("Serie_Temporal")

    serie = serie_temporal_cientifica(
        db=db,
        current=current
    )

    ws2.append([
        "Mês",
        "Aferições PA",
        "Glicemias",
        "Bioimpedâncias",
        "Intervenções"
    ])

    for item in serie:
        ws2.append([
            item.get("mes"),
            item.get("afericoes_pa"),
            item.get("glicemias"),
            item.get("bioimpedancias"),
            item.get("intervencoes")
        ])

    # ABA 3 — METADADOS
    ws3 = wb.create_sheet("Metadados")

    ws3.append(["Campo", "Valor"])
    ws3.append(["Data de exportação", datetime.now().strftime("%d/%m/%Y %H:%M")])
    ws3.append(["Profissional", getattr(current, "nome", "Não informado")])
    ws3.append(["Categoria profissional", getattr(current, "categoria_profissional", "Não informado")])
    ws3.append(["Finalidade", "Exportação científica agregada e anonimizada"])

    for sheet in wb.worksheets:
        for column_cells in sheet.columns:
            column_letter = column_cells[0].column_letter
            sheet.column_dimensions[column_letter].width = 28

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=exportacao_cientifica.xlsx"
        }
    )

@router.get("/exportacao-pesquisa-anonimizada")
def exportacao_pesquisa_anonimizada(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    wb = Workbook()

    # ABA 1 — PACIENTES
    ws = wb.active
    ws.title = "Pacientes"

    ws.append([
        "codigo_paciente",
        "idade",
        "sexo",
        "bairro",
        "convertido_consultorio"
    ])

    pacientes = db.query(PacienteSimplificado).all()

    for p in pacientes:
        convertido = db.query(PacienteClinico).filter(
            PacienteClinico.paciente_simplificado_origem_id == p.id
        ).first()

        ws.append([
            f"P{p.id}",
            getattr(p, "idade", None),
            getattr(p, "sexo", None),
            getattr(p, "bairro", None),
            "SIM" if convertido else "NÃO"
        ])

    # ABA 2 — SERVIÇOS RÁPIDOS
    ws2 = wb.create_sheet("Servicos_Rapidos")

    ws2.append([
        "codigo_paciente",
        "codigo_atendimento",
        "data_atendimento",
        "tipo_servico",
        "pas",
        "pad",
        "frequencia_cardiaca",
        "classificacao_pa",
        "glicemia",
        "tipo_glicemia",
        "classificacao_glicemia",
        "pfe",
        "pfe_previsto",
        "pfe_percentual",
        "classificacao_pfe",
        "peso",
        "altura",
        "imc",
        "classificacao_imc",
        "gordura_corporal_percentual",
        "massa_muscular_percentual",
        "gordura_visceral",
        "classificacao_gordura_visceral",
        "fmi",
        "ffmi"
    ])

    atendimentos = db.query(AtendimentoRapido).all()

    for a in atendimentos:
        pa = db.query(AfericaoPA).filter(
            AfericaoPA.atendimento_rapido_id == a.id
        ).first()

        glicemia = db.query(GlicemiaCapilar).filter(
            GlicemiaCapilar.atendimento_rapido_id == a.id
        ).first()

        pico = db.query(PicoFluxo).filter(
            PicoFluxo.atendimento_rapido_id == a.id
        ).first()

        bio = db.query(Bioimpedancia).filter(
            Bioimpedancia.atendimento_rapido_id == a.id
        ).first()

        ws2.append([
            f"P{a.paciente_simplificado_id}",
            f"A{a.id}",
            getattr(a, "data_atendimento", None),
            getattr(a, "tipo_servico", None),

            getattr(pa, "pressao_sistolica", None) if pa else None,
            getattr(pa, "pressao_diastolica", None) if pa else None,
            getattr(pa, "frequencia_cardiaca", None) if pa else None,
            getattr(pa, "classificacao", None) if pa else None,

            getattr(glicemia, "valor_glicemia", None) if glicemia else None,
            getattr(glicemia, "tipo_jejum", None) if glicemia else None,
            getattr(glicemia, "classificacao", None) if glicemia else None,

            getattr(pico, "valor_medido", None) if pico else None,
            getattr(pico, "valor_previsto", None) if pico else None,
            getattr(pico, "percentual_previsto", None) if pico else None,
            getattr(pico, "classificacao", None) if pico else None,

            getattr(bio, "peso", None) if bio else None,
            getattr(bio, "altura", None) if bio else None,
            getattr(bio, "imc", None) if bio else None,
            getattr(bio, "classificacao_imc", None) if bio else None,
            getattr(bio, "percentual_gordura", None) if bio else None,
            getattr(bio, "percentual_massa_muscular", None) if bio else None,
            getattr(bio, "gordura_visceral", None) if bio else None,
            getattr(bio, "classificacao_gordura_visceral", None) if bio else None,
            getattr(bio, "fmi", None) if bio else None,
            getattr(bio, "ffmi", None) if bio else None,
        ])

    # ABA 3 — INTERVENÇÕES FARMACÊUTICAS
    ws3 = wb.create_sheet("Intervencoes")

    ws3.append([
        "codigo_paciente_clinico",
        "codigo_intervencao",
        "data_intervencao",
        "tipo_intervencao",
        "aceita_pelo_paciente",
        "necessidade_encaminhamento",
        "status_desfecho",
        "necessidade_nova_intervencao"
    ])

    intervencoes = db.query(IntervencaoFarmacoterapia).all()

    for i in intervencoes:
        desfecho = db.query(DesfechoIntervencaoFarmacoterapia).filter(
            DesfechoIntervencaoFarmacoterapia.intervencao_id == i.id
        ).order_by(
            DesfechoIntervencaoFarmacoterapia.criado_em.desc()
        ).first()

        ws3.append([
            f"PC{i.paciente_clinico_id}",
            f"IF{i.id}",
            getattr(i, "criado_em", None),
            getattr(i, "tipo_intervencao", None),
            getattr(i, "aceita_pelo_paciente", None),
            getattr(i, "necessidade_encaminhamento", None),
            getattr(desfecho, "status_desfecho", None) if desfecho else None,
            getattr(desfecho, "necessidade_nova_intervencao", None) if desfecho else None,
        ])

    # ABA 4 — DICIONÁRIO DE DADOS
    ws4 = wb.create_sheet("Dicionario_Dados")

    ws4.append(["variavel", "descricao"])

    dicionario = [
        ["codigo_paciente", "Identificador pseudonimizado do paciente simplificado"],
        ["codigo_paciente_clinico", "Identificador pseudonimizado do paciente clínico"],
        ["idade", "Idade registrada no cadastro"],
        ["sexo", "Sexo registrado"],
        ["bairro", "Bairro de residência"],
        ["pas", "Pressão arterial sistólica"],
        ["pad", "Pressão arterial diastólica"],
        ["glicemia", "Valor de glicemia capilar"],
        ["pfe", "Pico de fluxo expiratório medido"],
        ["imc", "Índice de massa corporal"],
        ["fmi", "Índice de massa gorda"],
        ["ffmi", "Índice de massa livre de gordura"],
        ["tipo_intervencao", "Tipo de intervenção farmacêutica registrada"],
        ["status_desfecho", "Desfecho da intervenção farmacêutica"],
    ]

    for linha in dicionario:
        ws4.append(linha)

    # ABA 5 — METADADOS
    ws5 = wb.create_sheet("Metadados")

    ws5.append(["Campo", "Valor"])
    ws5.append(["Data de exportação", datetime.now().strftime("%d/%m/%Y %H:%M")])
    ws5.append(["Finalidade", "Base anonimizada para pesquisa e análise epidemiológica"])
    ws5.append(["Campos removidos", "Nome, CPF, CNS, telefone, endereço e nome da mãe"])
    ws5.append(["Identificação", "Pseudonimizada por códigos internos não nominais"])

    for sheet in wb.worksheets:
        for column_cells in sheet.columns:
            column_letter = column_cells[0].column_letter
            sheet.column_dimensions[column_letter].width = 28

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition":
            "attachment; filename=pesquisa_anonimizada_completa.xlsx"
        }
    )

@router.get("/relatorio-cientifico-pdf")
def relatorio_cientifico_pdf(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    indicadores = indicadores_cientificos(
        db=db,
        current=current
    )

    serie = serie_temporal_cientifica(
        db=db,
        current=current
    )

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

    elementos.append(Paragraph("Relatório Científico Automatizado", styles["Title"]))
    elementos.append(Paragraph(
        f"Emitido em: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        styles["Normal"]
    ))
    elementos.append(Spacer(1, 18))

    def adicionar_tabela(titulo, linhas):
        elementos.append(Paragraph(titulo, styles["Heading2"]))

        tabela = Table(linhas, colWidths=[260, 220])

        tabela.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0f2f1")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("PADDING", (0, 0), (-1, -1), 7),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))

        elementos.append(tabela)
        elementos.append(Spacer(1, 16))

    assistencial = indicadores.get("assistencial", {})
    cardiovascular = indicadores.get("cardiovascular", {})
    glicemico = indicadores.get("glicemico", {})
    antropometrico = indicadores.get("antropometrico", {})
    intervencoes = indicadores.get("intervencoes_farmaceuticas", {})

    adicionar_tabela("Indicadores Assistenciais", [
        ["Indicador", "Valor"],
        ["Pacientes clínicos", assistencial.get("total_pacientes_clinicos", 0)],
        ["Aferições de PA", assistencial.get("total_afericoes_pa", 0)],
        ["Aferições glicêmicas", assistencial.get("total_glicemias", 0)],
        ["Bioimpedâncias", assistencial.get("total_bioimpedancias", 0)],
        ["Intervenções farmacêuticas", assistencial.get("total_intervencoes", 0)],
    ])

    adicionar_tabela("Indicadores Cardiovasculares", [
        ["Indicador", "Valor"],
        ["PAS média", cardiovascular.get("media_pas", 0)],
        ["PAD média", cardiovascular.get("media_pad", 0)],
    ])

    adicionar_tabela("Indicadores Glicêmicos", [
        ["Indicador", "Valor"],
        ["Glicemia média", glicemico.get("media_glicemia", 0)],
    ])

    adicionar_tabela("Indicadores Antropométricos", [
        ["Indicador", "Valor"],
        ["IMC médio", antropometrico.get("media_imc", 0)],
    ])

    adicionar_tabela("Intervenções Farmacêuticas", [
        ["Indicador", "Valor"],
        ["Intervenções aceitas", intervencoes.get("intervencoes_aceitas", 0)],
        ["Encaminhamentos", intervencoes.get("encaminhamentos", 0)],
        ["Taxa de aceitação (%)", intervencoes.get("taxa_aceitacao", 0)],
        ["Taxa de encaminhamento (%)", intervencoes.get("taxa_encaminhamento", 0)],
    ])

    dados_serie = [[
        "Mês",
        "PA",
        "Glicemia",
        "Bioimpedância",
        "Intervenções"
    ]]

    for item in serie:
        dados_serie.append([
            item.get("mes", ""),
            item.get("afericoes_pa", 0),
            item.get("glicemias", 0),
            item.get("bioimpedancias", 0),
            item.get("intervencoes", 0),
        ])

    adicionar_tabela("Série Temporal Científica", dados_serie)

    elementos.append(Paragraph("Interpretação resumida", styles["Heading2"]))
    elementos.append(Paragraph(
        "Este relatório consolida indicadores assistenciais, epidemiológicos e clínicos "
        "registrados no sistema. Os dados têm finalidade de apoio à gestão, ensino, "
        "pesquisa, extensão e avaliação dos serviços farmacêuticos. A interpretação "
        "científica deve considerar o desenho observacional dos registros e a qualidade "
        "do preenchimento dos dados.",
        styles["Normal"]
    ))

    elementos.append(Spacer(1, 30))

    elementos.append(Paragraph(
        f"Profissional responsável: {getattr(current, 'nome', 'Não informado')}",
        styles["Normal"]
    ))

    elementos.append(Paragraph(
        f"Categoria profissional: {getattr(current, 'categoria_profissional', 'Não informado')}",
        styles["Normal"]
    ))

    doc.build(elementos)

    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "inline; filename=relatorio_cientifico.pdf"
        }
    )

