"""
Modelos SQLAlchemy do modulo Consultorio Farmaceutico.

Passo 6A: modelos separados de routers/consultorio.py.
Mantem BaseConsultorio proprio para preservar compatibilidade com a estrutura atual.
"""

from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Date, DateTime, Text, ForeignKey, Boolean, Float
from sqlalchemy.orm import declarative_base, relationship

BaseConsultorio = declarative_base()

class PacienteCEAF(BaseConsultorio):
    """Cadastro importado do CEAF para preparação da homologação.

    Esta tabela é intencionalmente separada de pacientes_clinicos. O objetivo é
    preservar a planilha original, permitir conferência/deduplicação e evitar
    sobrescrever prontuários clínicos já existentes.
    """

    __tablename__ = "pacientes_ceaf"

    id = Column(Integer, primary_key=True, index=True)
    chave_importacao = Column(String(80), unique=True, index=True, nullable=False)
    lote_importacao = Column(String(80), index=True, nullable=True)

    cns = Column(String, nullable=True, index=True)
    cpf = Column(String, nullable=True, index=True)
    nome = Column(String, nullable=False, index=True)

    medicamento_prescrito = Column(Text, nullable=True)
    municipio = Column(String, nullable=True, index=True)
    logradouro = Column(String, nullable=True)
    numero_residencia = Column(String, nullable=True)
    complemento_residencia = Column(String, nullable=True)

    data_fim_vigencia = Column(Date, nullable=True, index=True)
    situacao_lme = Column(String, nullable=True, index=True)
    data_inicio_medicamento = Column(Date, nullable=True)

    telefone = Column(String, nullable=True)
    telefone_comercial = Column(String, nullable=True)
    telefone_celular = Column(String, nullable=True)

    origem_arquivo = Column(String, nullable=True)
    ativo = Column(Boolean, default=True, index=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow)

class PacienteSimplificado(BaseConsultorio):
    __tablename__ = "pacientes_simplificados"

    id = Column(Integer, primary_key=True, index=True)
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

    catalogo_medicamento_id = Column(Integer, ForeignKey("catalogo_medicamentos.id"), nullable=True)
    nome_medicamento = Column(String, nullable=False)
    dose = Column(String, nullable=True)
    via = Column(String, nullable=True)
    frequencia = Column(String, nullable=True)
    frequencia_uso = Column(String, nullable=True)
    horarios_uso = Column(Text, nullable=True)
    uso_se_necessario = Column(Boolean, default=False)
    indicacao = Column(String, nullable=True)

    uso_continuo = Column(Boolean, default=True)
    adesao_referida = Column(String, nullable=True)
    observacoes = Column(Text, nullable=True)

    # Passo 14E.2C.5B.1 — ciclo de vida da farmacoterapia
    status_farmacoterapia = Column(String, default="EM_USO")
    data_status = Column(DateTime, nullable=True)
    motivo_status = Column(String, nullable=True)
    tipo_suspensao = Column(String, nullable=True)
    observacao_status = Column(Text, nullable=True)
    substituido_por_medicamento_id = Column(Integer, nullable=True)
    prm_relacionado_id = Column(Integer, nullable=True)
    intervencao_relacionada_id = Column(Integer, nullable=True)

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


class CatalogoMedicamento(BaseConsultorio):
    __tablename__ = "catalogo_medicamentos"

    id = Column(Integer, primary_key=True, index=True)
    farmaco = Column(String, nullable=False, index=True)
    principio_ativo = Column(String, nullable=True, index=True)
    nome_comercial = Column(String, nullable=True, index=True)
    apresentacao = Column(String, nullable=False)
    concentracao = Column(String, nullable=True)
    forma_farmaceutica = Column(String, nullable=True)
    laboratorio = Column(String, nullable=True)
    registro_anvisa = Column(String, nullable=True)
    classe_terapeutica = Column(String, nullable=True)
    componente = Column(String, nullable=True)
    frequencia_dispensacao = Column(String, nullable=True)
    ativo = Column(Boolean, default=True)
    observacoes = Column(Text, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow)

    @property
    def descricao_completa(self):
        partes = [self.farmaco, self.apresentacao, self.concentracao, self.forma_farmaceutica]
        return " - ".join([str(p) for p in partes if p])

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



class NotificacaoInterna(BaseConsultorio):
    __tablename__ = "notificacoes_internas"

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, nullable=True, index=True)
    evento_agenda_id = Column(Integer, ForeignKey("agenda_integrada.id"), nullable=True, index=True)

    tipo = Column(String, nullable=False, index=True)
    prioridade = Column(String, default="NORMAL", index=True)
    origem = Column(String, default="SISTEMA", index=True)

    titulo = Column(String, nullable=False)
    mensagem = Column(Text, nullable=False)

    lida = Column(Boolean, default=False, index=True)
    necessita_acao = Column(Boolean, default=False, index=True)

    enviada_whatsapp = Column(Boolean, default=False)
    data_envio_whatsapp = Column(DateTime, nullable=True)
    status_envio_whatsapp = Column(String, nullable=True)

    data_criacao = Column(DateTime, default=datetime.utcnow)
    data_leitura = Column(DateTime, nullable=True)

    evento = relationship("AgendaIntegrada", foreign_keys=[evento_agenda_id])

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

class AgendaIntegrada(BaseConsultorio):
    __tablename__ = "agenda_integrada"

    id = Column(Integer, primary_key=True, index=True)

    servico_origem = Column(String, nullable=False)
    tipo_evento = Column(String, nullable=False)

    paciente_id = Column(Integer, nullable=True)
    paciente_nome = Column(String, nullable=False)
    telefone = Column(String, nullable=True)

    medicamento_id = Column(Integer, ForeignKey("catalogo_medicamentos.id"), nullable=True)
    medicamento = Column(String, nullable=True)
    situacao_laudo = Column(String, nullable=True)

    data_evento = Column(Date, nullable=False)

    prioridade = Column(String, default="NORMAL")
    status = Column(String, default="agendado")
    titulo = Column(String, nullable=True)

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


class WhatsAppEnvio(BaseConsultorio):
    __tablename__ = "whatsapp_envios"

    id = Column(Integer, primary_key=True, index=True)
    notificacao_id = Column(Integer, ForeignKey("notificacoes_internas.id"), nullable=True, index=True)
    paciente_id = Column(Integer, nullable=True, index=True)

    telefone = Column(String, nullable=True, index=True)
    mensagem = Column(Text, nullable=False)

    status = Column(String, default="PENDENTE", index=True)
    provedor = Column(String, default="SIMULADOR", index=True)
    origem = Column(String, default="NOTIFICACAO_INTERNA", index=True)
    prioridade = Column(String, default="NORMAL", index=True)

    tentativa_envio = Column(Integer, default=0)
    ultimo_erro = Column(Text, nullable=True)

    data_programada = Column(DateTime, nullable=True)
    data_envio = Column(DateTime, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow)
    criado_por = Column(String, nullable=True)

    notificacao = relationship("NotificacaoInterna", foreign_keys=[notificacao_id])


class ProcessoDocumental(BaseConsultorio):
    """Agrupa documentos de uma mesma ação administrativa/assistencial.

    Exemplos: INCLUSAO, RENOVACAO, ADEQUACAO ou ENCERRAMENTO.
    A vigência operacional passa a ser vinculada ao pacote/processo,
    permitindo que laudo, exames, documentos pessoais e termo componham
    a mesma ação.
    """
    __tablename__ = "processos_documentais"

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes_clinicos.id"), nullable=False, index=True)

    tipo_processo = Column(String, nullable=False, index=True)  # INCLUSAO, RENOVACAO, ADEQUACAO, ENCERRAMENTO
    titulo = Column(String, nullable=True)
    descricao = Column(Text, nullable=True)

    situacao = Column(String, default="EM_MONTAGEM", index=True)
    prioridade = Column(String, default="NORMAL", index=True)

    data_abertura = Column(Date, default=date.today, index=True)
    data_conclusao = Column(Date, nullable=True)

    vigencia_inicio = Column(Date, nullable=True, index=True)
    vigencia_fim = Column(Date, nullable=True, index=True)
    vigencia_status = Column(String, nullable=True, index=True)

    pendencias_descricao = Column(Text, nullable=True)
    whatsapp_documental_automatico = Column(Boolean, default=False)

    criado_por = Column(String, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow)

    paciente = relationship("PacienteClinico")
    documentos = relationship("DocumentoPaciente", back_populates="processo_documental")


class DocumentoPaciente(BaseConsultorio):
    __tablename__ = "documentos_pacientes"

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes_clinicos.id"), nullable=False, index=True)
    processo_documental_id = Column(Integer, ForeignKey("processos_documentais.id"), nullable=True, index=True)

    tipo_documento = Column(String, nullable=False, index=True)
    titulo = Column(String, nullable=True)
    descricao = Column(Text, nullable=True)

    nome_arquivo_original = Column(String, nullable=False)
    nome_arquivo_salvo = Column(String, nullable=False, unique=True, index=True)
    caminho_arquivo = Column(Text, nullable=False)
    content_type = Column(String, nullable=True)
    tamanho_bytes = Column(Integer, nullable=True)

    data_emissao = Column(Date, nullable=True)
    data_validade = Column(Date, nullable=True, index=True)
    status = Column(String, default="ATIVO", index=True)
    status_documental = Column(String, default="RECEBIDO", index=True)  # PENDENTE, RECEBIDO, VALIDADO, REJEITADO, SUBSTITUIDO
    status_documental_motivo = Column(Text, nullable=True)
    status_documental_atualizado_por = Column(String, nullable=True)
    status_documental_atualizado_em = Column(DateTime, nullable=True)

    origem = Column(String, default="UPLOAD_MANUAL", index=True)
    ativo = Column(Boolean, default=True, index=True)

    criado_por = Column(String, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow)

    operacao_vigencia = Column(String, nullable=True, index=True)  # INCLUSAO, RENOVACAO, ADEQUACAO
    vigencia_inicio = Column(Date, nullable=True, index=True)
    vigencia_fim = Column(Date, nullable=True, index=True)
    vigencia_status = Column(String, nullable=True, index=True)  # AGUARDANDO_INICIO, ATIVA, ENCERRADA, SUBSTITUIDA, VENCIDA
    vigencia_origem_calculo = Column(String, nullable=True)
    vigencia_editada_manualmente = Column(Boolean, default=False)
    motivo_alteracao_vigencia = Column(Text, nullable=True)

    paciente = relationship("PacienteClinico")
    processo_documental = relationship("ProcessoDocumental", back_populates="documentos")


class HistoricoStatusDocumento(BaseConsultorio):
    __tablename__ = "historico_status_documentos"

    id = Column(Integer, primary_key=True, index=True)
    documento_id = Column(Integer, ForeignKey("documentos_pacientes.id"), nullable=False, index=True)
    paciente_id = Column(Integer, nullable=True, index=True)
    processo_documental_id = Column(Integer, nullable=True, index=True)

    status_anterior = Column(String, nullable=True)
    status_novo = Column(String, nullable=False, index=True)
    motivo = Column(Text, nullable=False)
    observacao = Column(Text, nullable=True)
    usuario = Column(String, nullable=True)
    origem = Column(String, default="MANUAL", index=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    documento = relationship("DocumentoPaciente")


class HistoricoVigenciaDocumento(BaseConsultorio):
    __tablename__ = "historico_vigencias_documentos"

    id = Column(Integer, primary_key=True, index=True)
    documento_id = Column(Integer, ForeignKey("documentos_pacientes.id"), nullable=False, index=True)
    paciente_id = Column(Integer, nullable=True, index=True)

    vigencia_inicio_anterior = Column(Date, nullable=True)
    vigencia_fim_anterior = Column(Date, nullable=True)
    vigencia_status_anterior = Column(String, nullable=True)

    vigencia_inicio_nova = Column(Date, nullable=True)
    vigencia_fim_nova = Column(Date, nullable=True)
    vigencia_status_nova = Column(String, nullable=True)

    motivo = Column(Text, nullable=False)
    observacao = Column(Text, nullable=True)
    usuario = Column(String, nullable=True)
    origem = Column(String, default="SISTEMA")
    criado_em = Column(DateTime, default=datetime.utcnow)

    documento = relationship("DocumentoPaciente")

class ExtracaoDocumentoOCR(BaseConsultorio):
    __tablename__ = "extracoes_documentos_ocr"

    id = Column(Integer, primary_key=True, index=True)
    documento_id = Column(Integer, ForeignKey("documentos_pacientes.id"), nullable=False, index=True)
    paciente_id = Column(Integer, nullable=True, index=True)
    processo_documental_id = Column(Integer, ForeignKey("processos_documentais.id"), nullable=True, index=True)

    metodo = Column(String, nullable=True, index=True)
    status = Column(String, default="CONCLUIDO", index=True)
    texto_extraido = Column(Text, nullable=True)
    campos_sugeridos_json = Column(Text, nullable=True)
    erro = Column(Text, nullable=True)

    criado_por = Column(String, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    documento = relationship("DocumentoPaciente")
    processo_documental = relationship("ProcessoDocumental")


class ProblemaFarmacoterapeutico(BaseConsultorio):
    """Problema relacionado a medicamento/terapia registrado no cuidado farmacêutico."""
    __tablename__ = "problemas_farmacoterapeuticos"

    id = Column(Integer, primary_key=True, index=True)
    paciente_clinico_id = Column(Integer, ForeignKey("pacientes_clinicos.id"), nullable=False, index=True)
    medicamento_uso_id = Column(Integer, ForeignKey("medicamentos_uso.id"), nullable=True, index=True)

    categoria = Column(String, nullable=False, index=True)  # NECESSIDADE, EFETIVIDADE, SEGURANCA, ADESAO
    tipo = Column(String, nullable=False, index=True)  # legado/compatibilidade: recebe a subcategoria padronizada
    subcategoria = Column(String, nullable=True, index=True)
    natureza = Column(String, default="MANIFESTO", index=True)  # POTENCIAL, MANIFESTO
    gravidade = Column(String, default="MODERADA", index=True)  # legado/compatibilidade
    criticidade = Column(String, default="MODERADA", index=True)  # BAIXA, MODERADA, ALTA
    descricao = Column(Text, nullable=True)
    evidencias = Column(Text, nullable=True)
    causa_fator = Column(String, nullable=True, index=True)
    condicao_saude = Column(String, nullable=True, index=True)

    status = Column(String, default="ABERTO", index=True)  # ABERTO, EM_ACOMPANHAMENTO, RESOLVIDO, NAO_RESOLVIDO, REGISTRO_INVALIDO
    desfecho = Column(String, default="NAO_AVALIADO", index=True)  # RESOLVIDO, PARCIALMENTE_RESOLVIDO, NAO_RESOLVIDO, NAO_AVALIADO
    data_identificacao = Column(DateTime, default=datetime.utcnow, index=True)
    data_resolucao = Column(DateTime, nullable=True)
    resolucao = Column(Text, nullable=True)

    origem = Column(String, default="CONSULTA_FARMACEUTICA", index=True)
    sistema_codificacao = Column(String, default="PRM_FE_NEES_V1", index=True)
    versao_catalogo = Column(String, default="2026.1", index=True)
    codigo_externo = Column(String, nullable=True)
    criado_por = Column(String, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow)

    paciente = relationship("PacienteClinico")
    medicamento = relationship("MedicamentoUso")


class MetaTerapeutica(BaseConsultorio):
    """Meta objetiva do plano de cuidado farmacêutico."""
    __tablename__ = "metas_terapeuticas"

    id = Column(Integer, primary_key=True, index=True)
    paciente_clinico_id = Column(Integer, ForeignKey("pacientes_clinicos.id"), nullable=False, index=True)
    problema_id = Column(Integer, ForeignKey("problemas_farmacoterapeuticos.id"), nullable=True, index=True)

    # Passo 14E.2C.3A — metas estruturadas
    intervencao_farmacoterapia_id = Column(Integer, ForeignKey("intervencoes_farmacoterapia.id"), nullable=True, index=True)
    categoria = Column(String, nullable=True, index=True)  # CONTROLE_CLINICO, ADESAO, SEGURANCA, PROCESSO_ASSISTENCIAL, OUTRA
    subcategoria = Column(String, nullable=True, index=True)
    valor_atual = Column(String, nullable=True)
    data_inicial = Column(Date, nullable=True)
    data_prevista = Column(Date, nullable=True, index=True)
    data_conclusao = Column(Date, nullable=True)
    origem = Column(String, default="CONSULTA", index=True)
    codigo_catalogo = Column(String, nullable=True, index=True)
    versao_catalogo = Column(String, default="2026.06", index=True)

    parametro = Column(String, nullable=False, index=True)  # PA, GLICEMIA, PFE, ADESAO, SINTOMAS, OUTRO
    descricao = Column(Text, nullable=False)
    valor_alvo = Column(String, nullable=True)
    valor_inicial = Column(String, nullable=True)
    unidade = Column(String, nullable=True)
    prazo = Column(Date, nullable=True, index=True)

    status = Column(String, default="ATIVA", index=True)  # ATIVA, ALCANCADA, PARCIAL, NAO_ALCANCADA, CANCELADA
    valor_resultado = Column(String, nullable=True)
    resultado_observado = Column(Text, nullable=True)
    data_avaliacao = Column(DateTime, nullable=True)

    criado_por = Column(String, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow)

    paciente = relationship("PacienteClinico")
    problema = relationship("ProblemaFarmacoterapeutico")
    intervencao = relationship("IntervencaoFarmacoterapia")


class AcaoPlanoCuidado(BaseConsultorio):
    """Ação concreta do plano de cuidado vinculada a PRM/meta/intervenção."""
    __tablename__ = "acoes_plano_cuidado"

    id = Column(Integer, primary_key=True, index=True)
    paciente_clinico_id = Column(Integer, ForeignKey("pacientes_clinicos.id"), nullable=False, index=True)
    problema_id = Column(Integer, ForeignKey("problemas_farmacoterapeuticos.id"), nullable=True, index=True)
    meta_id = Column(Integer, ForeignKey("metas_terapeuticas.id"), nullable=True, index=True)
    intervencao_farmacoterapia_id = Column(Integer, ForeignKey("intervencoes_farmacoterapia.id"), nullable=True, index=True)

    tipo_acao = Column(String, nullable=False, index=True)  # ORIENTACAO, AJUSTE, ENCAMINHAMENTO, MONITORAMENTO, CONTATO
    descricao = Column(Text, nullable=False)
    responsavel = Column(String, nullable=True)
    prazo = Column(Date, nullable=True, index=True)
    prioridade = Column(String, default="NORMAL", index=True)

    status = Column(String, default="PENDENTE", index=True)  # PENDENTE, EM_ANDAMENTO, CONCLUIDA, CANCELADA
    resultado = Column(Text, nullable=True)
    concluido_em = Column(DateTime, nullable=True)

    criado_por = Column(String, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow)

    paciente = relationship("PacienteClinico")
    problema = relationship("ProblemaFarmacoterapeutico")
    meta = relationship("MetaTerapeutica")
    intervencao = relationship("IntervencaoFarmacoterapia")


class AvaliacaoComplexidadeFarmacoterapeutica(BaseConsultorio):
    """Histórico de avaliação automatizada da complexidade farmacoterapêutica."""
    __tablename__ = "avaliacoes_complexidade_farmacoterapeutica"

    id = Column(Integer, primary_key=True, index=True)
    paciente_clinico_id = Column(Integer, ForeignKey("pacientes_clinicos.id"), nullable=False, index=True)

    total_medicamentos = Column(Integer, default=0)
    uso_continuo = Column(Integer, default=0)
    doses_diarias_estimadas = Column(Integer, default=0)
    formas_farmaceuticas = Column(Integer, default=0)
    medicamentos_alto_risco = Column(Integer, default=0)
    problemas_abertos = Column(Integer, default=0)

    escore = Column(Integer, default=0, index=True)
    classificacao = Column(String, nullable=False, index=True)  # BAIXA, MODERADA, ALTA, MUITO_ALTA
    fatores = Column(Text, nullable=True)

    calculado_em = Column(DateTime, default=datetime.utcnow, index=True)
    calculado_por = Column(String, nullable=True)

    paciente = relationship("PacienteClinico")
