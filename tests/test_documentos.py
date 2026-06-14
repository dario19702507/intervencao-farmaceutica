import requests


def test_documentos_opcoes(get):
    data = get('/consultorio/documentos/opcoes').json()
    assert 'LAUDO' in data['tipos_documento']
    assert 'RECEITA' in data['tipos_documento']
    assert 'ATIVO' in data['status']


def test_listar_documentos_paciente_inexistente(api_url, auth_headers):
    resp = requests.get(f'{api_url}/consultorio/paciente-clinico/999999/documentos', headers=auth_headers, timeout=20)
    assert resp.status_code == 404
