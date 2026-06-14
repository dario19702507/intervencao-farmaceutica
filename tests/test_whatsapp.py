import requests


def test_whatsapp_opcoes_dashboard_e_fila(get):
    opcoes = get('/consultorio/whatsapp/opcoes').json()
    assert 'SIMULADOR' in opcoes['provedores']
    assert 'PENDENTE' in opcoes['status']

    dashboard = get('/consultorio/whatsapp/dashboard').json()
    assert 'pendentes' in dashboard
    assert 'bloqueados' in dashboard

    fila = get('/consultorio/whatsapp/fila').json()
    assert 'envios' in fila


def test_whatsapp_envio_manual_e_simulacao(api_url, auth_headers):
    payload = {
        'telefone': '67999998888',
        'mensagem': 'Mensagem de teste automatizado do WhatsApp simulado.',
        'prioridade': 'NORMAL',
    }
    criado = requests.post(f'{api_url}/consultorio/whatsapp/envio-manual', json=payload, headers=auth_headers, timeout=20)
    assert criado.status_code == 200, criado.text
    envio = criado.json()['envio']
    assert envio['status'] == 'PENDENTE'

    simulado = requests.post(f'{api_url}/consultorio/whatsapp/simular-envio?limite=10', headers=auth_headers, timeout=20)
    assert simulado.status_code == 200, simulado.text
    assert 'simulados' in simulado.json()


def test_whatsapp_enfileirar_notificacoes(api_url, auth_headers):
    response = requests.post(f'{api_url}/consultorio/whatsapp/enfileirar-notificacoes', headers=auth_headers, timeout=20)
    assert response.status_code == 200, response.text
    data = response.json()
    assert 'criadas' in data
    assert 'ignoradas' in data
    assert 'bloqueadas' in data
