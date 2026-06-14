"""
Testes de fumaça do Sistema de Intervenção Farmacêutica.
Uso:
  1. Inicie o backend: uvicorn main:app --reload
  2. Execute: python smoke_tests_intervencao_farmaceutica.py
Ajuste BASE_URL, USERNAME e PASSWORD se necessário.
"""
import requests
from typing import Iterable

BASE_URL = "http://127.0.0.1:8000"
USERNAME = "admin@farmacia.local"
PASSWORD = "admin123"
TIMEOUT = 15


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def login() -> str:
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": USERNAME, "password": PASSWORD},
        timeout=TIMEOUT,
    )
    check(response.status_code == 200, f"Falha no login: {response.status_code} {response.text}")
    data = response.json()
    token = data.get("access_token")
    check(bool(token), "Resposta de login sem access_token")
    return token


def get(path: str, token: str, allowed: Iterable[int] = (200,)) -> None:
    response = requests.get(
        f"{BASE_URL}{path}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=TIMEOUT,
    )
    check(response.status_code in allowed, f"GET {path}: {response.status_code} {response.text[:500]}")
    print(f"OK GET {path} -> {response.status_code}")


def main() -> None:
    token = login()
    print("OK POST /auth/login")

    endpoints = [
        "/me",
        "/indicadores",
        "/consultorio/pacientes-simplificados",
        "/consultorio/pacientes-clinicos",
        "/consultorio/dashboard-servicos",
        "/consultorio/triagem-risco",
        "/consultorio/dashboard-farmacoterapeutico",
        "/consultorio/dashboard-epidemiologico",
        "/consultorio/dashboard-efetividade-cuidado",
        "/consultorio/alertas-pendentes",
    ]

    for endpoint in endpoints:
        get(endpoint, token, allowed=(200, 204))

    print("\nTodos os testes de fumaça passaram.")


if __name__ == "__main__":
    main()
