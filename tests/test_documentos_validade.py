import requests


def test_documentos_validade_dashboard(get):
    data = get('/consultorio/documentos/validade-dashboard').json()
    assert 'total_documentos_ativos' in data
    assert 'vencidos_urgentes' in data
    assert 'vence_em_60_dias' in data


def test_documentos_vencimentos(get):
    data = get('/consultorio/documentos/vencimentos?dias=60').json()
    assert 'total' in data
    assert 'documentos' in data


def test_gerar_notificacoes_validade_documental(api_url, auth_headers):
    resp = requests.post(f'{api_url}/consultorio/documentos/gerar-notificacoes-validade', headers=auth_headers, timeout=20)
    assert resp.status_code in (200, 403)
    if resp.status_code == 200:
        data = resp.json()
        assert 'criadas' in data
        assert 'ignoradas' in data
