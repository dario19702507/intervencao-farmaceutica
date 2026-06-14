from datetime import date
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from services.documentos_vigencia import calcular_primeira_retirada_inclusao


def test_primeira_retirada_inclusao_apos_inicio_vigencia_em_sabado():
    # Vigência inicia no sábado, 13/06/2026. A Farmácia Escola fecha sexta,
    # sábado e domingo; a próxima abertura é segunda, 15/06/2026, às 13:30.
    resultado = calcular_primeira_retirada_inclusao(date(2026, 6, 13))
    assert resultado["data"] == date(2026, 6, 15)
    assert resultado["horario_inicio"] == "13:30"


def test_primeira_retirada_inclusao_em_dia_com_atendimento_mantem_data():
    resultado = calcular_primeira_retirada_inclusao(date(2026, 6, 16))  # terça-feira
    assert resultado["data"] == date(2026, 6, 16)
    assert resultado["horario_inicio"] == "07:30"
