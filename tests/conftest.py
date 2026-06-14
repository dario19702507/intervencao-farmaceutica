"""Configuração compartilhada dos testes automatizados.

Os testes assumem que o backend FastAPI esteja rodando antes da execução.
Exemplo:
    cd backend
    uvicorn main:app --reload

Em outro terminal:
    pytest -q tests
"""
import os
import pytest
import requests

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000").rstrip("/")
API_EMAIL = os.getenv("API_EMAIL", "admin@farmacia.local")
API_PASSWORD = os.getenv("API_PASSWORD", "admin123")


def _assert_backend_online():
    try:
        response = requests.get(f"{API_URL}/docs", timeout=5)
    except requests.RequestException as exc:
        pytest.fail(
            "Backend indisponível. Inicie o servidor com: "
            "cd backend && uvicorn main:app --reload. "
            f"Detalhe: {exc}"
        )
    assert response.status_code in (200, 307), f"Backend respondeu {response.status_code} em /docs"


@pytest.fixture(scope="session")
def api_url():
    return API_URL


@pytest.fixture(scope="session")
def token(api_url):
    _assert_backend_online()
    response = requests.post(
        f"{api_url}/auth/login",
        data={"username": API_EMAIL, "password": API_PASSWORD},
        timeout=15,
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    return data["access_token"]


@pytest.fixture(scope="session")
def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def get(api_url, auth_headers):
    def _get(path: str, expected_status: int = 200):
        response = requests.get(f"{api_url}{path}", headers=auth_headers, timeout=20)
        assert response.status_code == expected_status, response.text[:1000]
        return response
    return _get
