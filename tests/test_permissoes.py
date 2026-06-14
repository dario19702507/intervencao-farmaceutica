import time
import requests


def test_usuario_nao_admin_nao_lista_usuarios(api_url, auth_headers):
    """Garante que listagem de usuários permanece restrita ao administrador."""
    email = f"teste.permissao.{int(time.time())}@farmacia.local"
    payload = {
        "nome": "Teste Permissão",
        "email": email,
        "password": "teste123",
        "perfil": "farmaceutico",
        "categoria_profissional": "Farmacêutico",
    }

    created = requests.post(f"{api_url}/users", json=payload, headers=auth_headers, timeout=20)
    assert created.status_code in (200, 400), created.text

    login = requests.post(
        f"{api_url}/auth/login",
        data={"username": email, "password": "teste123"},
        timeout=20,
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]

    response = requests.get(
        f"{api_url}/users",
        headers={"Authorization": f"Bearer {token}"},
        timeout=20,
    )
    assert response.status_code == 403, response.text


def test_perfil_invalido_eh_rejeitado(api_url, auth_headers):
    email = f"teste.perfil.invalido.{int(time.time())}@farmacia.local"
    payload = {
        "nome": "Perfil Inválido",
        "email": email,
        "password": "teste123",
        "perfil": "superusuario_inexistente",
        "categoria_profissional": "Farmacêutico",
    }

    response = requests.post(f"{api_url}/users", json=payload, headers=auth_headers, timeout=20)
    assert response.status_code == 400, response.text
