"""Testes de fumaça do Sistema de Intervenção Farmacêutica.

Executar com backend ativo:
    python tests/smoke_tests.py

Configurar se necessário no Windows CMD:
    set API_URL=http://127.0.0.1:8000
    set API_EMAIL=admin@farmacia.local
    set API_PASSWORD=admin123
"""
import os
import sys
import requests

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000").rstrip("/")
EMAIL = os.getenv("API_EMAIL", "admin@farmacia.local")
PASSWORD = os.getenv("API_PASSWORD", "admin123")

ENDPOINTS = [
    ("GET", "/me"),
    ("GET", "/indicadores"),
    ("GET", "/consultorio/pacientes-clinicos"),
    ("GET", "/consultorio/dashboard-servicos"),
    ("GET", "/consultorio/triagem-risco"),
    ("GET", "/consultorio/dashboard-farmacoterapeutico"),
    ("GET", "/consultorio/dashboard-efetividade-cuidado"),
    ("GET", "/consultorio/agenda/dashboard"),
    ("GET", "/consultorio/catalogo-medicamentos"),
    ("GET", "/consultorio/agenda/opcoes"),
    ("GET", "/consultorio/notificacoes/dashboard"),
    ("GET", "/consultorio/notificacoes/nao-lidas"),
    ("GET", "/consultorio/whatsapp/dashboard"),
    ("GET", "/consultorio/whatsapp/fila"),
    ("GET", "/consultorio/whatsapp/opcoes"),
    ("GET", "/consultorio/documentos/opcoes"),
    ("GET", "/consultorio/documentos/validade-dashboard"),
    ("GET", "/consultorio/documentos/vencimentos"),
    ("GET", "/consultorio/processos-documentais/opcoes"),
    ("GET", "/consultorio/processos-documentais/dashboard"),
    ("GET", "/consultorio/documentos/status-opcoes"),
    ("GET", "/consultorio/documentos/status-dashboard"),
    ("GET", "/consultorio/preenchimento-assistido/opcoes"),
    ("GET", "/consultorio/painel-operacional"),
    ("GET", "/consultorio/relatorios-gerenciais/opcoes"),
    ("GET", "/consultorio/relatorios-gerenciais/operacional"),
    ("GET", "/consultorio/relatorios-gerenciais/vigencias"),
    ("GET", "/consultorio/relatorios-gerenciais/documental"),
    ("GET", "/consultorio/migracao-intervencoes/opcoes"),
    ("GET", "/consultorio/migracao-intervencoes/integracao-resumo"),
    ("GET", "/consultorio/migracao-intervencoes/checkpoints"),
    ("GET", "/consultorio/migracao-intervencoes/consistencia"),
    ("GET", "/consultorio/migracao-intervencoes/rastreabilidade"),
    ("GET", "/consultorio/cuidado/opcoes"),
    ("GET", "/consultorio/cuidado/dashboard"),
    ("GET", "/consultorio/cuidado/prm-indicadores"),
    ("GET", "/consultorio/metas/dashboard"),
    ("GET", "/consultorio/metas/opcoes"),
    ("GET", "/consultorio/cuidado/timeline-unificada/opcoes"),
    ("GET", "/consultorio/farmacoterapia/opcoes"),
    ("GET", "/consultorio/atencao-farmaceutica/opcoes"),
    ("GET", "/consultorio/atencao-farmaceutica/dashboard"),
    ("GET", "/consultorio/atencao-farmaceutica/pendencias"),
    ("GET", "/consultorio/intervencoes-padronizadas/opcoes"),
    ("GET", "/consultorio/intervencoes-padronizadas/dashboard"),
]


def main():
    try:
        login = requests.post(
            f"{API_URL}/auth/login",
            data={"username": EMAIL, "password": PASSWORD},
            timeout=15,
        )
    except requests.RequestException as exc:
        print("ERRO: backend indisponível.")
        print("Inicie em outro terminal: cd backend && uvicorn main:app --reload")
        print(f"Detalhe: {exc}")
        return 1

    print("POST /auth/login", login.status_code)
    if login.status_code != 200:
        print(login.text)
        return 1

    token = login.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    failures = 0

    for method, path in ENDPOINTS:
        try:
            resp = requests.request(method, f"{API_URL}{path}", headers=headers, timeout=20)
        except requests.RequestException as exc:
            failures += 1
            print(method, path, "ERRO", exc)
            continue
        print(method, path, resp.status_code)
        if resp.status_code >= 400:
            failures += 1
            print(resp.text[:500])

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
