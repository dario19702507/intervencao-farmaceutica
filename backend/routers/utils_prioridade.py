from datetime import date


ORDEM_PRIORIDADE = {
    "CRITICO": 1,
    "ALTO": 2,
    "MODERADO": 3,
    "BAIXO": 4,
}


PRIORIDADE_VISUAL = {
    "CRITICO": {
        "rotulo": "Crítico",
        "icone": "🔴",
        "classe": "prioridade-critico",
    },
    "ALTO": {
        "rotulo": "Alto",
        "icone": "🟠",
        "classe": "prioridade-alto",
    },
    "MODERADO": {
        "rotulo": "Moderado",
        "icone": "🟡",
        "classe": "prioridade-moderado",
    },
    "BAIXO": {
        "rotulo": "Baixo",
        "icone": "🟢",
        "classe": "prioridade-baixo",
    },
}


def classificar_prioridade(
    data_retirada=None,
    data_fim_vigencia=None,
    risco_interrupcao=False
):
    hoje = date.today()

    if risco_interrupcao:
        return "CRITICO"

    if data_fim_vigencia:
        dias_vigencia = (data_fim_vigencia - hoje).days

        if dias_vigencia < 0:
            return "CRITICO"

        if dias_vigencia <= 7:
            return "ALTO"

        if dias_vigencia <= 30:
            return "MODERADO"

    if data_retirada:
        dias_retirada = (data_retirada - hoje).days

        if dias_retirada <= 0:
            return "ALTO"

        if dias_retirada == 1:
            return "MODERADO"

    return "BAIXO"


def prioridade_visual(prioridade: str):
    return PRIORIDADE_VISUAL.get(
        prioridade,
        PRIORIDADE_VISUAL["BAIXO"]
    )


def peso_prioridade(prioridade: str):
    return ORDEM_PRIORIDADE.get(prioridade, 99)