"""
Gera uma SECRET_KEY forte para homologação/produção.

Uso:
    cd backend
    python scripts/gerar_secret_key.py

Copie o valor exibido para a variável SECRET_KEY no Render ou no arquivo .env local.
"""

from __future__ import annotations

import secrets


def main() -> None:
    print(secrets.token_urlsafe(64))


if __name__ == "__main__":
    main()
