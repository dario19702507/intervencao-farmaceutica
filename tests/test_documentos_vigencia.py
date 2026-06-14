import requests
from datetime import date, timedelta


def test_documentos_opcoes_inclui_vigencia(get):
    data = get('/consultorio/documentos/opcoes').json()
    assert 'INCLUSAO' in data['operacoes_vigencia']
    assert 'RENOVACAO' in data['operacoes_vigencia']
    assert 'AGUARDANDO_INICIO' in data['status_vigencia']


def test_rotas_vigencia_documental_no_openapi(get):
    spec = get('/openapi.json').json()
    paths = spec.get('paths', {})
    assert '/consultorio/documentos/{documento_id}/vigencia' in paths
    assert '/consultorio/documentos/{documento_id}/vigencia-historico' in paths
    assert '/consultorio/documentos/{documento_id}/reprocessar-fluxo' in paths


def test_regra_vigencia_padrao_seis_meses_unitaria():
    from datetime import date
    from pathlib import Path
    import sys

    backend_dir = Path(__file__).resolve().parents[1] / "backend"
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

    from services.documentos_vigencia import calcular_fim_padrao

    assert calcular_fim_padrao(date(2026, 10, 1)) == date(2027, 3, 31)
    assert calcular_fim_padrao(date(2026, 7, 15)) == date(2027, 1, 14)


def test_documentos_opcoes_rota_continua_disponivel(get):
    response = get('/consultorio/documentos/opcoes')
    assert response.status_code == 200
