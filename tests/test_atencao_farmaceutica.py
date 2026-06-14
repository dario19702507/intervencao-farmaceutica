from datetime import date, timedelta

from services.atencao_farmaceutica import REGRAS, _dias_desde, _dias_ate


def test_regras_basicas_atencao_farmaceutica():
    assert REGRAS["PRM_CRITICO_DIAS"] == 60
    assert REGRAS["LAUDO_VENCE_MODERADO_DIAS"] == 30
    assert REGRAS["SEM_RETIRADA_MODERADO_DIAS"] == 30


def test_calculo_dias_pendencias():
    hoje = date(2026, 6, 13)
    assert _dias_desde(hoje - timedelta(days=45), hoje) == 45
    assert _dias_ate(hoje + timedelta(days=30), hoje) == 30
