import requests


def test_notificacoes_opcoes_e_dashboard(get):
    opcoes = get('/consultorio/notificacoes/opcoes').json()
    assert 'RENOVACAO' in opcoes['tipos']
    assert 'URGENTE' in opcoes['prioridades']

    dashboard = get('/consultorio/notificacoes/dashboard').json()
    assert 'nao_lidas' in dashboard
    assert 'urgentes' in dashboard


def test_criar_listar_marcar_notificacao_manual(api_url, auth_headers):
    payload = {
        'tipo': 'SISTEMA',
        'prioridade': 'NORMAL',
        'origem': 'MANUAL',
        'titulo': 'Teste automatizado de notificação',
        'mensagem': 'Mensagem criada pelo teste automatizado.',
        'necessita_acao': False,
    }
    criado = requests.post(f'{api_url}/consultorio/notificacoes', json=payload, headers=auth_headers, timeout=20)
    assert criado.status_code == 200, criado.text
    notificacao_id = criado.json()['notificacao']['id']

    lista = requests.get(f'{api_url}/consultorio/notificacoes?lida=false&limite=20', headers=auth_headers, timeout=20)
    assert lista.status_code == 200, lista.text
    assert any(n['id'] == notificacao_id for n in lista.json()['notificacoes'])

    marcada = requests.put(f'{api_url}/consultorio/notificacoes/{notificacao_id}/marcar-lida', headers=auth_headers, timeout=20)
    assert marcada.status_code == 200, marcada.text
    assert marcada.json()['notificacao']['lida'] is True


def test_gerar_notificacoes_automaticas_endpoint(api_url, auth_headers):
    response = requests.post(f'{api_url}/consultorio/notificacoes/gerar-automaticas', headers=auth_headers, timeout=20)
    assert response.status_code == 200, response.text
    data = response.json()
    assert 'criadas' in data
    assert 'ignoradas' in data
