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
from jose import JWTError, jwt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import Column, Integer, String, Date, DateTime, Text, ForeignKey, Boolean, Float, func
from collections import defaultdict
from openpyxl import Workbook
from sqlalchemy.orm import declarative_base, Session, relationship
from database import engine, SessionLocal
from auth import ALGORITHM, SECRET_KEY, oauth2_scheme
from permissions import (
    exigir_autenticado as perm_exigir_autenticado,
    exigir_pode_registrar as perm_exigir_pode_registrar,
    exigir_farmaceutico_ou_admin as perm_exigir_farmaceutico_ou_admin,
    exigir_admin as perm_exigir_admin,
)
from models.consultorio_models import (
    BaseConsultorio,
    PacienteSimplificado,
    AtendimentoRapido,
    AfericaoPA,
    GlicemiaCapilar,
    Bioimpedancia,
    PicoFluxo,
    PacienteClinico,
    PlanoCuidado,
    ProntuarioClinico,
    EvolucaoClinica,
    DesfechoClinico,
    MedicamentoUso,
    IntervencaoFarmacoterapia,
    DesfechoIntervencaoFarmacoterapia,
    EvolucaoFarmaceutica,
    UserConsultorio,
    ResolucaoAlertaClinico,
    CapacidadeAgenda,
    NotificacaoAgenda,
    PacienteAgenda,
    AgendaIntegrada,
    CatalogoMedicamento,
)
from schemas.consultorio_schemas import (
    PacienteSimplificadoCreate,
    AtendimentoRapidoCreate,
    AfericaoPACreate,
    GlicemiaCapilarCreate,
    BioimpedanciaCreate,
    PicoFluxoCreate,
    ConversaoClinicoCreate,
    PacienteClinicoIdentificacaoUpdate,
    PacienteClinicoDadosClinicosUpdate,
    EvolucaoClinicaCreate,
    DesfechoClinicoCreate,
    MedicamentoUsoCreate,
    IntervencaoFarmacoterapiaCreate,
    DesfechoIntervencaoFarmacoterapiaCreate,
    EvolucaoFarmaceuticaCreate,
    ResolucaoAlertaClinicoCreate,
    PlanoCuidadoCreate,
    PlanoCuidadoUpdate,
    PlanoCuidadoConclusao,
    AgendaIntegradaCreate,
    AgendaIntegradaUpdate,
    AgendaStatusUpdate,
    CapacidadeAgendaCreate,
    CapacidadeAgendaUpdate,
    NotificacaoAgendaUpdate,
    PacienteAgendaCreate,
    PacienteAgendaUpdate,
)

from services.consultorio_helpers import (
    calcular_idade,
    classificar_imc,
    classificar_gordura_visceral,
    calcular_bioimpedancia,
    calcular_risco_populacional,
    definir_prioridade,
    gerar_sugestao_conduta,
    dashboard_vazio,
    calcular_percentual,
    classificar_pa,
    classificar_glicemia,
    classificar_pico_fluxo,
)

from services.agenda_notificacoes import (
    obter_ou_criar_paciente_agenda,
    calcular_capacidade_agenda,
    criar_proxima_dispensacao_automatica,
    gerar_alertas_renovacao_laudo,
    gerar_alertas_risco_interrupcao,
    gerar_notificacoes_agenda,
)
from services.agenda_inteligente import (
    data_tem_atendimento,
    ajustar_para_proximo_dia_atendimento,
    horarios_do_dia,
)

from services.auditoria import registrar_auditoria
from services.indicadores_consultorio import (
    montar_dashboard_servicos,
    montar_triagem_risco,
)

from services.farmacoterapia import (
    montar_avaliacao_polifarmacia,
    montar_evolucao_farmacoterapeutica,
    montar_sugestoes_plano_cuidado,
    montar_dashboard_farmacoterapeutico,
)

from services.relatorios_consultorio import (
    svc_gerar_declaracao_pdf,
    svc_laudo_bioimpedancia_pdf,
    svc_relatorio_mensal_consultorio,
    svc_gerar_pdf_prontuario,
    svc_evolucao_farmaceutica_pdf,
    svc_plano_cuidado_pdf,
    svc_evolucoes_clinicas_pdf,
    svc_orientacoes_farmaceuticas_pdf,
)

from services.alertas_clinicos import (
    svc_alertas_pendentes,
    svc_alertas_clinicos_consolidados,
    svc_resolver_alerta_clinico,
    svc_listar_resolucoes_alertas_clinicos,
    svc_dashboard_resolucao_alertas,
    svc_relatorio_resolucao_alertas_pdf,
    svc_dashboard_serie_temporal,
    svc_classificacao_risco_populacional,
)



def get_db_consultorio():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()






























































BaseConsultorio.metadata.create_all(bind=engine)











router = APIRouter(
    prefix="/consultorio",
    tags=["Consultório Farmacêutico"]
)

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
    return perm_exigir_autenticado(user)

def exigir_pode_registrar(user: UserConsultorio):
    return perm_exigir_pode_registrar(user)

def exigir_farmaceutico_ou_admin(user: UserConsultorio):
    return perm_exigir_farmaceutico_ou_admin(user)

def exigir_admin(user: UserConsultorio):
    return perm_exigir_admin(user)

@router.get("/alertas-clinicos/resolucoes")
def listar_resolucoes_alertas_clinicos(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    return svc_listar_resolucoes_alertas_clinicos(db=db, current=current)



@router.get("/atendimento-rapido/{atendimento_id}/declaracao-pdf")
def gerar_declaracao_pdf(
    atendimento_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    return svc_gerar_declaracao_pdf(atendimento_id=atendimento_id, db=db, current=current)

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
    return montar_dashboard_servicos(
        db=db,
        data_inicio=data_inicio,
        data_fim=data_fim,
        tipo_servico=tipo_servico,
        sexo=sexo,
        bairro=bairro,
        idade_min=idade_min,
        idade_max=idade_max,
        somente_risco=somente_risco,
    )

@router.get("/dashboard-resolucao-alertas")
def dashboard_resolucao_alertas(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    return svc_dashboard_resolucao_alertas(db=db, current=current)

@router.get("/relatorio-resolucao-alertas-pdf")
def relatorio_resolucao_alertas_pdf(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    return svc_relatorio_resolucao_alertas_pdf(db=db, current=current)

@router.get("/dashboard-serie-temporal")
def dashboard_serie_temporal(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    return svc_dashboard_serie_temporal(db=db, current=current)

@router.get("/classificacao-risco-populacional")
def classificacao_risco_populacional(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    return svc_classificacao_risco_populacional(db=db, current=current)

@router.get("/triagem-risco")
def triagem_risco(
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    db: Session = Depends(get_db_consultorio)
):
    return montar_triagem_risco(
        db=db,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )

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

    tipos_validos = {"INCLUSAO", "RETIRADA", "RENOVACAO", "ADEQUACAO", "ENCERRAMENTO"}
    prioridades_validas = {"NORMAL", "IMPORTANTE", "URGENTE"}

    if dados.tipo_evento and dados.tipo_evento.upper() not in tipos_validos:
        raise HTTPException(
            status_code=400,
            detail="Tipo de evento inválido. Use: INCLUSAO, RETIRADA, RENOVACAO, ADEQUACAO ou ENCERRAMENTO."
        )

    prioridade = (dados.prioridade or "NORMAL").upper()
    if prioridade not in prioridades_validas:
        raise HTTPException(
            status_code=400,
            detail="Prioridade inválida. Use: NORMAL, IMPORTANTE ou URGENTE."
        )

    medicamento_catalogo = None
    if getattr(dados, "medicamento_id", None):
        medicamento_catalogo = db.query(CatalogoMedicamento).filter(
            CatalogoMedicamento.id == dados.medicamento_id,
            CatalogoMedicamento.ativo == True
        ).first()
        if not medicamento_catalogo:
            raise HTTPException(status_code=404, detail="Medicamento do catálogo não encontrado ou inativo")

    data_original = dados.data_evento
    data_ajustada_por_atendimento = None
    if dados.data_evento and not data_tem_atendimento(dados.data_evento):
        data_ajustada_por_atendimento = ajustar_para_proximo_dia_atendimento(dados.data_evento)
        dados.data_evento = data_ajustada_por_atendimento

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

    payload = dados.model_dump()
    payload["tipo_evento"] = payload.get("tipo_evento", "").upper()
    payload["prioridade"] = prioridade

    if medicamento_catalogo:
        payload["medicamento"] = medicamento_catalogo.descricao_completa

    agenda = AgendaIntegrada(
        **payload
    )

    db.add(agenda)
    db.commit()
    db.refresh(agenda)

    return {
        "mensagem": "Agendamento criado com sucesso.",
        "agenda": agenda,
        "alerta_capacidade": alerta_capacidade,
        "ajuste_atendimento": (
            {
                "data_original": data_original,
                "data_ajustada": data_ajustada_por_atendimento,
                "horarios": horarios_do_dia(data_ajustada_por_atendimento),
                "mensagem": "Data ajustada automaticamente para dia de atendimento da Farmácia Escola."
            }
            if data_ajustada_por_atendimento
            else None
        )
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

    if agenda.data_evento and not data_tem_atendimento(agenda.data_evento):
        agenda.data_evento = ajustar_para_proximo_dia_atendimento(agenda.data_evento)

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
    return svc_alertas_pendentes(db=db)

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
    termo_like = f"%{termo}%"

    pacientes = db.query(PacienteAgenda).filter(
        PacienteAgenda.ativo == True,
        (
            PacienteAgenda.nome.ilike(termo_like)
            | PacienteAgenda.cpf.ilike(termo_like)
            | PacienteAgenda.cns.ilike(termo_like)
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

@router.get("/alertas-clinicos-consolidados")
def alertas_clinicos_consolidados(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    return svc_alertas_clinicos_consolidados(db=db, current=current)

@router.post("/alertas-clinicos/resolver")
def resolver_alerta_clinico(
    dados: ResolucaoAlertaClinicoCreate,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    return svc_resolver_alerta_clinico(dados=dados, db=db, current=current)

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
    return svc_laudo_bioimpedancia_pdf(bioimpedancia_id=bioimpedancia_id, db=db, current=current)

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
    mes: int = None,
    ano: int = None,
    db: Session = Depends(get_db_consultorio)
):
    return svc_relatorio_mensal_consultorio(mes=mes, ano=ano, db=db)

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
    return svc_evolucao_farmaceutica_pdf(evolucao_id=evolucao_id, db=db, current=current)


@router.get("/paciente-clinico/{paciente_clinico_id}/plano-cuidado-pdf")
def plano_cuidado_pdf(
    paciente_clinico_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    return svc_plano_cuidado_pdf(paciente_clinico_id=paciente_clinico_id, db=db, current=current)


@router.get("/paciente-clinico/{paciente_clinico_id}/evolucoes-clinicas-pdf")
def evolucoes_clinicas_pdf(
    paciente_clinico_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    return svc_evolucoes_clinicas_pdf(paciente_clinico_id=paciente_clinico_id, db=db, current=current)


@router.get("/paciente-clinico/{paciente_clinico_id}/orientacoes-farmaceuticas-pdf")
def orientacoes_farmaceuticas_pdf(
    paciente_clinico_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    return svc_orientacoes_farmaceuticas_pdf(paciente_clinico_id=paciente_clinico_id, db=db, current=current)

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










