"""Regras inteligentes da Agenda da Farmácia Escola.

Passo 10C: centraliza regras de funcionamento, ajuste de datas e gatilhos
operacionais para retirada e renovação de laudos.
"""

from __future__ import annotations

import calendar
from datetime import date, time, timedelta
from typing import Dict, List, Optional

# Python weekday(): segunda=0, terça=1, quarta=2, quinta=3, sexta=4, sábado=5, domingo=6
HORARIOS_FARMACIA_ESCOLA: Dict[int, List[Dict[str, str]]] = {
    0: [{"inicio": "13:30", "fim": "16:30"}],
    1: [{"inicio": "07:30", "fim": "11:00"}],
    2: [{"inicio": "07:30", "fim": "11:00"}],
    3: [
        {"inicio": "07:30", "fim": "11:00"},
        {"inicio": "13:30", "fim": "16:30"},
    ],
    4: [],
    5: [],
    6: [],
}

DIAS_SEMANA_PT = {
    0: "segunda-feira",
    1: "terça-feira",
    2: "quarta-feira",
    3: "quinta-feira",
    4: "sexta-feira",
    5: "sábado",
    6: "domingo",
}

FREQUENCIA_DIAS = {
    "MENSAL": 30,
    "BIMESTRAL": 60,
    "TRIMESTRAL": 90,
    "SEMESTRAL": 180,
    "ANUAL": 365,
}


def configuracao_atendimento_farmacia_escola() -> dict:
    return {
        "descricao": "Farmácia Escola UFMS",
        "regra": "Agenda respeita os dias e horários oficiais de atendimento.",
        "dias": [
            {
                "dia_semana": indice,
                "nome": DIAS_SEMANA_PT[indice],
                "atende": bool(janelas),
                "horarios": janelas,
            }
            for indice, janelas in HORARIOS_FARMACIA_ESCOLA.items()
        ],
        "fechada": ["sexta-feira", "sábado", "domingo"],
    }


def data_tem_atendimento(data_referencia: date) -> bool:
    return bool(HORARIOS_FARMACIA_ESCOLA.get(data_referencia.weekday(), []))


def horarios_do_dia(data_referencia: date) -> List[Dict[str, str]]:
    return HORARIOS_FARMACIA_ESCOLA.get(data_referencia.weekday(), [])


def ajustar_para_proximo_dia_atendimento(data_referencia: date, limite_data: Optional[date] = None) -> date:
    data_teste = data_referencia
    for _ in range(0, 14):
        if limite_data and data_teste > limite_data:
            break
        if data_tem_atendimento(data_teste):
            return data_teste
        data_teste += timedelta(days=1)
    return data_referencia


def ajustar_para_dia_atendimento_sem_ultrapassar(data_referencia: date, limite_data: date) -> date:
    """Ajusta para um dia de atendimento sem ultrapassar o limite informado.

    Usado para retirada mensal: se D+30 cair em sexta/sábado/domingo, a data
    retorna para a quinta-feira ou outro dia válido anterior, preservando o limite
    máximo de 30 dias.
    """
    data_teste = min(data_referencia, limite_data)
    for _ in range(0, 14):
        if data_tem_atendimento(data_teste):
            return data_teste
        data_teste -= timedelta(days=1)
    return limite_data


def calcular_proxima_retirada(data_retirada_realizada: date, frequencia: Optional[str] = "MENSAL") -> date:
    freq = (frequencia or "MENSAL").upper()
    dias = FREQUENCIA_DIAS.get(freq, 30)

    # Para o fluxo atual da Farmácia Escola, a regra operacional da retirada mensal
    # não deve ultrapassar 30 dias, mesmo quando a frequência cadastrada vier maior.
    dias_limite = min(dias, 30)
    limite = data_retirada_realizada + timedelta(days=dias_limite)
    return ajustar_para_dia_atendimento_sem_ultrapassar(limite, limite)


def subtrair_meses(data_referencia: date, meses: int) -> date:
    mes = data_referencia.month - meses
    ano = data_referencia.year
    while mes <= 0:
        mes += 12
        ano -= 1

    ultimo_dia = calendar.monthrange(ano, mes)[1]
    dia = min(data_referencia.day, ultimo_dia)
    return date(ano, mes, dia)


def somar_meses(data_referencia: date, meses: int) -> date:
    mes = data_referencia.month + meses
    ano = data_referencia.year
    while mes > 12:
        mes -= 12
        ano += 1

    ultimo_dia = calendar.monthrange(ano, mes)[1]
    dia = min(data_referencia.day, ultimo_dia)
    return date(ano, mes, dia)


def calcular_data_alerta_renovacao(data_vencimento: date) -> date:
    # Regra definida: notificar no segundo mês anterior ao vencimento.
    return ajustar_para_proximo_dia_atendimento(subtrair_meses(data_vencimento, 2), limite_data=data_vencimento)


def calcular_data_risco_pos_vencimento(data_vencimento: date) -> date:
    """Regra oficial: laudo não renovado torna-se URGENTE no primeiro dia útil após o vencimento."""
    return ajustar_para_proximo_dia_atendimento(data_vencimento + timedelta(days=1))


def quinto_dia_util_antes_fim_mes(data_referencia: date) -> date:
    ultimo_dia = calendar.monthrange(data_referencia.year, data_referencia.month)[1]
    data_teste = date(data_referencia.year, data_referencia.month, ultimo_dia)
    encontrados = 0
    while True:
        if data_tem_atendimento(data_teste):
            encontrados += 1
            if encontrados == 5:
                return data_teste
        data_teste -= timedelta(days=1)
