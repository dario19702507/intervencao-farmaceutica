from datetime import date
from typing import Optional

from models.consultorio_models import (
    PacienteSimplificado,
    AtendimentoRapido,
    AfericaoPA,
    GlicemiaCapilar,
    Bioimpedancia,
    PicoFluxo,
)
from services.consultorio_helpers import (
    calcular_percentual,
    dashboard_vazio,
    definir_prioridade,
    gerar_sugestao_conduta,
)


def aplicar_filtros_atendimento(
    query,
    data_inicio: Optional[date],
    data_fim: Optional[date],
    tipo_servico: Optional[str],
    sexo: Optional[str],
    bairro: Optional[str],
    idade_min: Optional[int],
    idade_max: Optional[int],
):
    """Aplica filtros comuns aos dashboards de serviços rápidos."""
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


def montar_dashboard_servicos(
    db,
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    tipo_servico: Optional[str] = None,
    sexo: Optional[str] = None,
    bairro: Optional[str] = None,
    idade_min: Optional[int] = None,
    idade_max: Optional[int] = None,
    somente_risco: bool = False,
):
    """Monta os indicadores consolidados dos serviços rápidos."""
    query_atendimentos = db.query(AtendimentoRapido).join(
        PacienteSimplificado,
        PacienteSimplificado.id == AtendimentoRapido.paciente_simplificado_id,
    )

    query_atendimentos = aplicar_filtros_atendimento(
        query_atendimentos,
        data_inicio,
        data_fim,
        tipo_servico,
        sexo,
        bairro,
        idade_min,
        idade_max,
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
            "somente_risco": somente_risco,
        },
        "total_atendimentos_rapidos": total_atendimentos,
        "total_procedimentos": total_procedimentos,
        "por_tipo_servico": por_tipo,
        "pressao_arterial": {
            "total": pa_total,
            "alterados": pa_alterada,
            "percentual_alterados": calcular_percentual(pa_alterada, pa_total),
        },
        "glicemia": {
            "total": glicemia_total,
            "alterados": glicemia_alterada,
            "percentual_alterados": calcular_percentual(glicemia_alterada, glicemia_total),
        },
        "bioimpedancia": {
            "total": bio_total,
            "risco": bio_risco,
            "percentual_risco": calcular_percentual(bio_risco, bio_total),
        },
        "pico_fluxo": {
            "total": pico_total,
            "risco": pico_risco,
            "percentual_risco": calcular_percentual(pico_risco, pico_total),
        },
        "alertas": {
            "pa_alterada": pa_alterada,
            "glicemia_alterada": glicemia_alterada,
            "bioimpedancia_risco": bio_risco,
            "pico_fluxo_risco": pico_risco,
            "total_alertas": pa_alterada + glicemia_alterada + bio_risco + pico_risco,
        },
    }


def montar_triagem_risco(
    db,
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
):
    """Monta a lista de pacientes com alterações nos serviços rápidos."""
    query_atendimentos = db.query(AtendimentoRapido).join(
        PacienteSimplificado,
        PacienteSimplificado.id == AtendimentoRapido.paciente_simplificado_id,
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
            "obesidade_grau_3",
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
                "sugestao": gerar_sugestao_conduta(prioridade),
            })

    return {
        "total_pacientes_risco": len(pacientes_em_risco),
        "pacientes": pacientes_em_risco,
    }
