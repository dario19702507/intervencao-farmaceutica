"""Schemas Pydantic do modulo Consultorio Farmaceutico.

Passo 6B: schemas separados de routers/consultorio.py.
"""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel


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
    catalogo_medicamento_id: Optional[int] = None
    nome_medicamento: Optional[str] = None
    dose: Optional[str] = None
    via: Optional[str] = None
    frequencia: Optional[str] = None
    frequencia_uso: Optional[str] = None
    horarios_uso: Optional[str] = None
    uso_se_necessario: bool = False
    indicacao: Optional[str] = None
    uso_continuo: bool = True
    adesao_referida: Optional[str] = None
    observacoes: Optional[str] = None    


class IntervencaoFarmacoterapiaCreate(BaseModel):
    pass

class MedicamentoTrocaCreate(BaseModel):
    novo_medicamento: MedicamentoUsoCreate
    data_troca: Optional[date] = None
    motivo_troca: str
    prm_relacionado_id: Optional[int] = None
    intervencao_relacionada_id: Optional[int] = None
    observacao: Optional[str] = None


class MedicamentoSuspensaoCreate(BaseModel):
    data_suspensao: Optional[date] = None
    motivo_suspensao: str
    tipo_suspensao: str = "DEFINITIVA"
    prm_relacionado_id: Optional[int] = None
    intervencao_relacionada_id: Optional[int] = None
    observacao: Optional[str] = None


class MedicamentoEncerramentoCreate(BaseModel):
    data_encerramento: Optional[date] = None
    motivo_encerramento: str = "FIM_DO_TRATAMENTO"
    prm_relacionado_id: Optional[int] = None
    intervencao_relacionada_id: Optional[int] = None
    observacao: Optional[str] = None

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


TIPOS_EVENTO_AGENDA = {"INCLUSAO", "RETIRADA", "RENOVACAO", "ADEQUACAO", "ENCERRAMENTO"}
PRIORIDADES_AGENDA = {"NORMAL", "IMPORTANTE", "URGENTE"}
STATUS_AGENDA = {"AGENDADO", "REALIZADO", "ATRASADO", "CANCELADO"}

class AgendaIntegradaCreate(BaseModel):
    servico_origem: str
    tipo_evento: str
    prioridade: Optional[str] = "NORMAL"
    titulo: Optional[str] = None

    paciente_id: Optional[int] = None
    paciente_nome: str
    telefone: Optional[str] = None

    medicamento_id: Optional[int] = None
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
    prioridade: Optional[str] = None
    titulo: Optional[str] = None

    paciente_nome: Optional[str] = None
    telefone: Optional[str] = None

    medicamento_id: Optional[int] = None
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



class CatalogoMedicamentoCreate(BaseModel):
    farmaco: str
    principio_ativo: Optional[str] = None
    nome_comercial: Optional[str] = None
    apresentacao: str
    concentracao: Optional[str] = None
    forma_farmaceutica: Optional[str] = None
    laboratorio: Optional[str] = None
    registro_anvisa: Optional[str] = None
    classe_terapeutica: Optional[str] = None
    componente: Optional[str] = None
    frequencia_dispensacao: Optional[str] = None
    observacoes: Optional[str] = None


class CatalogoMedicamentoUpdate(BaseModel):
    farmaco: Optional[str] = None
    principio_ativo: Optional[str] = None
    nome_comercial: Optional[str] = None
    apresentacao: Optional[str] = None
    concentracao: Optional[str] = None
    forma_farmaceutica: Optional[str] = None
    laboratorio: Optional[str] = None
    registro_anvisa: Optional[str] = None
    classe_terapeutica: Optional[str] = None
    componente: Optional[str] = None
    frequencia_dispensacao: Optional[str] = None
    ativo: Optional[bool] = None
    observacoes: Optional[str] = None


class NotificacaoInternaCreate(BaseModel):
    paciente_id: Optional[int] = None
    evento_agenda_id: Optional[int] = None
    tipo: str
    prioridade: Optional[str] = "NORMAL"
    origem: Optional[str] = "MANUAL"
    titulo: str
    mensagem: str
    necessita_acao: Optional[bool] = False


class NotificacaoInternaUpdate(BaseModel):
    lida: Optional[bool] = None
    prioridade: Optional[str] = None
    necessita_acao: Optional[bool] = None
    status_envio_whatsapp: Optional[str] = None


class WhatsAppEnvioManualCreate(BaseModel):
    telefone: str
    mensagem: str
    paciente_id: Optional[int] = None
    prioridade: Optional[str] = "NORMAL"
    data_programada: Optional[datetime] = None


class WhatsAppEnvioUpdate(BaseModel):
    status: Optional[str] = None
    telefone: Optional[str] = None
    mensagem: Optional[str] = None
    data_programada: Optional[datetime] = None

class DocumentoPacienteUpdate(BaseModel):
    tipo_documento: Optional[str] = None
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    data_emissao: Optional[date] = None
    data_validade: Optional[date] = None
    status: Optional[str] = None
    ativo: Optional[bool] = None
    operacao_vigencia: Optional[str] = None
    processo_documental_id: Optional[int] = None


class VigenciaDocumentoUpdate(BaseModel):
    vigencia_inicio: date
    vigencia_fim: date
    motivo: str
    observacao: Optional[str] = None

