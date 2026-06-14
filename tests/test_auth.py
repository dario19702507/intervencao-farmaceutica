import os
import requests


def test_login_valido_retorna_token(api_url):
    email = os.getenv("API_EMAIL", "admin@farmacia.local")
    password = os.getenv("API_PASSWORD", "admin123")
    response = requests.post(
        f"{api_url}/auth/login",
        data={"username": email, "password": password},
        timeout=15,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body.get("token_type") == "bearer"
    assert body.get("access_token")


def test_login_invalido_retorna_401(api_url):
    response = requests.post(
        f"{api_url}/auth/login",
        data={"username": "usuario_inexistente@teste.local", "password": "senha_errada"},
        timeout=15,
    )
    assert response.status_code == 401


def test_me_retorna_usuario_logado(get):
    response = get("/me")
    body = response.json()
    assert body["email"]
    assert body["perfil"]
