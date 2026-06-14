import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / 'backend'
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from services.agenda_inteligente import calcular_data_risco_pos_vencimento


def test_laudo_vencido_fica_urgente_no_primeiro_dia_util_apos_vencimento():
    # 30/09/2026 é quarta-feira; a Farmácia Escola atende na quinta de manhã/tarde.
    assert calcular_data_risco_pos_vencimento(date(2026, 9, 30)) == date(2026, 10, 1)


def test_laudo_vencido_quinta_vai_para_proximo_dia_de_atendimento():
    # 01/10/2026 é quinta-feira; dia seguinte é sexta, mas Farmácia Escola fecha sexta/sábado/domingo.
    # Próximo atendimento válido: segunda-feira 05/10/2026, 13:30-16:30.
    assert calcular_data_risco_pos_vencimento(date(2026, 10, 1)) == date(2026, 10, 5)
