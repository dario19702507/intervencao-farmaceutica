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
from sqlalchemy import Column, Integer, String, Date, DateTime, Text, ForeignKey, Boolean, Float, func, or_
from collections import defaultdict
from openpyxl import Workbook


STATUS_ENCERRADOS_AGENDA = {"cancelado", "realizado", "concluido", "reagendado"}
STATUS_ATIVOS_AGENDA = {"agendado", "notificado", "retirada_prevista", "renovacao_recomendada", "renovacao_urgente", "risco_interrupcao_tratamento", "faltou"}
TIPOS_RETIRADA_AGENDA = {"retirada_medicamento", "retirada", "retirada_prevista", "dispensacao"}
TIPOS_RENOVACAO_AGENDA = {"renovacao_lme", "renovacao_laudo", "pendencia_documental"}

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
    AgendaHistorico,
    CatalogoMedicamento,
    PacienteCEAF,
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
    AgendaReagendarCreate,
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


def _adicionar_coluna_se_nao_existir(tabela: str, coluna: str, tipo: str) -> None:
    try:
        with engine.begin() as conn:
            dialecto = engine.dialect.name
            if dialecto == "sqlite":
                existentes = {linha[1] for linha in conn.execute(text(f"PRAGMA table_info({tabela})")).fetchall()}
                if coluna not in existentes:
                    conn.execute(text(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {tipo}"))
            else:
                conn.execute(text(f"ALTER TABLE {tabela} ADD COLUMN IF NOT EXISTS {coluna} {tipo}"))
    except Exception:
        # A expansão da agenda não deve impedir a inicialização do sistema.
        pass


def _garantir_colunas_agenda_ceaf() -> None:
    colunas = {
        "paciente_ceaf_id": "INTEGER",
        "paciente_clinico_id": "INTEGER",
        "data_original": "DATE",
        "motivo_reagendamento": "TEXT",
        "tipo_motivo_reagendamento": "VARCHAR",
        "reagendado_em": "TIMESTAMP",
        "reagendado_por": "VARCHAR",
    }
    for coluna, tipo in colunas.items():
        _adicionar_coluna_se_nao_existir("agenda_integrada", coluna, tipo)


def _usuario_atual_identificacao(current) -> str:
    return (
        getattr(current, "nome", None)
        or getattr(current, "email", None)
        or "sistema"
    )


def _telefone_ceaf(paciente: PacienteCEAF) -> Optional[str]:
    return paciente.telefone_celular or paciente.telefone or paciente.telefone_comercial


def _paciente_ceaf_resumo(paciente: PacienteCEAF) -> dict:
    return {
        "id": paciente.id,
        "nome": paciente.nome,
        "cpf": paciente.cpf,
        "cns": paciente.cns,
        "telefone": _telefone_ceaf(paciente),
        "telefone_celular": paciente.telefone_celular,
        "municipio": paciente.municipio,
        "logradouro": paciente.logradouro,
        "numero_residencia": paciente.numero_residencia,
        "complemento_residencia": paciente.complemento_residencia,
        "medicamento_prescrito": paciente.medicamento_prescrito,
        "situacao_lme": paciente.situacao_lme,
        "data_inicio_medicamento": paciente.data_inicio_medicamento,
        "data_fim_vigencia": paciente.data_fim_vigencia,
        "paciente_clinico_id": paciente.paciente_clinico_id,
        "paciente_agenda_id": paciente.paciente_agenda_id,
        "conversao_status": paciente.conversao_status,
    }


def _inicio_fim_mes(ano: Optional[int] = None, mes: Optional[int] = None) -> tuple[date, date]:
    hoje = date.today()
    ano = int(ano or hoje.year)
    mes = int(mes or hoje.month)
    if mes < 1 or mes > 12:
        raise HTTPException(status_code=400, detail="Mês inválido. Use valores entre 1 e 12.")
    inicio = date(ano, mes, 1)
    if mes == 12:
        fim = date(ano + 1, 1, 1) - timedelta(days=1)
    else:
        fim = date(ano, mes + 1, 1) - timedelta(days=1)
    return inicio, fim


def _status_normalizado(valor: Optional[str]) -> str:
    return (valor or "").strip().lower()


def _situacao_lme_vigente(paciente: PacienteCEAF, data_referencia: date) -> bool:
    situacao = (paciente.situacao_lme or "").strip().lower()
    if any(term in situacao for term in ["indefer", "cancel", "encerr", "suspens", "bloque"]):
        return False
    if paciente.data_fim_vigencia and paciente.data_fim_vigencia < data_referencia:
        return False
    return True


def _data_retirada_prevista_mes(inicio_mes: date, fim_mes: date, data_fim_vigencia: Optional[date]) -> Optional[date]:
    hoje = date.today()
    data_base = max(hoje, inicio_mes)
    if data_base > fim_mes:
        data_base = inicio_mes
    if not data_tem_atendimento(data_base):
        data_base = ajustar_para_proximo_dia_atendimento(data_base)
    if data_base > fim_mes:
        return None
    if data_fim_vigencia and data_base > data_fim_vigencia:
        return None
    return data_base


def _query_retiradas_ceaf_mes(db: Session, inicio_mes: date, fim_mes: date):
    """Retiradas vinculadas ao CEAF no mês, independentemente da origem visual.

    A conciliação não deve depender exclusivamente de servico_origem="CEAF",
    porque uma retirada pode ter sido cadastrada como dispensação, mas ainda
    estar vinculada ao paciente CEAF ou ao paciente clínico convertido.
    """
    return db.query(AgendaIntegrada).filter(
        func.lower(AgendaIntegrada.tipo_evento).in_(TIPOS_RETIRADA_AGENDA),
        AgendaIntegrada.data_evento >= inicio_mes,
        AgendaIntegrada.data_evento <= fim_mes,
        or_(
            AgendaIntegrada.paciente_ceaf_id.isnot(None),
            AgendaIntegrada.servico_origem == "CEAF",
            func.lower(AgendaIntegrada.servico_origem) == "dispensacao",
        ),
    )


def _retirada_ceaf_existente_mes(db: Session, paciente: PacienteCEAF, inicio_mes: date, fim_mes: date) -> Optional[AgendaIntegrada]:
    filtros_paciente = []
    if paciente.id:
        filtros_paciente.append(AgendaIntegrada.paciente_ceaf_id == paciente.id)
    if paciente.paciente_clinico_id:
        filtros_paciente.append(AgendaIntegrada.paciente_clinico_id == paciente.paciente_clinico_id)
    if paciente.paciente_agenda_id:
        filtros_paciente.append(AgendaIntegrada.paciente_id == paciente.paciente_agenda_id)
    if not filtros_paciente:
        return None
    return _query_retiradas_ceaf_mes(db, inicio_mes, fim_mes).filter(
        or_(*filtros_paciente),
        func.lower(AgendaIntegrada.status).in_(
            STATUS_ATIVOS_AGENDA.union({"realizado", "concluido", "reagendado"})
        )
    ).first()


def _mapear_retiradas_ceaf_mes(db: Session, inicio_mes: date, fim_mes: date) -> dict:
    """Mapeia retiradas CEAF do mês em uma única consulta.

    Evita uma consulta por paciente nas telas de resumo, conciliação e alertas.
    Esse ponto ficou crítico depois da importação CEAF e da geração de centenas
    de eventos de agenda.
    """
    registros = _query_retiradas_ceaf_mes(db, inicio_mes, fim_mes).with_entities(
        AgendaIntegrada.id,
        AgendaIntegrada.paciente_ceaf_id,
        AgendaIntegrada.paciente_clinico_id,
        AgendaIntegrada.paciente_id,
        AgendaIntegrada.status,
    ).all()

    por_ceaf = set()
    por_clinico = set()
    por_agenda = set()
    realizados_ceaf = set()
    status_counts = defaultdict(int)

    for item in registros:
        status_norm = _status_normalizado(item.status)
        status_counts[status_norm] += 1

        if item.paciente_ceaf_id:
            por_ceaf.add(item.paciente_ceaf_id)
            if status_norm in {"realizado", "concluido"}:
                realizados_ceaf.add(item.paciente_ceaf_id)
        if item.paciente_clinico_id:
            por_clinico.add(item.paciente_clinico_id)
        if item.paciente_id:
            por_agenda.add(item.paciente_id)

    return {
        "por_ceaf": por_ceaf,
        "por_clinico": por_clinico,
        "por_agenda": por_agenda,
        "realizados_ceaf": realizados_ceaf,
        "status_counts": status_counts,
    }


def _paciente_tem_retirada_mapeada(paciente: PacienteCEAF, mapa_retiradas: dict) -> bool:
    return (
        (paciente.id and paciente.id in mapa_retiradas.get("por_ceaf", set()))
        or (paciente.paciente_clinico_id and paciente.paciente_clinico_id in mapa_retiradas.get("por_clinico", set()))
        or (paciente.paciente_agenda_id and paciente.paciente_agenda_id in mapa_retiradas.get("por_agenda", set()))
    )


def _pendencia_renovacao_ceaf_existente(db: Session, paciente: PacienteCEAF) -> Optional[AgendaIntegrada]:
    return db.query(AgendaIntegrada).filter(
        AgendaIntegrada.servico_origem == "CEAF",
        AgendaIntegrada.paciente_ceaf_id == paciente.id,
        AgendaIntegrada.tipo_evento.in_(["RENOVACAO_LME", "PENDENCIA_DOCUMENTAL"]),
        AgendaIntegrada.status.in_(["agendado", "notificado", "reagendado", "retirada_prevista", "AGENDADO"]),
    ).first()


def _criar_pendencia_renovacao_ceaf(db: Session, paciente: PacienteCEAF, data_base: date, usuario: str) -> Optional[AgendaIntegrada]:
    if _pendencia_renovacao_ceaf_existente(db, paciente):
        return None
    data_evento = data_base
    if not data_tem_atendimento(data_evento):
        data_evento = ajustar_para_proximo_dia_atendimento(data_evento)
    agenda = AgendaIntegrada(
        servico_origem="CEAF",
        tipo_evento="RENOVACAO_LME",
        prioridade="URGENTE",
        status="agendado",
        titulo="Pendência de renovação LME - CEAF",
        paciente_id=paciente.paciente_agenda_id,
        paciente_ceaf_id=paciente.id,
        paciente_clinico_id=paciente.paciente_clinico_id,
        paciente_nome=paciente.nome,
        telefone=_telefone_ceaf(paciente),
        medicamento=paciente.medicamento_prescrito,
        situacao_laudo=paciente.situacao_lme,
        data_evento=data_evento,
        data_original=data_evento,
        data_inicio_vigencia=paciente.data_inicio_medicamento,
        data_fim_vigencia=paciente.data_fim_vigencia,
        referencia_tipo="CEAF",
        referencia_id=paciente.id,
        origem_importacao="CONCILIACAO_CEAF",
        observacoes="Pendência criada pela conciliação mensal: LME vencida ou sem vigência suficiente para retirada.",
        notificar_whatsapp=True,
    )
    db.add(agenda)
    db.flush()
    db.add(AgendaHistorico(
        agenda_id=agenda.id,
        acao="CONCILIACAO_CEAF_PENDENCIA_RENOVACAO",
        data_original=data_evento,
        nova_data=data_evento,
        status_original=None,
        novo_status=agenda.status,
        motivo="Bloqueio de retirada por LME vencida ou vigência insuficiente.",
        tipo_motivo="sistema",
        usuario=usuario,
    ))
    return agenda


def _montar_resumo_conciliacao_ceaf(db: Session, inicio_mes: date, fim_mes: date) -> dict:
    """Resumo da conciliação CEAF com consultas agregadas.

    A versão anterior percorria todos os pacientes e fazia busca individual de
    retirada para cada um. Em produção/Supabase isso gerava lentidão severa nas
    abas de Agenda e Conciliação.
    """
    pacientes_ativos_query = db.query(PacienteCEAF).filter(
        or_(PacienteCEAF.ativo == True, PacienteCEAF.ativo.is_(None))
    )
    pacientes_ativos = pacientes_ativos_query.count()

    mapa_retiradas = _mapear_retiradas_ceaf_mes(db, inicio_mes, fim_mes)
    status_counts = mapa_retiradas["status_counts"]

    hoje = date.today()
    em_30_dias = hoje + timedelta(days=30)
    lme_vencidas = pacientes_ativos_query.filter(
        PacienteCEAF.data_fim_vigencia.isnot(None),
        PacienteCEAF.data_fim_vigencia < hoje,
    ).count()
    lme_vencendo_30 = pacientes_ativos_query.filter(
        PacienteCEAF.data_fim_vigencia.isnot(None),
        PacienteCEAF.data_fim_vigencia >= hoje,
        PacienteCEAF.data_fim_vigencia <= em_30_dias,
    ).count()

    pacientes_minimos = pacientes_ativos_query.with_entities(
        PacienteCEAF.id,
        PacienteCEAF.nome,
        PacienteCEAF.paciente_clinico_id,
        PacienteCEAF.paciente_agenda_id,
        PacienteCEAF.situacao_lme,
        PacienteCEAF.data_fim_vigencia,
    ).all()

    sem_retirada_prevista = 0
    bloqueados_lme = 0
    for paciente in pacientes_minimos:
        data_prevista = _data_retirada_prevista_mes(inicio_mes, fim_mes, paciente.data_fim_vigencia)
        if not _situacao_lme_vigente(paciente, data_prevista or max(date.today(), inicio_mes)):
            bloqueados_lme += 1
            continue
        if not _paciente_tem_retirada_mapeada(paciente, mapa_retiradas):
            sem_retirada_prevista += 1

    return {
        "periodo": {"inicio": inicio_mes, "fim": fim_mes},
        "pacientes_ceaf_ativos": pacientes_ativos,
        "retiradas_previstas": status_counts.get("retirada_prevista", 0),
        "retiradas_agendadas": status_counts.get("agendado", 0) + status_counts.get("notificado", 0) + status_counts.get("reagendado", 0),
        "retiradas_realizadas": status_counts.get("realizado", 0) + status_counts.get("concluido", 0),
        "retiradas_canceladas": status_counts.get("cancelado", 0),
        "faltosos": status_counts.get("faltou", 0),
        "sem_retirada_prevista": sem_retirada_prevista,
        "bloqueados_por_lme": bloqueados_lme,
        "lme_vencidas": lme_vencidas,
        "lme_vencendo_30_dias": lme_vencendo_30,
    }


PRIORIDADE_CEAF_PESO = {
    "critico": 0,
    "urgente": 1,
    "atencao": 2,
    "informativo": 3,
}


def _prioridade_ceaf_para_alerta(prioridade_ceaf: str) -> str:
    """Mapeia a prioridade CEAF para a escala já usada na visão geral."""
    prioridade = (prioridade_ceaf or "informativo").lower()
    if prioridade in {"critico", "urgente"}:
        return "alta"
    if prioridade == "atencao":
        return "moderada"
    return "baixa"


def _alerta_ceaf(
    *,
    tipo_alerta: str,
    prioridade_ceaf: str,
    mensagem: str,
    paciente: Optional[PacienteCEAF] = None,
    evento: Optional[AgendaIntegrada] = None,
    data_referencia: Optional[date] = None,
    acao_sugerida: Optional[str] = None,
) -> dict:
    paciente_nome = None
    telefone = None
    medicamento = None
    paciente_ceaf_id = None
    paciente_clinico_id = None
    agenda_id = None
    data_fim_vigencia = None

    if paciente is not None:
        paciente_nome = paciente.nome
        telefone = _telefone_ceaf(paciente)
        medicamento = paciente.medicamento_prescrito
        paciente_ceaf_id = paciente.id
        paciente_clinico_id = paciente.paciente_clinico_id
        data_fim_vigencia = paciente.data_fim_vigencia

    if evento is not None:
        paciente_nome = paciente_nome or evento.paciente_nome
        telefone = telefone or evento.telefone
        medicamento = medicamento or evento.medicamento
        paciente_ceaf_id = paciente_ceaf_id or evento.paciente_ceaf_id
        paciente_clinico_id = paciente_clinico_id or evento.paciente_clinico_id
        agenda_id = evento.id
        data_fim_vigencia = data_fim_vigencia or evento.data_fim_vigencia

    return {
        "origem": "CEAF",
        "tipo_alerta": tipo_alerta,
        "prioridade": _prioridade_ceaf_para_alerta(prioridade_ceaf),
        "prioridade_ceaf": prioridade_ceaf,
        "mensagem": mensagem,
        "paciente_ceaf_id": paciente_ceaf_id,
        "paciente_clinico_id": paciente_clinico_id,
        "paciente_id": paciente_clinico_id,
        "paciente_nome": paciente_nome or "Não informado",
        "telefone": telefone,
        "medicamento": medicamento,
        "agenda_id": agenda_id,
        "data_referencia": data_referencia,
        "data_fim_vigencia": data_fim_vigencia,
        "acao_sugerida": acao_sugerida,
    }


def _ordenar_alertas_ceaf(alertas: list[dict]) -> list[dict]:
    return sorted(
        alertas,
        key=lambda item: (
            PRIORIDADE_CEAF_PESO.get(str(item.get("prioridade_ceaf", "informativo")).lower(), 9),
            item.get("data_referencia") or date.max,
            str(item.get("paciente_nome") or ""),
        ),
    )


def _resumo_alertas_ceaf(alertas: list[dict]) -> dict:
    resumo = {
        "total": len(alertas),
        "critico": 0,
        "urgente": 0,
        "atencao": 0,
        "informativo": 0,
        "por_tipo": defaultdict(int),
    }
    for alerta in alertas:
        prioridade = str(alerta.get("prioridade_ceaf") or "informativo").lower()
        if prioridade in resumo:
            resumo[prioridade] += 1
        resumo["por_tipo"][alerta.get("tipo_alerta") or "outro"] += 1
    resumo["por_tipo"] = dict(resumo["por_tipo"])
    return resumo


def _coletar_alertas_ceaf(db: Session, limite: int = 120) -> list[dict]:
    """Gera alertas CEAF sem criar registros e sem consultas paciente a paciente."""
    hoje = date.today()
    amanha = hoje + timedelta(days=1)
    em_7_dias = hoje + timedelta(days=7)
    em_15_dias = hoje + timedelta(days=15)
    em_30_dias = hoje + timedelta(days=30)
    inicio_mes, fim_mes = _inicio_fim_mes(hoje.year, hoje.month)
    alertas: list[dict] = []

    pacientes_query = db.query(PacienteCEAF).filter(
        or_(PacienteCEAF.ativo == True, PacienteCEAF.ativo.is_(None))
    )

    # Prioriza pacientes com LME vencida/a vencer e limita a carga inicial.
    pacientes = pacientes_query.order_by(
        PacienteCEAF.data_fim_vigencia.asc().nullslast(),
        PacienteCEAF.nome.asc(),
    ).limit(max(1, min(limite * 2, 800))).all()

    mapa_retiradas = _mapear_retiradas_ceaf_mes(db, inicio_mes, fim_mes)

    for paciente in pacientes:
        if paciente.data_fim_vigencia:
            dias_vigencia = (paciente.data_fim_vigencia - hoje).days
            if dias_vigencia < 0:
                alertas.append(_alerta_ceaf(
                    tipo_alerta="ceaf_lme_vencida",
                    prioridade_ceaf="critico",
                    paciente=paciente,
                    data_referencia=paciente.data_fim_vigencia,
                    mensagem=(
                        f"LME vencida em {paciente.data_fim_vigencia.strftime('%d/%m/%Y')}. "
                        "Bloquear retirada e orientar renovação."
                    ),
                    acao_sugerida="Criar/confirmar pendência de renovação de LME.",
                ))
            elif paciente.data_fim_vigencia <= em_7_dias:
                alertas.append(_alerta_ceaf(
                    tipo_alerta="ceaf_lme_vence_7_dias",
                    prioridade_ceaf="urgente",
                    paciente=paciente,
                    data_referencia=paciente.data_fim_vigencia,
                    mensagem=f"LME vence em {dias_vigencia} dia(s). Priorizar contato para renovação.",
                    acao_sugerida="Orientar renovação imediata.",
                ))
            elif paciente.data_fim_vigencia <= em_15_dias:
                alertas.append(_alerta_ceaf(
                    tipo_alerta="ceaf_lme_vence_15_dias",
                    prioridade_ceaf="urgente",
                    paciente=paciente,
                    data_referencia=paciente.data_fim_vigencia,
                    mensagem=f"LME vence em {dias_vigencia} dia(s). Programar renovação.",
                    acao_sugerida="Agendar renovação de LME.",
                ))
            elif paciente.data_fim_vigencia <= em_30_dias:
                alertas.append(_alerta_ceaf(
                    tipo_alerta="ceaf_lme_vence_30_dias",
                    prioridade_ceaf="atencao",
                    paciente=paciente,
                    data_referencia=paciente.data_fim_vigencia,
                    mensagem=f"LME vence em {dias_vigencia} dia(s). Recomendar início da renovação.",
                    acao_sugerida="Preparar documentação de renovação.",
                ))

        if _situacao_lme_vigente(paciente, hoje) and not _paciente_tem_retirada_mapeada(paciente, mapa_retiradas):
            alertas.append(_alerta_ceaf(
                tipo_alerta="ceaf_sem_retirada_no_mes",
                prioridade_ceaf="atencao",
                paciente=paciente,
                data_referencia=hoje,
                mensagem="Paciente CEAF ativo sem retirada prevista, agendada ou realizada no mês corrente.",
                acao_sugerida="Avaliar conciliação e agendamento de retirada.",
            ))

    retiradas_base = _query_retiradas_ceaf_mes(db, inicio_mes, fim_mes).filter(
        func.lower(AgendaIntegrada.status).in_(STATUS_ATIVOS_AGENDA)
    ).order_by(AgendaIntegrada.data_evento.asc()).limit(max(1, min(limite * 2, 800))).all()

    for evento in retiradas_base:
        status = _status_normalizado(evento.status)
        data_evento = evento.data_evento
        if not data_evento:
            continue
        if data_evento < hoje and status in {"agendado", "notificado", "retirada_prevista", "faltou"}:
            alertas.append(_alerta_ceaf(
                tipo_alerta="ceaf_retirada_atrasada",
                prioridade_ceaf="urgente",
                evento=evento,
                data_referencia=data_evento,
                mensagem=f"Retirada de medicamento atrasada desde {data_evento.strftime('%d/%m/%Y')}.",
                acao_sugerida="Contatar paciente, reagendar ou registrar falta.",
            ))
        elif data_evento == hoje and status in {"agendado", "notificado", "retirada_prevista"}:
            alertas.append(_alerta_ceaf(
                tipo_alerta="ceaf_retirada_hoje",
                prioridade_ceaf="informativo",
                evento=evento,
                data_referencia=data_evento,
                mensagem="Retirada prevista para hoje.",
                acao_sugerida="Confirmar comparecimento ou registrar retirada.",
            ))
        elif data_evento == amanha and status in {"agendado", "notificado", "retirada_prevista"}:
            alertas.append(_alerta_ceaf(
                tipo_alerta="ceaf_retirada_amanha",
                prioridade_ceaf="informativo",
                evento=evento,
                data_referencia=data_evento,
                mensagem="Retirada prevista para amanhã.",
                acao_sugerida="Preparar notificação/lembrete.",
            ))

    return _ordenar_alertas_ceaf(alertas)[:max(1, limite)]


def _alertas_ceaf_para_notificacoes(alertas: list[dict]) -> list[dict]:
    notificacoes = []
    for alerta in alertas:
        telefone = alerta.get("telefone")
        if not telefone:
            continue
        tipo = alerta.get("tipo_alerta")
        paciente_nome = alerta.get("paciente_nome") or "Paciente"
        medicamento = alerta.get("medicamento") or "medicamento"
        data_ref = alerta.get("data_referencia") or alerta.get("data_fim_vigencia")
        data_fmt = data_ref.strftime("%d/%m/%Y") if hasattr(data_ref, "strftime") else None

        if tipo in {"ceaf_lme_vencida", "ceaf_lme_vence_7_dias", "ceaf_lme_vence_15_dias", "ceaf_lme_vence_30_dias"}:
            mensagem = (
                f"Olá, {paciente_nome}. A Farmácia Escola informa que a vigência da sua LME "
                f"{('vence em ' + data_fmt) if data_fmt else 'precisa ser conferida'}. "
                "Procure a equipe para orientação sobre renovação e continuidade do tratamento."
            )
            tipo_notificacao = "ceaf_renovacao_lme"
        elif tipo in {"ceaf_retirada_amanha", "ceaf_retirada_hoje", "ceaf_retirada_atrasada", "ceaf_sem_retirada_no_mes"}:
            mensagem = (
                f"Olá, {paciente_nome}. A Farmácia Escola identificou pendência relacionada à retirada de "
                f"{medicamento}. Procure a equipe para confirmação, reagendamento ou orientação."
            )
            tipo_notificacao = "ceaf_retirada"
        else:
            mensagem = f"Olá, {paciente_nome}. A Farmácia Escola possui uma orientação pendente para você."
            tipo_notificacao = "ceaf_alerta"

        notificacoes.append({
            "agenda_id": alerta.get("agenda_id"),
            "paciente_ceaf_id": alerta.get("paciente_ceaf_id"),
            "paciente_clinico_id": alerta.get("paciente_clinico_id"),
            "paciente_nome": paciente_nome,
            "telefone": telefone,
            "medicamento": medicamento,
            "prioridade": alerta.get("prioridade_ceaf"),
            "tipo_alerta": tipo,
            "tipo_notificacao": tipo_notificacao,
            "mensagem": mensagem,
            "data_programada": date.today(),
        })
    return notificacoes


def _gerar_notificacoes_ceaf_agenda(db: Session, limite: int = 120) -> dict:
    """Materializa alertas CEAF na tabela de notificações da agenda.

    Usado pela aba Notificações para preparar mensagens, sem disparo automático
    de WhatsApp durante a homologação.
    """
    notificacoes = _alertas_ceaf_para_notificacoes(_coletar_alertas_ceaf(db, limite=limite))
    criadas = 0
    ignoradas = 0

    for item in notificacoes:
        query = db.query(NotificacaoAgenda).filter(
            NotificacaoAgenda.tipo_notificacao == item["tipo_notificacao"],
            NotificacaoAgenda.status.in_(["pendente", "enviada"]),
        )
        if item.get("agenda_id"):
            query = query.filter(NotificacaoAgenda.agenda_id == item.get("agenda_id"))
        else:
            query = query.filter(
                NotificacaoAgenda.paciente_nome == item.get("paciente_nome"),
                NotificacaoAgenda.telefone == item.get("telefone"),
            )

        if query.first():
            ignoradas += 1
            continue

        db.add(NotificacaoAgenda(
            agenda_id=item.get("agenda_id"),
            paciente_nome=item.get("paciente_nome"),
            telefone=item.get("telefone"),
            tipo_notificacao=item.get("tipo_notificacao"),
            mensagem=item.get("mensagem"),
            data_programada=item.get("data_programada") or date.today(),
            status="pendente",
            canal="whatsapp_preparacao",
        ))
        criadas += 1

    db.commit()
    return {
        "notificacoes_ceaf_criadas": criadas,
        "notificacoes_ceaf_ignoradas": ignoradas,
    }

_garantir_colunas_agenda_ceaf()











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

    tipos_validos = {
        "INCLUSAO", "RETIRADA", "RENOVACAO", "ADEQUACAO", "ENCERRAMENTO",
        "RETIRADA_MEDICAMENTO", "RENOVACAO_LME", "RENOVACAO_LAUDO",
        "CONSULTA_FARMACEUTICA", "SERVICO_RAPIDO", "PENDENCIA_DOCUMENTAL",
        "RISCO_PERDA_MEDICACAO", "RISCO_ENCERRAMENTO_PROCESSO",
        "RETORNO_PLANO_CUIDADO", "RETORNO_INTERVENCAO"
    }
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

    paciente_ceaf = None
    if payload.get("paciente_ceaf_id"):
        paciente_ceaf = db.query(PacienteCEAF).filter(PacienteCEAF.id == payload["paciente_ceaf_id"]).first()
        if not paciente_ceaf:
            raise HTTPException(status_code=404, detail="Paciente CEAF não encontrado")

        payload["paciente_nome"] = payload.get("paciente_nome") or paciente_ceaf.nome
        payload["telefone"] = payload.get("telefone") or _telefone_ceaf(paciente_ceaf)
        payload["paciente_clinico_id"] = payload.get("paciente_clinico_id") or paciente_ceaf.paciente_clinico_id
        payload["paciente_id"] = payload.get("paciente_id") or paciente_ceaf.paciente_agenda_id
        payload["medicamento"] = payload.get("medicamento") or paciente_ceaf.medicamento_prescrito
        payload["situacao_laudo"] = payload.get("situacao_laudo") or paciente_ceaf.situacao_lme
        payload["data_inicio_vigencia"] = payload.get("data_inicio_vigencia") or paciente_ceaf.data_inicio_medicamento
        payload["data_fim_vigencia"] = payload.get("data_fim_vigencia") or paciente_ceaf.data_fim_vigencia
        payload["referencia_tipo"] = payload.get("referencia_tipo") or "CEAF"
        payload["referencia_id"] = payload.get("referencia_id") or paciente_ceaf.id
        payload["servico_origem"] = payload.get("servico_origem") or "CEAF"

    if medicamento_catalogo:
        payload["medicamento"] = medicamento_catalogo.descricao_completa

    if payload.get("data_evento"):
        payload["data_original"] = payload.get("data_evento")

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
    origem: Optional[str] = None,
    tipo_evento: Optional[str] = None,
    paciente: Optional[str] = None,
    somente_ativos: bool = True,
    limit: int = 150,
    offset: int = 0,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    """Lista agenda com limites de produção.

    A agenda passou a ter centenas de eventos CEAF; por isso a listagem agora
    aplica limite/paginação e filtro de ativos por padrão. Use
    somente_ativos=false quando precisar consultar encerrados.
    """
    query = db.query(AgendaIntegrada)

    if data_inicio:
        query = query.filter(AgendaIntegrada.data_evento >= data_inicio)

    if data_fim:
        query = query.filter(AgendaIntegrada.data_evento <= data_fim)

    if status:
        query = query.filter(func.lower(AgendaIntegrada.status) == status.lower())
    elif somente_ativos:
        query = query.filter(func.lower(AgendaIntegrada.status).notin_(STATUS_ENCERRADOS_AGENDA))

    if origem:
        query = query.filter(func.lower(AgendaIntegrada.servico_origem) == origem.lower())

    if tipo_evento:
        query = query.filter(func.lower(AgendaIntegrada.tipo_evento) == tipo_evento.lower())

    if paciente and paciente.strip():
        termo = f"%{paciente.strip().lower()}%"
        query = query.filter(or_(
            func.lower(AgendaIntegrada.paciente_nome).like(termo),
            func.lower(AgendaIntegrada.telefone).like(termo),
            func.lower(AgendaIntegrada.medicamento).like(termo),
            func.lower(AgendaIntegrada.situacao_laudo).like(termo),
        ))

    total = query.count()
    limite_seguro = max(1, min(limit or 150, 500))
    offset_seguro = max(0, offset or 0)
    eventos = query.order_by(
        AgendaIntegrada.data_evento.asc().nullslast(),
        AgendaIntegrada.id.desc(),
    ).offset(offset_seguro).limit(limite_seguro).all()

    return {
        "total": total,
        "limit": limite_seguro,
        "offset": offset_seguro,
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

    notificacoes_ceaf = _alertas_ceaf_para_notificacoes(_coletar_alertas_ceaf(db, limite=300))
    notificacoes.extend(notificacoes_ceaf)

    return {
        "total": len(notificacoes),
        "notificacoes": notificacoes,
        "ceaf_total": len(notificacoes_ceaf),
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

    data_anterior = agenda.data_evento
    status_anterior = agenda.status

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

    if dados.data_evento and data_anterior != agenda.data_evento:
        if not agenda.data_original:
            agenda.data_original = data_anterior
        historico = AgendaHistorico(
            agenda_id=agenda.id,
            acao="ALTERACAO_DATA",
            data_original=data_anterior,
            nova_data=agenda.data_evento,
            status_original=status_anterior,
            novo_status=agenda.status,
            motivo=agenda.motivo_reagendamento or "Alteração manual de data",
            tipo_motivo=agenda.tipo_motivo_reagendamento or "equipe",
            usuario=_usuario_atual_identificacao(current),
        )
        db.add(historico)

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

    status_anterior = agenda.status
    agenda.status = dados.status

    agenda.data_status = datetime.utcnow()

    try:
        agenda.usuario_status = getattr(current, "nome", None) or getattr(current, "email", None) or "sistema"
    except: agenda.usuario_status = "sistema"
    if dados.observacoes:
        agenda.observacoes = dados.observacoes

    agenda.atualizado_em = datetime.utcnow()

    if status_anterior != agenda.status:
        db.add(AgendaHistorico(
            agenda_id=agenda.id,
            acao="ALTERACAO_STATUS",
            data_original=agenda.data_evento,
            nova_data=agenda.data_evento,
            status_original=status_anterior,
            novo_status=agenda.status,
            motivo=dados.observacoes,
            tipo_motivo="equipe",
            usuario=_usuario_atual_identificacao(current),
        ))

    proximo_agendamento = None

    servico_normalizado = (agenda.servico_origem or "").strip().lower()
    status_normalizado = (dados.status or "").strip().lower()

    tipo_normalizado = (agenda.tipo_evento or "").strip().lower()

    if (
        status_normalizado == "realizado"
        and (
            servico_normalizado in ["dispensacao", "dispensação", "ceaf"]
            or tipo_normalizado in TIPOS_RETIRADA_AGENDA
        )
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



@router.get("/agenda/pacientes-ceaf/buscar")
def buscar_pacientes_ceaf_agenda(
    termo: str,
    limite: int = 30,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    if not termo or len(termo.strip()) < 3:
        return {"total": 0, "pacientes": []}

    termo_limpo = termo.strip()
    termo_like = f"%{termo_limpo}%"
    somente_digitos = "".join(ch for ch in termo_limpo if ch.isdigit())

    # Registros importados antes da coluna ativo podem estar com NULL no PostgreSQL.
    # Para a agenda, consideramos ativos tanto True quanto NULL, e excluímos apenas False.
    query = db.query(PacienteCEAF).filter(or_(PacienteCEAF.ativo == True, PacienteCEAF.ativo.is_(None)))
    filtros = [PacienteCEAF.nome.ilike(termo_like), PacienteCEAF.medicamento_prescrito.ilike(termo_like)]
    if somente_digitos:
        digitos_like = f"%{somente_digitos}%"
        filtros.extend([PacienteCEAF.cpf.ilike(digitos_like), PacienteCEAF.cns.ilike(digitos_like)])

    pacientes = query.filter(or_(*filtros)).order_by(PacienteCEAF.nome.asc()).limit(max(1, min(limite, 100))).all()
    return {"total": len(pacientes), "pacientes": [_paciente_ceaf_resumo(p) for p in pacientes]}


@router.get("/agenda/pacientes-ceaf/{paciente_ceaf_id}/contexto")
def obter_contexto_paciente_ceaf_agenda(
    paciente_ceaf_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    paciente = db.query(PacienteCEAF).filter(PacienteCEAF.id == paciente_ceaf_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente CEAF não encontrado")

    agenda_aberta = db.query(AgendaIntegrada).filter(
        AgendaIntegrada.paciente_ceaf_id == paciente.id,
        AgendaIntegrada.status.in_(["agendado", "notificado", "reagendado", "AGENDADO"]),
    ).order_by(AgendaIntegrada.data_evento.asc()).limit(10).all()

    sugestao_data = None
    tipo_sugerido = "RETIRADA_MEDICAMENTO"
    if paciente.data_fim_vigencia:
        tipo_sugerido = "RENOVACAO_LME"
        sugestao_data = paciente.data_fim_vigencia - timedelta(days=30)
        if sugestao_data < date.today():
            sugestao_data = date.today()
        if not data_tem_atendimento(sugestao_data):
            sugestao_data = ajustar_para_proximo_dia_atendimento(sugestao_data)

    return {
        "paciente": _paciente_ceaf_resumo(paciente),
        "sugestao": {
            "tipo_evento": tipo_sugerido,
            "servico_origem": "CEAF",
            "data_evento": sugestao_data,
            "prioridade": "URGENTE" if paciente.data_fim_vigencia and paciente.data_fim_vigencia <= date.today() + timedelta(days=15) else "NORMAL",
        },
        "agenda_aberta": agenda_aberta,
    }


@router.post("/agenda/gerar-ceaf")
def gerar_agenda_ceaf_automatica(
    dias_antes_vigencia: int = 30,
    limite: int = 1000,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    exigir_farmaceutico_ou_admin(current)

    hoje = date.today()
    pacientes = db.query(PacienteCEAF).filter(
        PacienteCEAF.ativo == True,
        PacienteCEAF.data_fim_vigencia.isnot(None),
    ).order_by(PacienteCEAF.data_fim_vigencia.asc()).limit(max(1, min(limite, 5000))).all()

    criados = 0
    existentes = 0
    ignorados = 0
    exemplos = []

    for paciente in pacientes:
        data_base = paciente.data_fim_vigencia - timedelta(days=max(0, min(dias_antes_vigencia, 120)))
        if data_base < hoje:
            data_base = hoje
        if not data_tem_atendimento(data_base):
            data_base = ajustar_para_proximo_dia_atendimento(data_base)

        existente = db.query(AgendaIntegrada).filter(
            AgendaIntegrada.paciente_ceaf_id == paciente.id,
            AgendaIntegrada.tipo_evento.in_(["RENOVACAO_LME", "RENOVACAO_LAUDO"]),
            AgendaIntegrada.status.in_(["agendado", "notificado", "reagendado", "AGENDADO"]),
        ).first()
        if existente:
            existentes += 1
            continue

        if not paciente.nome:
            ignorados += 1
            continue

        prioridade = "URGENTE" if paciente.data_fim_vigencia <= hoje + timedelta(days=15) else "NORMAL"
        agenda = AgendaIntegrada(
            servico_origem="CEAF",
            tipo_evento="RENOVACAO_LME",
            prioridade=prioridade,
            titulo="Renovação de LME - CEAF",
            paciente_id=paciente.paciente_agenda_id,
            paciente_ceaf_id=paciente.id,
            paciente_clinico_id=paciente.paciente_clinico_id,
            paciente_nome=paciente.nome,
            telefone=_telefone_ceaf(paciente),
            medicamento=paciente.medicamento_prescrito,
            situacao_laudo=paciente.situacao_lme,
            data_evento=data_base,
            data_original=data_base,
            data_inicio_vigencia=paciente.data_inicio_medicamento,
            data_fim_vigencia=paciente.data_fim_vigencia,
            referencia_tipo="CEAF",
            referencia_id=paciente.id,
            origem_importacao="CEAF_AUTOMATICO",
            observacoes="Agendamento automático gerado a partir da vigência CEAF.",
            notificar_whatsapp=True,
        )
        db.add(agenda)
        criados += 1
        if len(exemplos) < 5:
            exemplos.append({"paciente": paciente.nome, "data_evento": data_base, "medicamento": paciente.medicamento_prescrito})

    db.commit()
    return {"mensagem": "Agenda CEAF processada", "criados": criados, "existentes": existentes, "ignorados": ignorados, "exemplos": exemplos}


@router.post("/agenda/{agenda_id}/reagendar")
def reagendar_agendamento(
    agenda_id: int,
    dados: AgendaReagendarCreate,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    agenda = db.query(AgendaIntegrada).filter(AgendaIntegrada.id == agenda_id).first()
    if not agenda:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")
    if dados.nova_data < date.today():
        raise HTTPException(status_code=400, detail="Não é permitido reagendar para data passada.")
    if not dados.motivo or not dados.motivo.strip():
        raise HTTPException(status_code=400, detail="Informe o motivo do reagendamento.")

    data_original = agenda.data_evento
    status_original = agenda.status
    nova_data = dados.nova_data
    data_ajustada = None
    if not data_tem_atendimento(nova_data):
        data_ajustada = ajustar_para_proximo_dia_atendimento(nova_data)
        nova_data = data_ajustada

    if not agenda.data_original:
        agenda.data_original = data_original
    agenda.data_evento = nova_data
    agenda.status = "reagendado"
    agenda.motivo_reagendamento = dados.motivo.strip()
    agenda.tipo_motivo_reagendamento = (dados.tipo_motivo or "equipe").strip().lower()
    agenda.reagendado_em = datetime.utcnow()
    agenda.reagendado_por = _usuario_atual_identificacao(current)
    agenda.atualizado_em = datetime.utcnow()
    if dados.observacoes:
        agenda.observacoes = f"{agenda.observacoes or ''}\nReagendamento: {dados.observacoes}".strip()

    db.add(AgendaHistorico(
        agenda_id=agenda.id,
        acao="REAGENDAMENTO",
        data_original=data_original,
        nova_data=nova_data,
        status_original=status_original,
        novo_status="reagendado",
        motivo=dados.motivo.strip(),
        tipo_motivo=(dados.tipo_motivo or "equipe").strip().lower(),
        usuario=_usuario_atual_identificacao(current),
    ))
    db.commit()
    db.refresh(agenda)
    return {"mensagem": "Agendamento reagendado.", "agenda": agenda, "data_ajustada": data_ajustada}


@router.get("/agenda/{agenda_id}/historico")
def listar_historico_agendamento(
    agenda_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    agenda = db.query(AgendaIntegrada).filter(AgendaIntegrada.id == agenda_id).first()
    if not agenda:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")
    historico = db.query(AgendaHistorico).filter(AgendaHistorico.agenda_id == agenda_id).order_by(AgendaHistorico.criado_em.desc()).all()
    return {"agenda_id": agenda_id, "total": len(historico), "historico": historico}



@router.get("/agenda/conciliacao-ceaf/resumo")
def resumo_conciliacao_ceaf(
    ano: Optional[int] = None,
    mes: Optional[int] = None,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    """Resumo operacional da conciliação mensal de retiradas CEAF.

    Não altera dados. Serve para avaliar o mês antes de sincronizar a agenda.
    """
    inicio_mes, fim_mes = _inicio_fim_mes(ano, mes)
    return _montar_resumo_conciliacao_ceaf(db, inicio_mes, fim_mes)


@router.post("/agenda/conciliacao-ceaf/sincronizar")
def sincronizar_retiradas_ceaf(
    ano: Optional[int] = None,
    mes: Optional[int] = None,
    limite: int = 5000,
    criar_pendencia_renovacao: bool = True,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    """Concilia retiradas mensais CEAF sem duplicar eventos já existentes.

    Regras principais:
    - paciente CEAF ativo + LME vigente + sem retirada no mês => cria retirada_prevista;
    - LME vencida/insuficiente => não cria retirada e pode criar pendência de renovação;
    - retirada já agendada/realizada/reagendada no mês => não duplica.
    """
    exigir_farmaceutico_ou_admin(current)

    inicio_mes, fim_mes = _inicio_fim_mes(ano, mes)
    usuario = _usuario_atual_identificacao(current)
    hoje = date.today()

    pacientes = db.query(PacienteCEAF).filter(
        or_(PacienteCEAF.ativo == True, PacienteCEAF.ativo.is_(None))
    ).order_by(PacienteCEAF.nome.asc()).limit(max(1, min(limite, 20000))).all()

    criadas_previstas = 0
    ja_existentes = 0
    ja_realizadas = 0
    bloqueadas_lme = 0
    pendencias_criadas = 0
    ignoradas_sem_dados = 0
    exemplos_criados = []
    exemplos_bloqueados = []

    for paciente in pacientes:
        if not paciente.nome:
            ignoradas_sem_dados += 1
            continue

        data_prevista = _data_retirada_prevista_mes(inicio_mes, fim_mes, paciente.data_fim_vigencia)
        referencia_vigencia = data_prevista or max(hoje, inicio_mes)

        if not _situacao_lme_vigente(paciente, referencia_vigencia):
            bloqueadas_lme += 1
            if criar_pendencia_renovacao:
                pendencia = _criar_pendencia_renovacao_ceaf(
                    db=db,
                    paciente=paciente,
                    data_base=max(hoje, inicio_mes),
                    usuario=usuario,
                )
                if pendencia is not None:
                    pendencias_criadas += 1
            if len(exemplos_bloqueados) < 8:
                exemplos_bloqueados.append({
                    "paciente": paciente.nome,
                    "medicamento": paciente.medicamento_prescrito,
                    "situacao_lme": paciente.situacao_lme,
                    "data_fim_vigencia": paciente.data_fim_vigencia,
                    "motivo": "LME vencida ou vigência insuficiente para retirada no mês",
                })
            continue

        existente = _retirada_ceaf_existente_mes(db, paciente, inicio_mes, fim_mes)
        if existente:
            status_existente = _status_normalizado(existente.status)
            if status_existente in ["realizado", "concluido"]:
                ja_realizadas += 1
            else:
                ja_existentes += 1
            continue

        if not data_prevista:
            bloqueadas_lme += 1
            continue

        agenda = AgendaIntegrada(
            servico_origem="dispensacao",
            tipo_evento="retirada_medicamento",
            prioridade="NORMAL",
            status="retirada_prevista",
            titulo="Retirada prevista de medicamento",
            paciente_id=paciente.paciente_agenda_id,
            paciente_ceaf_id=paciente.id,
            paciente_clinico_id=paciente.paciente_clinico_id,
            paciente_nome=paciente.nome,
            telefone=_telefone_ceaf(paciente),
            medicamento=paciente.medicamento_prescrito,
            situacao_laudo=paciente.situacao_lme,
            data_evento=data_prevista,
            data_original=data_prevista,
            data_inicio_vigencia=paciente.data_inicio_medicamento,
            data_fim_vigencia=paciente.data_fim_vigencia,
            referencia_tipo="CEAF",
            referencia_id=paciente.id,
            origem_importacao="CONCILIACAO_CEAF",
            observacoes="Retirada prevista criada pela conciliação mensal CEAF. Deve ser confirmada, reagendada, concluída ou cancelada pela equipe.",
            notificar_whatsapp=True,
        )
        db.add(agenda)
        db.flush()
        db.add(AgendaHistorico(
            agenda_id=agenda.id,
            acao="CONCILIACAO_CEAF_RETIRADA_PREVISTA",
            data_original=data_prevista,
            nova_data=data_prevista,
            status_original=None,
            novo_status="retirada_prevista",
            motivo="Retirada mensal prevista criada automaticamente pela conciliação CEAF.",
            tipo_motivo="sistema",
            usuario=usuario,
        ))
        criadas_previstas += 1
        if len(exemplos_criados) < 8:
            exemplos_criados.append({
                "paciente": paciente.nome,
                "data_evento": data_prevista,
                "medicamento": paciente.medicamento_prescrito,
                "vigencia": paciente.data_fim_vigencia,
            })

    db.commit()

    resumo = _montar_resumo_conciliacao_ceaf(db, inicio_mes, fim_mes)
    return {
        "mensagem": "Conciliação mensal CEAF concluída.",
        "periodo": {"inicio": inicio_mes, "fim": fim_mes},
        "processados": len(pacientes),
        "retiradas_previstas_criadas": criadas_previstas,
        "retiradas_ja_existentes": ja_existentes,
        "retiradas_ja_realizadas": ja_realizadas,
        "bloqueadas_por_lme": bloqueadas_lme,
        "pendencias_renovacao_criadas": pendencias_criadas,
        "ignoradas_sem_dados": ignoradas_sem_dados,
        "exemplos_criados": exemplos_criados,
        "exemplos_bloqueados": exemplos_bloqueados,
        "resumo_atualizado": resumo,
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
    base = svc_alertas_pendentes(db=db)
    alertas_base = base.get("alertas", [])
    alertas_ceaf = _coletar_alertas_ceaf(db, limite=80)
    alertas = alertas_base + alertas_ceaf

    def peso(item):
        prioridade_ceaf = str(item.get("prioridade_ceaf") or "").lower()
        if prioridade_ceaf:
            return PRIORIDADE_CEAF_PESO.get(prioridade_ceaf, 9)
        prioridade = str(item.get("prioridade") or "baixa").lower()
        return {"alta": 1, "moderada": 2, "baixa": 3}.get(prioridade, 9)

    alertas = sorted(alertas, key=lambda a: (peso(a), str(a.get("paciente_nome") or "")))
    resumo = {
        "total_alertas": len(alertas),
        "alta": sum(1 for a in alertas if a.get("prioridade") == "alta"),
        "moderada": sum(1 for a in alertas if a.get("prioridade") == "moderada"),
        "baixa": sum(1 for a in alertas if a.get("prioridade") == "baixa"),
        "ceaf_total": len(alertas_ceaf),
        "ceaf_critico": sum(1 for a in alertas_ceaf if a.get("prioridade_ceaf") == "critico"),
        "ceaf_urgente": sum(1 for a in alertas_ceaf if a.get("prioridade_ceaf") == "urgente"),
        "ceaf_atencao": sum(1 for a in alertas_ceaf if a.get("prioridade_ceaf") == "atencao"),
        "ceaf_informativo": sum(1 for a in alertas_ceaf if a.get("prioridade_ceaf") == "informativo"),
    }
    return {"resumo": resumo, "alertas": alertas}

@router.get("/agenda/alertas-ceaf")
def listar_alertas_ceaf_agenda(
    limite: int = 120,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    alertas = _coletar_alertas_ceaf(db, limite=limite)
    return {
        "resumo": _resumo_alertas_ceaf(alertas),
        "total": len(alertas),
        "alertas": alertas,
    }


@router.get("/agenda/alertas-ceaf/resumo")
def resumo_alertas_ceaf_agenda(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    alertas = _coletar_alertas_ceaf(db, limite=120)
    return _resumo_alertas_ceaf(alertas)


@router.get("/agenda/notificacoes-pendentes-ceaf")
def notificacoes_pendentes_ceaf_agenda(
    limite: int = 120,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    alertas = _coletar_alertas_ceaf(db, limite=limite)
    notificacoes = _alertas_ceaf_para_notificacoes(alertas)
    return {
        "total": len(notificacoes),
        "notificacoes": notificacoes,
        "resumo_alertas": _resumo_alertas_ceaf(alertas),
    }


@router.get("/agenda/notificacoes")
def buscar_notificacoes_agenda(
    incluir_listas: bool = True,
    limite_lista: int = 50,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    """Resumo leve de notificações da agenda.

    Usa count() para os cartões e limita as listas retornadas. Isso evita que a
    aba Agenda carregue centenas de registros CEAF apenas para calcular números.
    """
    hoje = date.today()
    amanha = hoje + timedelta(days=1)
    em_15_dias = hoje + timedelta(days=15)
    em_30_dias = hoje + timedelta(days=30)
    limite_lista = max(0, min(limite_lista or 50, 100))

    risco_query = db.query(AgendaIntegrada).filter(
        func.lower(AgendaIntegrada.status) == "risco_interrupcao_tratamento"
    )
    lme_vencidas_query = db.query(PacienteCEAF).filter(
        or_(PacienteCEAF.ativo == True, PacienteCEAF.ativo.is_(None)),
        PacienteCEAF.data_fim_vigencia.isnot(None),
        PacienteCEAF.data_fim_vigencia < hoje,
    )
    renovacoes_urgentes_query = db.query(AgendaIntegrada).filter(
        func.lower(AgendaIntegrada.tipo_evento).in_(TIPOS_RENOVACAO_AGENDA),
        AgendaIntegrada.data_fim_vigencia.isnot(None),
        AgendaIntegrada.data_fim_vigencia >= hoje,
        AgendaIntegrada.data_fim_vigencia <= em_15_dias,
        func.lower(AgendaIntegrada.status).notin_(STATUS_ENCERRADOS_AGENDA),
    )
    renovacoes_recomendadas_query = db.query(AgendaIntegrada).filter(
        func.lower(AgendaIntegrada.tipo_evento).in_(TIPOS_RENOVACAO_AGENDA),
        AgendaIntegrada.data_fim_vigencia.isnot(None),
        AgendaIntegrada.data_fim_vigencia > em_15_dias,
        AgendaIntegrada.data_fim_vigencia <= em_30_dias,
        func.lower(AgendaIntegrada.status).notin_(STATUS_ENCERRADOS_AGENDA),
    )
    ceaf_urgentes_query = db.query(PacienteCEAF).filter(
        or_(PacienteCEAF.ativo == True, PacienteCEAF.ativo.is_(None)),
        PacienteCEAF.data_fim_vigencia.isnot(None),
        PacienteCEAF.data_fim_vigencia >= hoje,
        PacienteCEAF.data_fim_vigencia <= em_15_dias,
    )
    ceaf_recomendados_query = db.query(PacienteCEAF).filter(
        or_(PacienteCEAF.ativo == True, PacienteCEAF.ativo.is_(None)),
        PacienteCEAF.data_fim_vigencia.isnot(None),
        PacienteCEAF.data_fim_vigencia > em_15_dias,
        PacienteCEAF.data_fim_vigencia <= em_30_dias,
    )
    dispensacoes_amanha_query = db.query(AgendaIntegrada).filter(
        func.lower(AgendaIntegrada.tipo_evento).in_(TIPOS_RETIRADA_AGENDA),
        AgendaIntegrada.data_evento == amanha,
        func.lower(AgendaIntegrada.status).in_({"agendado", "notificado"})
    )
    consultas_amanha_query = db.query(AgendaIntegrada).filter(
        func.lower(AgendaIntegrada.servico_origem) == "consultorio",
        AgendaIntegrada.data_evento == amanha,
        func.lower(AgendaIntegrada.status).in_({"agendado", "notificado"})
    )

    risco_total = risco_query.count()
    lme_vencidas_total = lme_vencidas_query.count()
    renovacoes_urgentes_total = renovacoes_urgentes_query.count()
    renovacoes_recomendadas_total = renovacoes_recomendadas_query.count()
    ceaf_urgentes_total = ceaf_urgentes_query.count()
    ceaf_recomendados_total = ceaf_recomendados_query.count()
    dispensacoes_amanha_total = dispensacoes_amanha_query.count()
    consultas_amanha_total = consultas_amanha_query.count()

    resposta = {
        "resumo": {
            "risco_interrupcao": risco_total + lme_vencidas_total,
            "renovacoes_urgentes": renovacoes_urgentes_total + ceaf_urgentes_total,
            "renovacoes_recomendadas": renovacoes_recomendadas_total + ceaf_recomendados_total,
            "dispensacoes_amanha": dispensacoes_amanha_total,
            "consultas_amanha": consultas_amanha_total,
            "ceaf_lme_vencidas": lme_vencidas_total,
            "ceaf_lme_vencendo_15_dias": ceaf_urgentes_total,
            "ceaf_lme_vencendo_30_dias": ceaf_recomendados_total,
        }
    }

    if incluir_listas and limite_lista > 0:
        resposta.update({
            "risco_interrupcao": risco_query.limit(limite_lista).all(),
            "ceaf_lme_vencidas": [_paciente_ceaf_resumo(p) for p in lme_vencidas_query.order_by(PacienteCEAF.data_fim_vigencia.asc()).limit(limite_lista).all()],
            "renovacoes_urgentes": renovacoes_urgentes_query.limit(limite_lista).all(),
            "renovacoes_recomendadas": renovacoes_recomendadas_query.limit(limite_lista).all(),
            "ceaf_renovacoes_urgentes": [_paciente_ceaf_resumo(p) for p in ceaf_urgentes_query.order_by(PacienteCEAF.data_fim_vigencia.asc()).limit(limite_lista).all()],
            "ceaf_renovacoes_recomendadas": [_paciente_ceaf_resumo(p) for p in ceaf_recomendados_query.order_by(PacienteCEAF.data_fim_vigencia.asc()).limit(limite_lista).all()],
            "dispensacoes_amanha": dispensacoes_amanha_query.limit(limite_lista).all(),
            "consultas_amanha": consultas_amanha_query.limit(limite_lista).all(),
        })

    return resposta

@router.post("/agenda/notificacoes/gerar")
def executar_geracao_notificacoes_agenda(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    resultado_base = gerar_notificacoes_agenda(db)
    resultado_ceaf = _gerar_notificacoes_ceaf_agenda(db)
    return {
        **resultado_base,
        **resultado_ceaf,
        "notificacoes_criadas_total": (resultado_base.get("notificacoes_criadas") or 0) + resultado_ceaf.get("notificacoes_ceaf_criadas", 0),
        "notificacoes_ignoradas_total": (resultado_base.get("notificacoes_ignoradas") or 0) + resultado_ceaf.get("notificacoes_ceaf_ignoradas", 0),
    }

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










