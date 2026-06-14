"""
Backup automático do banco de dados do Sistema de Intervenção Farmacêutica.

Uso, a partir da raiz do projeto:
    python backup_database.py

Compatível com:
- SQLite: copia segura do arquivo .db em uso.
- PostgreSQL/Supabase: executa pg_dump quando disponível no sistema.

As configurações são lidas de backend/.env ou das variáveis de ambiente.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

try:
    from dotenv import load_dotenv
except ImportError:  # fallback para ambientes mínimos
    load_dotenv = None

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
BACKUP_DIR = ROOT_DIR / "backups"
DEFAULT_RETENTION = 30


def carregar_ambiente() -> str:
    """Carrega DATABASE_URL do backend/.env, se existir."""
    env_path = BACKEND_DIR / ".env"
    if load_dotenv and env_path.exists():
        load_dotenv(env_path)
    return os.getenv("DATABASE_URL", "sqlite:///./intervencoes.db")


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def resolver_sqlite_path(database_url: str) -> Path:
    raw_path = database_url.replace("sqlite:///", "", 1)
    db_path = Path(raw_path)
    if not db_path.is_absolute():
        # O backend roda a partir da pasta backend; portanto ./intervencoes.db fica em backend/.
        db_path = BACKEND_DIR / db_path
    return db_path.resolve()


def backup_sqlite(database_url: str) -> Path:
    db_path = resolver_sqlite_path(database_url)
    if not db_path.exists():
        raise FileNotFoundError(f"Banco SQLite não encontrado: {db_path}")

    BACKUP_DIR.mkdir(exist_ok=True)
    destino = BACKUP_DIR / f"backup_sqlite_{timestamp()}.db"

    # Backup transacional via API sqlite3, mais seguro que uma cópia crua com o app ligado.
    origem_conn = sqlite3.connect(str(db_path))
    try:
        destino_conn = sqlite3.connect(str(destino))
        try:
            origem_conn.backup(destino_conn)
        finally:
            destino_conn.close()
    finally:
        origem_conn.close()

    return destino


def backup_postgres(database_url: str) -> Path:
    if shutil.which("pg_dump") is None:
        raise RuntimeError(
            "pg_dump não foi encontrado. Instale PostgreSQL Client Tools ou gere backup pelo painel do Supabase."
        )

    BACKUP_DIR.mkdir(exist_ok=True)
    destino = BACKUP_DIR / f"backup_postgres_{timestamp()}.sql"

    comando = [
        "pg_dump",
        database_url,
        "--no-owner",
        "--no-privileges",
        "--file",
        str(destino),
    ]

    subprocess.run(comando, check=True)
    return destino


def limpar_backups_antigos(retention: int) -> None:
    if retention <= 0 or not BACKUP_DIR.exists():
        return

    backups = sorted(
        [p for p in BACKUP_DIR.iterdir() if p.is_file() and p.name.startswith("backup_")],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    for antigo in backups[retention:]:
        antigo.unlink(missing_ok=True)


def criar_backup(retention: int = DEFAULT_RETENTION) -> Path:
    database_url = carregar_ambiente()

    if database_url.startswith("sqlite"):
        destino = backup_sqlite(database_url)
    elif database_url.startswith(("postgresql", "postgres")):
        destino = backup_postgres(database_url)
    else:
        raise ValueError(f"DATABASE_URL não suportada para backup automático: {database_url}")

    limpar_backups_antigos(retention)
    return destino


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera backup do banco de dados do projeto.")
    parser.add_argument("--retention", type=int, default=DEFAULT_RETENTION, help="Quantidade de backups a manter.")
    args = parser.parse_args()

    try:
        destino = criar_backup(retention=args.retention)
    except Exception as exc:
        print(f"ERRO ao gerar backup: {exc}", file=sys.stderr)
        return 1

    print(f"Backup gerado com sucesso: {destino}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
