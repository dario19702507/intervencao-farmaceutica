"""Importa intervenções do App de Intervenções para staging via API.

Uso:
    python scripts\importar_intervencoes_staging.py --arquivo scripts\intervencoes_rows.json

Variáveis opcionais:
    set API_URL=http://127.0.0.1:8000
    set API_EMAIL=admin@farmacia.local
    set API_PASSWORD=admin123
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import requests


API_URL = os.getenv("API_URL", "http://127.0.0.1:8000").rstrip("/")
EMAIL = os.getenv("API_EMAIL", "admin@farmacia.local")
PASSWORD = os.getenv("API_PASSWORD", "admin123")


def login() -> str:
    response = requests.post(
        f"{API_URL}/auth/login",
        data={"username": EMAIL, "password": PASSWORD},
        timeout=30,
    )
    print("POST /auth/login", response.status_code)
    if response.status_code != 200:
        print(response.text[:1000])
        raise SystemExit(1)

    token = response.json().get("access_token")
    if not token:
        print("ERRO: token não retornado pelo backend.")
        raise SystemExit(1)
    return token


def preparar_estrutura(headers: dict[str, str]) -> None:
    response = requests.post(
        f"{API_URL}/consultorio/migracao-intervencoes/preparar-estrutura",
        headers=headers,
        timeout=60,
    )
    print("POST /consultorio/migracao-intervencoes/preparar-estrutura", response.status_code)
    if response.status_code >= 400:
        print(response.text[:1000])
        raise SystemExit(1)


def criar_checkpoint(headers: dict[str, str], etapa: str, descricao: str) -> None:
    response = requests.post(
        f"{API_URL}/consultorio/migracao-intervencoes/checkpoint",
        headers=headers,
        params={"etapa": etapa, "descricao": descricao},
        timeout=60,
    )
    print("POST /consultorio/migracao-intervencoes/checkpoint", response.status_code)
    if response.status_code >= 400:
        print(response.text[:1000])
        raise SystemExit(1)


def importar_staging(headers: dict[str, str], arquivo: Path) -> dict:
    if not arquivo.exists():
        print(f"ERRO: arquivo não encontrado: {arquivo}")
        raise SystemExit(1)

    with arquivo.open("rb") as f:
        files = {"arquivo": (arquivo.name, f, "application/json")}
        response = requests.post(
            f"{API_URL}/consultorio/migracao-intervencoes/staging/importar-json",
            headers=headers,
            files=files,
            timeout=120,
        )

    print("POST /consultorio/migracao-intervencoes/staging/importar-json", response.status_code)
    if response.status_code >= 400:
        print(response.text[:2000])
        raise SystemExit(1)

    return response.json()


def dashboard(headers: dict[str, str]) -> dict:
    response = requests.get(
        f"{API_URL}/consultorio/migracao-intervencoes/dashboard",
        headers=headers,
        timeout=60,
    )
    print("GET /consultorio/migracao-intervencoes/dashboard", response.status_code)
    if response.status_code >= 400:
        print(response.text[:1000])
        raise SystemExit(1)
    return response.json()


def main() -> int:
    parser = argparse.ArgumentParser(description="Importa JSON do Supabase para staging de intervenções.")
    parser.add_argument(
        "--arquivo",
        default="scripts/intervencoes_rows.json",
        help="Caminho do JSON exportado do Supabase. Padrão: scripts/intervencoes_rows.json",
    )
    parser.add_argument(
        "--sem-checkpoint",
        action="store_true",
        help="Não cria checkpoint antes da importação.",
    )
    args = parser.parse_args()

    arquivo = Path(args.arquivo)

    print(f"API_URL: {API_URL}")
    print(f"Arquivo: {arquivo}")

    token = login()
    headers = {"Authorization": f"Bearer {token}"}

    preparar_estrutura(headers)

    if not args.sem_checkpoint:
        criar_checkpoint(
            headers,
            etapa="PRE_IMPORTACAO_STAGING",
            descricao=f"Checkpoint antes da importação em staging do arquivo {arquivo.name}",
        )

    resultado = importar_staging(headers, arquivo)
    print("\nResultado da importação em staging:")
    print(json.dumps(resultado, ensure_ascii=False, indent=2, default=str))

    resumo = dashboard(headers)
    print("\nDashboard de migração:")
    print(json.dumps(resumo, ensure_ascii=False, indent=2, default=str))

    return 0


if __name__ == "__main__":
    sys.exit(main())
