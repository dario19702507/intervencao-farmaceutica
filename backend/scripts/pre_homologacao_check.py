"""
Checagem pré-homologação multiusuário - 15B.4

Execute a partir da pasta backend:

    cd backend
    python scripts/pre_homologacao_check.py

O script não altera banco de dados nem arquivos do sistema. Ele apenas sinaliza riscos
básicos antes de liberar o sistema para teste online com múltiplos usuários.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = BASE_DIR.parent
PROD_ENVS = {"production", "homologation", "staging"}
ALLOWED_APP_ENVS = {"development", "homologation", "staging", "production"}
INSECURE_SECRET_VALUES = {
    "",
    "secret",
    "changeme",
    "admin123",
    "troque-esta-chave-em-producao",
    "alterar-para-uma-chave-longa-e-segura",
    "dev-secret-key-change-before-deploy",
}


def status(ok: bool) -> str:
    return "OK" if ok else "ATENÇÃO"


def check_file(path: Path, label: str) -> bool:
    exists = path.exists()
    print(f"[{status(exists)}] {label}: {path}")
    return exists


def read_text_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1", errors="ignore")
    except FileNotFoundError:
        return ""


def parse_env_text(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def env_from_file_or_process() -> tuple[dict[str, str], str]:
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        return parse_env_text(read_text_safe(env_path)), str(env_path)
    env_example = BASE_DIR / ".env.example"
    return parse_env_text(read_text_safe(env_example)), str(env_example) + " (modelo)"


def check_env_example() -> None:
    env_path = BASE_DIR / ".env.example"
    text = read_text_safe(env_path)
    if not text:
        print("[ATENÇÃO] .env.example não encontrado ou vazio.")
        return

    values = parse_env_text(text)
    risky_pairs = []
    secret_value = values.get("SECRET_KEY", "")
    if secret_value.lower() in INSECURE_SECRET_VALUES and secret_value:
        risky_pairs.append("SECRET_KEY preenchida com valor inseguro")
    if values.get("SEED_ADMIN_PASSWORD", ""):
        risky_pairs.append("SEED_ADMIN_PASSWORD preenchido no modelo")

    print(f"[{status(not risky_pairs)}] .env.example sem credenciais ou chaves inseguras preenchidas")
    if risky_pairs:
        print("    Revisar:", "; ".join(risky_pairs))


def check_runtime_env() -> None:
    values, source = env_from_file_or_process()
    app_env = (values.get("APP_ENV") or os.getenv("APP_ENV") or "development").lower()
    database_url = values.get("DATABASE_URL") or os.getenv("DATABASE_URL", "")
    secret_key = values.get("SECRET_KEY") or os.getenv("SECRET_KEY", "")
    origins = values.get("ALLOWED_ORIGINS") or os.getenv("ALLOWED_ORIGINS", "")
    seed_admin = (values.get("SEED_ADMIN") or os.getenv("SEED_ADMIN", "false")).lower()

    print(f"[INFO] Ambiente analisado: {source}")
    print(f"[INFO] APP_ENV={app_env}")
    print(f"[{status(app_env in ALLOWED_APP_ENVS)}] APP_ENV reconhecido")

    if app_env in PROD_ENVS:
        secret_ok = bool(secret_key) and len(secret_key) >= 40 and secret_key.lower() not in INSECURE_SECRET_VALUES
        db_ok = database_url.startswith(("postgresql://", "postgresql+psycopg2://"))
        admin_ok = seed_admin not in {"1", "true", "yes", "sim"}
        cors_ok = bool(origins) and "localhost" not in origins and "127.0.0.1" not in origins
        print(f"[{status(secret_ok)}] SECRET_KEY forte configurada para homologação/produção")
        print(f"[{status(db_ok)}] DATABASE_URL aponta para PostgreSQL/Supabase")
        print(f"[{status(admin_ok)}] SEED_ADMIN desativado")
        print(f"[{status(cors_ok)}] CORS sem localhost como origem principal")
    else:
        print("[OK] Ambiente local/desenvolvimento: SQLite e localhost são aceitáveis para testes locais")
        print(f"[{status(bool(origins))}] ALLOWED_ORIGINS configurado")


def check_main_security() -> None:
    main_path = BASE_DIR / "main.py"
    auth_path = BASE_DIR / "auth.py"
    main_text = read_text_safe(main_path)
    auth_text = read_text_safe(auth_path)
    combined = main_text + "\n" + auth_text
    combined_low = combined.lower()
    if not main_text:
        print("[ATENÇÃO] backend/main.py não encontrado.")
        return

    checks = {
        "middleware CORS configurado": "corsmiddleware" in combined_low,
        "uso de autenticação no backend": "get_current_user" in combined or "oauth2_scheme" in combined,
        "referência a permissões/perfis": "permissions" in combined_low or "perfil" in combined_low,
        "controle explícito de ambiente": "APP_ENV" in combined,
        "bloqueio de SECRET_KEY insegura em homologação/produção": (
            "SECRET_KEY insegura" in combined
            or "SECRET_KEY deve ser configurada" in combined
            or "dev-secret-key-change-before-deploy" in combined
        ),
        "controle do admin padrão por SEED_ADMIN": "SEED_ADMIN" in combined,
    }
    for label, ok in checks.items():
        print(f"[{status(ok)}] {label}")


def check_database() -> None:
    db_path = BASE_DIR / "intervencoes.db"
    if not db_path.exists():
        print("[ATENÇÃO] Banco SQLite local não encontrado em backend/intervencoes.db")
        return

    print(f"[OK] Banco SQLite local encontrado: {db_path}")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        print(f"[OK] Total de tabelas SQLite: {len(tables)}")
        principais = ["users", "intervencoes", "pacientes", "pacientes_clinicos", "evolucoes_clinicas"]
        encontrados = [t for t in principais if t in tables]
        print("[INFO] Tabelas principais encontradas:", ", ".join(encontrados) if encontrados else "nenhuma das esperadas")
    except Exception as exc:
        print(f"[ATENÇÃO] Não foi possível inspecionar o SQLite: {exc}")


def check_frontend_api() -> None:
    api_path = ROOT_DIR / "frontend" / "src" / "api" / "api.js"
    text = read_text_safe(api_path)
    text_low = text.lower()
    if not text:
        print("[ATENÇÃO] frontend/src/api/api.js não encontrado.")
        return

    checks = {
        "api.js existe": True,
        "usa token Authorization": "authorization" in text_low,
        "possui tratamento de erro": "interceptors" in text_low or "catch" in text_low,
        "possui X-Request-ID ou proteção contra requisição duplicada": (
            "x-request-id" in text_low
            or "pendingmutations" in text_low
            or "solicitação duplicada" in text_low
            or "solicitacao duplicada" in text_low
            or "duplic" in text_low
        ),
    }
    for label, ok in checks.items():
        print(f"[{status(ok)}] {label}")


def main() -> None:
    print("=== Checagem pré-homologação multiusuário - 15B.4 ===")
    print(f"Backend: {BASE_DIR}")
    print(f"Raiz do projeto: {ROOT_DIR}")
    print()

    check_file(BASE_DIR / "main.py", "Backend principal")
    check_file(BASE_DIR / "auth.py", "Autenticação")
    check_file(BASE_DIR / "permissions.py", "Permissões")
    check_file(BASE_DIR / ".env.example", "Modelo de variáveis de ambiente")
    check_file(ROOT_DIR / "frontend" / "src" / "api" / "api.js", "Cliente API frontend")
    print()

    check_env_example()
    print()
    check_runtime_env()
    print()
    check_main_security()
    print()
    check_database()
    print()
    check_frontend_api()
    print()

    print("Conclusão: para teste local, os itens essenciais devem aparecer como OK. Para homologação online, configure APP_ENV=homologation e repita a checagem.")


if __name__ == "__main__":
    main()
