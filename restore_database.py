"""
Restauração controlada de backup do banco de dados.

Uso, a partir da raiz do projeto:
    python restore_database.py --file backups/backup_sqlite_YYYYMMDD_HHMMSS.db

A restauração SQLite cria automaticamente uma cópia de segurança do banco atual antes de substituir.
Para PostgreSQL/Supabase, requer psql instalado e um arquivo .sql gerado por pg_dump.
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

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
BACKUP_DIR = ROOT_DIR / "backups"


def carregar_ambiente() -> str:
    env_path = BACKEND_DIR / ".env"
    if load_dotenv and env_path.exists():
        load_dotenv(env_path)
    return os.getenv("DATABASE_URL", "sqlite:///./intervencoes.db")


def resolver_sqlite_path(database_url: str) -> Path:
    raw_path = database_url.replace("sqlite:///", "", 1)
    db_path = Path(raw_path)
    if not db_path.is_absolute():
        db_path = BACKEND_DIR / db_path
    return db_path.resolve()


def validar_sqlite_backup(arquivo: Path) -> None:
    try:
        conn = sqlite3.connect(str(arquivo))
        try:
            conn.execute("PRAGMA integrity_check;").fetchone()
        finally:
            conn.close()
    except sqlite3.DatabaseError as exc:
        raise ValueError(f"Arquivo de backup SQLite inválido: {arquivo}") from exc


def restaurar_sqlite(database_url: str, backup_file: Path) -> Path:
    if backup_file.suffix.lower() not in {".db", ".sqlite", ".sqlite3"}:
        raise ValueError("Para SQLite, informe um arquivo .db, .sqlite ou .sqlite3")

    if not backup_file.exists():
        raise FileNotFoundError(f"Backup não encontrado: {backup_file}")

    validar_sqlite_backup(backup_file)

    destino_db = resolver_sqlite_path(database_url)
    destino_db.parent.mkdir(parents=True, exist_ok=True)

    copia_atual = None
    if destino_db.exists():
        copia_atual = destino_db.with_name(f"{destino_db.stem}_antes_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}{destino_db.suffix}")
        shutil.copy2(destino_db, copia_atual)

    shutil.copy2(backup_file, destino_db)
    return copia_atual


def restaurar_postgres(database_url: str, backup_file: Path) -> None:
    if shutil.which("psql") is None:
        raise RuntimeError("psql não foi encontrado. Instale PostgreSQL Client Tools para restaurar via script.")
    if backup_file.suffix.lower() != ".sql":
        raise ValueError("Para PostgreSQL, informe um arquivo .sql")
    subprocess.run(["psql", database_url, "-f", str(backup_file)], check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Restaura backup do banco de dados do projeto.")
    parser.add_argument("--file", required=True, help="Caminho do arquivo de backup a restaurar.")
    parser.add_argument("--yes", action="store_true", help="Confirma a restauração sem prompt interativo.")
    args = parser.parse_args()

    backup_file = Path(args.file).resolve()
    database_url = carregar_ambiente()

    if not args.yes:
        print("ATENÇÃO: a restauração substituirá o banco atual.")
        print(f"Backup selecionado: {backup_file}")
        confirmar = input("Digite RESTAURAR para continuar: ").strip()
        if confirmar != "RESTAURAR":
            print("Restauração cancelada.")
            return 0

    try:
        if database_url.startswith("sqlite"):
            copia_atual = restaurar_sqlite(database_url, backup_file)
            print("Restauração SQLite concluída.")
            if copia_atual:
                print(f"Cópia do banco anterior: {copia_atual}")
        elif database_url.startswith(("postgresql", "postgres")):
            restaurar_postgres(database_url, backup_file)
            print("Restauração PostgreSQL concluída.")
        else:
            raise ValueError(f"DATABASE_URL não suportada para restauração: {database_url}")
    except Exception as exc:
        print(f"ERRO ao restaurar backup: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
