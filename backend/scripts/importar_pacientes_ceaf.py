"""Importa planilha CEAF pela API do backend.

Uso local:
    python backend/scripts/importar_pacientes_ceaf.py --arquivo caminho.xls --api-url https://... --email ... --senha ...

O script autentica em /auth/login e envia a planilha para /ceaf/pacientes/importar-planilha.
"""

import argparse
import json
from pathlib import Path

import requests


def main() -> None:
    parser = argparse.ArgumentParser(description="Importar planilha CEAF pela API")
    parser.add_argument("--arquivo", required=True, help="Caminho do arquivo .xls, .xlsx ou .csv")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000", help="URL base do backend")
    parser.add_argument("--email", required=True, help="E-mail do usuário administrador/farmacêutico")
    parser.add_argument("--senha", required=True, help="Senha do usuário")
    parser.add_argument("--nao-atualizar", action="store_true", help="Não atualizar registros já existentes")
    args = parser.parse_args()

    arquivo = Path(args.arquivo)
    if not arquivo.exists():
        raise SystemExit(f"Arquivo não encontrado: {arquivo}")

    api_url = args.api_url.rstrip("/")

    login_resp = requests.post(
        f"{api_url}/auth/login",
        data={"username": args.email, "password": args.senha},
        timeout=60,
    )
    if login_resp.status_code >= 400:
        raise SystemExit(f"Falha no login: {login_resp.status_code} {login_resp.text}")

    token = login_resp.json().get("access_token")
    if not token:
        raise SystemExit("Login não retornou access_token.")

    with arquivo.open("rb") as f:
        resp = requests.post(
            f"{api_url}/ceaf/pacientes/importar-planilha",
            params={"atualizar_existentes": str(not args.nao_atualizar).lower()},
            files={"arquivo": (arquivo.name, f, "application/octet-stream")},
            headers={"Authorization": f"Bearer {token}"},
            timeout=300,
        )

    print(f"Status: {resp.status_code}")
    try:
        print(json.dumps(resp.json(), ensure_ascii=False, indent=2))
    except Exception:
        print(resp.text)

    if resp.status_code >= 400:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
