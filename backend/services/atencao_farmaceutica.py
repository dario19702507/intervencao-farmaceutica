"""Motor de pendências assistenciais do Centro de Atenção Farmacêutica.

Este serviço não executa ações automáticas nem encerra registros. Ele apenas
identifica pendências clínicas, CEAF, documentais e farmacoterapêuticas para
apoiar a priorização do trabalho farmacêutico.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime
from typing import Any

from sqlalchemy.orm import Session

from models.consultorio_models import (
    PacienteClinico,
    MedicamentoUso,
    IntervencaoFarmacoterapia,
    DesfechoIntervencaoFarmacoterapia,
    ProcessoDocumental,
    DocumentoPaciente,
    AgendaIntegrada,
    ProblemaFarmacoterapeutico,
    MetaTerapeutica,
    AcaoPlanoCuidado,
)
from services.cuidado_farmaceutico import calcular_complexidade_farmacoterapeutica

CRITICIDADE = ["CRITICA", "MODERADA", "INFORMATIVA"]
CATEGORIAS = ["ASSISTENCIAL", "CEAF", "DOCUMENTAL", "FARMACOTERAPEUTICA"]

REGRAS = {
    "PRM_CRITICO_DIAS": 60,
    "PRM_MODERADO_DIAS": 30,
    "INTERVENCAO_SEM_DESFECHO_DIAS": 30,
    "META_CRITICA_DIAS": 90,
    "META_MODERADA_DIAS": 30,
    "SEM_RETIRADA_CRITICO_DIAS": 60,
    "SEM_RETIRADA_MODERADO_DIAS": 30,
    "LAUDO_VENCE_MODERADO_DIAS": 30,
    "LAUDO_VENCE_INFORMATIVO_DIAS": 60,
}

MEDICAMENTOS_ALTO_RISCO = [
    "insulina", "varfarina", "warfarin", "rivaroxabana", "apixabana", "dabigatrana",
    "edoxabana", "digoxina", "amiodarona", "metotrexato", "lítio", "litio",
    "clozapina", "carbamazepina", "fenitoina", "fenitoína", "fenobarbital",
]

STATUS_ABERTO_PRM = ["ABERTO", "EM_ACOMPANHAMENTO"]
STATUS_META_ATIVA = ["ATIVA", "PARCIAL", "NAO_ALCANCADA"]
STATUS_ACAO_ABERTA = ["PENDENTE", "EM_ANDAMENTO"]
STATUS_PROCESSO_INCOMPLETO = ["EM_MONTAGEM", "INCOMPLETO", "PENDENTE", "EM_ANALISE"]
STATUS_AGENDA_CONCLUIDO = ["realizado", "realizada", "concluido", "concluida", "retirado", "retirada"]


def _hoje() -> date:
    return date.today()


def _as_date(valor: Any) -> date | None:
    if valor is None:
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    try:
        return datetime.fromisoformat(str(valor)).date()
    except Exception:
        return None


def _dias_desde(valor: Any, hoje: date | None = None) -> int | None:
    data = _as_date(valor)
    if not data:
        return None
    return ((hoje or _hoje()) - data).days


def _dias_ate(valor: Any, hoje: date | None = None) -> int | None:
    data = _as_date(valor)
    if not data:
        return None
    return (data - (hoje or _hoje())).days


def _texto(value: Any) -> str:
    return str(value or "").strip()


def _status(value: Any) -> str:
    return _texto(value).upper()


def _pendencia(
    *,
    paciente: PacienteClinico,
    categoria: str,
    tipo: str,
    criticidade: str,
    titulo: str,
    descricao: str,
    acao_sugerida: str,
    origem_tipo: str,
    origem_id: int | None = None,
    dias: int | None = None,
    data_referencia: Any = None,
    destino_url: str | None = None,
    metadados: dict | None = None,
) -> dict:
    return {
        "id": f"{categoria}:{tipo}:{paciente.id}:{origem_tipo}:{origem_id or 'sem_id'}",
        "paciente_id": paciente.id,
        "paciente_nome": paciente.nome,
        "categoria": categoria,
        "tipo": tipo,
        "criticidade": criticidade,
        "titulo": titulo,
        "descricao": descricao,
        "acao_sugerida": acao_sugerida,
        "dias": dias,
        "data_referencia": _as_date(data_referencia).isoformat() if _as_date(data_referencia) else None,
        "origem_tipo": origem_tipo,
        "origem_id": origem_id,
        "destino_url": destino_url or f"/atendimento/consultorio?paciente_id={paciente.id}",
        "metadados": metadados or {},
    }


def _tem_medicamento_alto_risco(nome: str | None) -> bool:
    texto = (nome or "").lower()
    return any(t in texto for t in MEDICAMENTOS_ALTO_RISCO)


def _adesao_baixa(valor: str | None) -> bool:
    texto = (valor or "").strip().lower()
    return texto in {"baixa", "ruim", "irregular", "não adesão", "nao adesao", "não aderente", "nao aderente"}


def gerar_pendencias_paciente(paciente_id: int, db: Session, hoje: date | None = None) -> list[dict]:
    hoje = hoje or _hoje()
    paciente = db.query(PacienteClinico).filter(PacienteClinico.id == paciente_id).first()
    if not paciente:
        return []

    pendencias: list[dict] = []

    prms = db.query(ProblemaFarmacoterapeutico).filter(
        ProblemaFarmacoterapeutico.paciente_clinico_id == paciente_id,
        ProblemaFarmacoterapeutico.status.in_(STATUS_ABERTO_PRM),
    ).all()
    for prm in prms:
        dias = _dias_desde(prm.data_identificacao, hoje) or 0
        if dias >= REGRAS["PRM_CRITICO_DIAS"] or _status(prm.gravidade) == "CRITICA":
            crit = "CRITICA"
        elif dias >= REGRAS["PRM_MODERADO_DIAS"] or _status(prm.gravidade) in {"ALTA", "MODERADA"}:
            crit = "MODERADA"
        else:
            crit = "INFORMATIVA"
        pendencias.append(_pendencia(
            paciente=paciente,
            categoria="ASSISTENCIAL",
            tipo="PRM_ABERTO",
            criticidade=crit,
            titulo="PRM aberto/em acompanhamento",
            descricao=f"{prm.tipo or 'PRM'} · {prm.descricao or 'sem descrição'}",
            acao_sugerida="Revisar prontuário, registrar evolução e vincular intervenção/meta/plano quando necessário.",
            origem_tipo="PRM",
            origem_id=prm.id,
            dias=dias,
            data_referencia=prm.data_identificacao,
            metadados={"categoria_prm": prm.categoria, "gravidade": prm.gravidade, "status": prm.status},
        ))

    intervencoes = db.query(IntervencaoFarmacoterapia).filter(
        IntervencaoFarmacoterapia.paciente_clinico_id == paciente_id,
    ).all()
    for intervencao in intervencoes:
        dias = _dias_desde(intervencao.criado_em, hoje) or 0
        if dias < REGRAS["INTERVENCAO_SEM_DESFECHO_DIAS"]:
            continue
        desfecho = db.query(DesfechoIntervencaoFarmacoterapia).filter(
            DesfechoIntervencaoFarmacoterapia.intervencao_id == intervencao.id
        ).first()
        if not desfecho:
            pendencias.append(_pendencia(
                paciente=paciente,
                categoria="ASSISTENCIAL",
                tipo="INTERVENCAO_SEM_DESFECHO",
                criticidade="MODERADA",
                titulo="Intervenção sem desfecho",
                descricao=f"{intervencao.tipo_intervencao or 'Intervenção'} registrada há {dias} dias sem desfecho farmacoterapêutico.",
                acao_sugerida="Registrar desfecho, acompanhamento ou necessidade de nova intervenção.",
                origem_tipo="INTERVENCAO_FARMACOTERAPIA",
                origem_id=intervencao.id,
                dias=dias,
                data_referencia=intervencao.criado_em,
            ))

    metas = db.query(MetaTerapeutica).filter(
        MetaTerapeutica.paciente_clinico_id == paciente_id,
        MetaTerapeutica.status.in_(STATUS_META_ATIVA),
    ).all()
    for meta in metas:
        dias_vencida = _dias_desde(meta.prazo, hoje)
        if dias_vencida is None or dias_vencida < REGRAS["META_MODERADA_DIAS"]:
            continue
        crit = "CRITICA" if dias_vencida >= REGRAS["META_CRITICA_DIAS"] else "MODERADA"
        pendencias.append(_pendencia(
            paciente=paciente,
            categoria="ASSISTENCIAL",
            tipo="META_VENCIDA",
            criticidade=crit,
            titulo="Meta terapêutica vencida",
            descricao=f"Meta {meta.parametro or ''}: {meta.descricao or ''}",
            acao_sugerida="Reavaliar meta, registrar resultado e pactuar novo prazo se necessário.",
            origem_tipo="META_TERAPEUTICA",
            origem_id=meta.id,
            dias=dias_vencida,
            data_referencia=meta.prazo,
            metadados={"status": meta.status, "valor_alvo": meta.valor_alvo, "valor_resultado": meta.valor_resultado},
        ))

    acoes = db.query(AcaoPlanoCuidado).filter(
        AcaoPlanoCuidado.paciente_clinico_id == paciente_id,
        AcaoPlanoCuidado.status.in_(STATUS_ACAO_ABERTA),
    ).all()
    for acao in acoes:
        dias_atraso = _dias_desde(acao.prazo, hoje)
        if dias_atraso is None or dias_atraso < 1:
            continue
        crit = "CRITICA" if dias_atraso >= 60 or _status(acao.prioridade) in {"ALTA", "CRITICA"} else "MODERADA"
        pendencias.append(_pendencia(
            paciente=paciente,
            categoria="ASSISTENCIAL",
            tipo="ACAO_PLANO_ATRASADA",
            criticidade=crit,
            titulo="Ação do plano de cuidado atrasada",
            descricao=acao.descricao or "Ação sem descrição.",
            acao_sugerida="Atualizar status da ação, registrar resultado ou reagendar prazo.",
            origem_tipo="ACAO_PLANO_CUIDADO",
            origem_id=acao.id,
            dias=dias_atraso,
            data_referencia=acao.prazo,
            metadados={"prioridade": acao.prioridade, "status": acao.status},
        ))

    processos = db.query(ProcessoDocumental).filter(ProcessoDocumental.paciente_id == paciente_id).all()
    for proc in processos:
        dias_ate_venc = _dias_ate(proc.vigencia_fim, hoje)
        if dias_ate_venc is not None:
            if dias_ate_venc < 0:
                pendencias.append(_pendencia(
                    paciente=paciente,
                    categoria="CEAF",
                    tipo="LAUDO_VENCIDO",
                    criticidade="CRITICA",
                    titulo="Laudo/vigência vencida",
                    descricao=f"Processo {proc.tipo_processo or ''} com vigência encerrada em {proc.vigencia_fim}.",
                    acao_sugerida="Verificar renovação, adequação ou encerramento do processo.",
                    origem_tipo="PROCESSO_DOCUMENTAL",
                    origem_id=proc.id,
                    dias=abs(dias_ate_venc),
                    data_referencia=proc.vigencia_fim,
                ))
            elif dias_ate_venc <= REGRAS["LAUDO_VENCE_MODERADO_DIAS"]:
                pendencias.append(_pendencia(
                    paciente=paciente,
                    categoria="CEAF",
                    tipo="LAUDO_A_VENCER_30_DIAS",
                    criticidade="MODERADA",
                    titulo="Laudo vence em até 30 dias",
                    descricao=f"Processo {proc.tipo_processo or ''} com vigência até {proc.vigencia_fim}.",
                    acao_sugerida="Orientar renovação e revisar documentação necessária.",
                    origem_tipo="PROCESSO_DOCUMENTAL",
                    origem_id=proc.id,
                    dias=dias_ate_venc,
                    data_referencia=proc.vigencia_fim,
                ))
            elif dias_ate_venc <= REGRAS["LAUDO_VENCE_INFORMATIVO_DIAS"]:
                pendencias.append(_pendencia(
                    paciente=paciente,
                    categoria="CEAF",
                    tipo="LAUDO_A_VENCER_60_DIAS",
                    criticidade="INFORMATIVA",
                    titulo="Laudo vence em até 60 dias",
                    descricao=f"Processo {proc.tipo_processo or ''} com vigência até {proc.vigencia_fim}.",
                    acao_sugerida="Monitorar renovação e preparar orientação ao paciente.",
                    origem_tipo="PROCESSO_DOCUMENTAL",
                    origem_id=proc.id,
                    dias=dias_ate_venc,
                    data_referencia=proc.vigencia_fim,
                ))

        if _status(proc.situacao) in STATUS_PROCESSO_INCOMPLETO:
            pendencias.append(_pendencia(
                paciente=paciente,
                categoria="DOCUMENTAL",
                tipo="PACOTE_DOCUMENTAL_INCOMPLETO",
                criticidade="MODERADA",
                titulo="Pacote documental incompleto/em análise",
                descricao=proc.pendencias_descricao or proc.titulo or "Processo documental exige conferência.",
                acao_sugerida="Revisar documentos pendentes e atualizar status do pacote.",
                origem_tipo="PROCESSO_DOCUMENTAL",
                origem_id=proc.id,
                dias=_dias_desde(proc.data_abertura, hoje),
                data_referencia=proc.data_abertura,
                metadados={"situacao": proc.situacao, "tipo_processo": proc.tipo_processo},
            ))

    documentos = db.query(DocumentoPaciente).filter(DocumentoPaciente.paciente_id == paciente_id, DocumentoPaciente.ativo == True).all()
    for doc in documentos:
        if _status(doc.status_documental) == "REJEITADO":
            pendencias.append(_pendencia(
                paciente=paciente,
                categoria="DOCUMENTAL",
                tipo="DOCUMENTO_REJEITADO",
                criticidade="MODERADA",
                titulo="Documento rejeitado",
                descricao=doc.status_documental_motivo or doc.titulo or doc.nome_arquivo_original,
                acao_sugerida="Solicitar correção manualmente e anexar documento substituto quando recebido.",
                origem_tipo="DOCUMENTO",
                origem_id=doc.id,
                dias=_dias_desde(doc.status_documental_atualizado_em or doc.criado_em, hoje),
                data_referencia=doc.status_documental_atualizado_em or doc.criado_em,
            ))
        if _status(doc.origem) != "OCR_PROCESSADO" and doc.tipo_documento in {"LAUDO", "RECEITA", "EXAME", "ESPIROMETRIA"} and not doc.status_documental_atualizado_em:
            # Informativo: documento relevante recebido sem etapa de validação/atualização registrada.
            pendencias.append(_pendencia(
                paciente=paciente,
                categoria="DOCUMENTAL",
                tipo="DOCUMENTO_SEM_CONFERENCIA",
                criticidade="INFORMATIVA",
                titulo="Documento sem conferência registrada",
                descricao=doc.titulo or doc.nome_arquivo_original,
                acao_sugerida="Conferir documento, validar/rejeitar e executar OCR quando pertinente.",
                origem_tipo="DOCUMENTO",
                origem_id=doc.id,
                dias=_dias_desde(doc.criado_em, hoje),
                data_referencia=doc.criado_em,
            ))

    retiradas = db.query(AgendaIntegrada).filter(
        AgendaIntegrada.paciente_id == paciente_id,
        AgendaIntegrada.tipo_evento.ilike("%RETIRADA%"),
    ).order_by(AgendaIntegrada.data_evento.desc()).all()
    if retiradas:
        ultima = retiradas[0]
        dias = _dias_desde(ultima.data_evento, hoje) or 0
        status = (ultima.status or "").lower()
        if dias >= REGRAS["SEM_RETIRADA_CRITICO_DIAS"] and status not in STATUS_AGENDA_CONCLUIDO:
            crit = "CRITICA"
        elif dias >= REGRAS["SEM_RETIRADA_MODERADO_DIAS"] and status not in STATUS_AGENDA_CONCLUIDO:
            crit = "MODERADA"
        else:
            crit = None
        if crit:
            pendencias.append(_pendencia(
                paciente=paciente,
                categoria="CEAF",
                tipo="RETIRADA_ATRASADA",
                criticidade=crit,
                titulo="Retirada pendente/atrasada",
                descricao=f"Última retirada prevista em {ultima.data_evento} com status {ultima.status or 'não informado'}.",
                acao_sugerida="Verificar retirada, contato com paciente ou risco de abandono/perda de tratamento.",
                origem_tipo="AGENDA",
                origem_id=ultima.id,
                dias=dias,
                data_referencia=ultima.data_evento,
            ))

    medicamentos = db.query(MedicamentoUso).filter(MedicamentoUso.paciente_clinico_id == paciente_id, MedicamentoUso.ativo == True).all()
    if len(medicamentos) >= 5:
        pendencias.append(_pendencia(
            paciente=paciente,
            categoria="FARMACOTERAPEUTICA",
            tipo="POLIFARMACIA",
            criticidade="MODERADA",
            titulo="Polifarmácia",
            descricao=f"Paciente com {len(medicamentos)} medicamentos ativos.",
            acao_sugerida="Revisar necessidade, efetividade, segurança, adesão, duplicidades e horários.",
            origem_tipo="FARMACOTERAPIA",
            origem_id=None,
            dias=None,
            metadados={"total_medicamentos": len(medicamentos)},
        ))

    if medicamentos:
        complexidade = calcular_complexidade_farmacoterapeutica(paciente_id, db)
        if complexidade.get("classificacao") == "MUITO_ALTA":
            pendencias.append(_pendencia(
                paciente=paciente,
                categoria="FARMACOTERAPEUTICA",
                tipo="COMPLEXIDADE_MUITO_ALTA",
                criticidade="CRITICA",
                titulo="Complexidade farmacoterapêutica muito alta",
                descricao=f"Escore {complexidade.get('escore')} · fatores: {', '.join(complexidade.get('fatores') or [])}",
                acao_sugerida="Priorizar consulta farmacêutica e plano de cuidado estruturado.",
                origem_tipo="COMPLEXIDADE_FARMACOTERAPEUTICA",
                origem_id=None,
                metadados=complexidade,
            ))
        elif complexidade.get("classificacao") == "ALTA":
            pendencias.append(_pendencia(
                paciente=paciente,
                categoria="FARMACOTERAPEUTICA",
                tipo="COMPLEXIDADE_ALTA",
                criticidade="MODERADA",
                titulo="Complexidade farmacoterapêutica alta",
                descricao=f"Escore {complexidade.get('escore')} · fatores: {', '.join(complexidade.get('fatores') or [])}",
                acao_sugerida="Revisar farmacoterapia e acompanhar adesão/segurança.",
                origem_tipo="COMPLEXIDADE_FARMACOTERAPEUTICA",
                origem_id=None,
                metadados=complexidade,
            ))

    for med in medicamentos:
        if _adesao_baixa(med.adesao_referida):
            pendencias.append(_pendencia(
                paciente=paciente,
                categoria="FARMACOTERAPEUTICA",
                tipo="ADESAO_BAIXA",
                criticidade="CRITICA",
                titulo="Adesão referida baixa",
                descricao=f"{med.nome_medicamento}: adesão {med.adesao_referida}.",
                acao_sugerida="Investigar barreiras de adesão e pactuar estratégia individualizada.",
                origem_tipo="MEDICAMENTO_USO",
                origem_id=med.id,
                data_referencia=med.criado_em,
            ))
        if not _texto(getattr(med, "horarios_uso", None)) and not bool(getattr(med, "uso_se_necessario", False)):
            pendencias.append(_pendencia(
                paciente=paciente,
                categoria="FARMACOTERAPEUTICA",
                tipo="HORARIOS_NAO_ESTRUTURADOS",
                criticidade="INFORMATIVA",
                titulo="Horários de uso não estruturados",
                descricao=f"{med.nome_medicamento}: horários de uso não informados.",
                acao_sugerida="Padronizar horários/orientações para apoiar adesão e alertas futuros.",
                origem_tipo="MEDICAMENTO_USO",
                origem_id=med.id,
                data_referencia=med.criado_em,
            ))
        if not getattr(med, "catalogo_medicamento_id", None):
            pendencias.append(_pendencia(
                paciente=paciente,
                categoria="FARMACOTERAPEUTICA",
                tipo="MEDICAMENTO_NAO_PADRONIZADO",
                criticidade="INFORMATIVA",
                titulo="Medicamento não vinculado ao catálogo",
                descricao=med.nome_medicamento,
                acao_sugerida="Vincular ao catálogo quando possível ou manter justificativa de cadastro manual.",
                origem_tipo="MEDICAMENTO_USO",
                origem_id=med.id,
                data_referencia=med.criado_em,
            ))
        if _tem_medicamento_alto_risco(med.nome_medicamento):
            # Sem reavaliação recente será aproximado pela ausência de evolução nos últimos 90 dias.
            pendencias.append(_pendencia(
                paciente=paciente,
                categoria="FARMACOTERAPEUTICA",
                tipo="MEDICAMENTO_ALTO_RISCO",
                criticidade="MODERADA",
                titulo="Medicamento potencialmente de alto risco",
                descricao=med.nome_medicamento,
                acao_sugerida="Verificar monitoramento, segurança, sinais de alerta e necessidade de acompanhamento.",
                origem_tipo="MEDICAMENTO_USO",
                origem_id=med.id,
                data_referencia=med.criado_em,
            ))

    ordem = {"CRITICA": 0, "MODERADA": 1, "INFORMATIVA": 2}
    pendencias.sort(key=lambda p: (ordem.get(p["criticidade"], 9), -(p.get("dias") or 0), p["paciente_nome"]))
    return pendencias


def listar_pendencias(
    db: Session,
    criticidade: str | None = None,
    categoria: str | None = None,
    paciente_id: int | None = None,
    limite: int = 100,
    limite_pacientes: int = 80,
) -> list[dict]:
    """Lista pendências com limite real de pacientes.

    A versão anterior percorria todos os pacientes clínicos e, para cada um,
    executava várias consultas. Em produção/Supabase isso torna a aba de
    consultório muito lenta e pode fazer o navegador acusar CORS quando a
    requisição falha antes de retornar resposta útil.
    """
    limite = max(1, min(int(limite or 100), 300))
    limite_pacientes = max(1, min(int(limite_pacientes or 80), 300))

    pacientes_query = db.query(PacienteClinico).order_by(PacienteClinico.nome.asc())
    if paciente_id:
        pacientes_query = pacientes_query.filter(PacienteClinico.id == paciente_id)

    pacientes = pacientes_query.limit(limite_pacientes).all()

    todas: list[dict] = []
    for paciente in pacientes:
        try:
            todas.extend(gerar_pendencias_paciente(paciente.id, db))
        except Exception:
            # Uma falha pontual em um paciente não deve derrubar a central.
            continue
        if len(todas) >= limite * 3:
            break

    if criticidade:
        todas = [p for p in todas if p["criticidade"] == criticidade.upper()]
    if categoria:
        todas = [p for p in todas if p["categoria"] == categoria.upper()]

    return todas[:limite]


def montar_dashboard_atencao(db: Session) -> dict:
    pendencias = listar_pendencias(db, limite=200, limite_pacientes=80)
    por_criticidade = Counter(p["criticidade"] for p in pendencias)
    por_categoria = Counter(p["categoria"] for p in pendencias)
    por_tipo = Counter(p["tipo"] for p in pendencias)
    pacientes = {p["paciente_id"] for p in pendencias}
    por_paciente = Counter((p["paciente_id"], p["paciente_nome"]) for p in pendencias)

    return {
        "total_pendencias": len(pendencias),
        "pendencias_criticas": por_criticidade.get("CRITICA", 0),
        "pendencias_moderadas": por_criticidade.get("MODERADA", 0),
        "pendencias_informativas": por_criticidade.get("INFORMATIVA", 0),
        "pacientes_impactados": len(pacientes),
        "por_criticidade": dict(por_criticidade),
        "por_categoria": dict(por_categoria),
        "top_tipos": [{"tipo": k, "total": v} for k, v in por_tipo.most_common(10)],
        "top_pacientes": [
            {"paciente_id": k[0], "paciente_nome": k[1], "total": v}
            for k, v in por_paciente.most_common(10)
        ],
        "fila_priorizada": pendencias[:20],
        "gerado_em": datetime.utcnow().isoformat(),
    }
