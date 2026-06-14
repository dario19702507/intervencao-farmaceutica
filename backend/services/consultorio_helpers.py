from datetime import date
from typing import Optional


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

def calcular_bioimpedancia(dados, paciente=None):
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
