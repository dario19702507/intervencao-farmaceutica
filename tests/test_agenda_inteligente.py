from datetime import date
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from services.agenda_inteligente import (
    data_tem_atendimento,
    calcular_proxima_retirada,
    calcular_data_alerta_renovacao,
    configuracao_atendimento_farmacia_escola,
)


def test_configuracao_atendimento_farmacia_escola():
    cfg = configuracao_atendimento_farmacia_escola()
    dias = {item["dia_semana"]: item for item in cfg["dias"]}
    assert dias[0]["horarios"] == [{"inicio": "13:30", "fim": "16:30"}]
    assert dias[1]["horarios"] == [{"inicio": "07:30", "fim": "11:00"}]
    assert dias[2]["horarios"] == [{"inicio": "07:30", "fim": "11:00"}]
    assert len(dias[3]["horarios"]) == 2
    assert dias[4]["atende"] is False
    assert dias[5]["atende"] is False
    assert dias[6]["atende"] is False


def test_data_tem_atendimento():
    assert data_tem_atendimento(date(2026, 6, 8)) is True   # segunda
    assert data_tem_atendimento(date(2026, 6, 12)) is False  # sexta
    assert data_tem_atendimento(date(2026, 6, 13)) is False  # sábado


def test_proxima_retirada_nao_ultrapassa_30_dias_e_respeita_atendimento():
    # 10/06/2026 + 30 dias = 10/07/2026, sexta-feira fechada.
    # Deve recuar para quinta-feira, 09/07/2026, sem ultrapassar 30 dias.
    assert calcular_proxima_retirada(date(2026, 6, 10)) == date(2026, 7, 9)


def test_alerta_renovacao_segundo_mes_anterior():
    # 30/09/2026 menos 2 meses = 30/07/2026, quinta-feira com atendimento.
    assert calcular_data_alerta_renovacao(date(2026, 9, 30)) == date(2026, 7, 30)
