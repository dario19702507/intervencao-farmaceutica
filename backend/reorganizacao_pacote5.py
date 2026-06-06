"""
Pacote 5 - Limpeza Final do consultorio.py

Objetivo:
- Criar backup automatico dos arquivos principais.
- Atualizar .gitignore com padroes de backup e arquivos temporarios.
- Gerar relatorio de rotas potencialmente duplicadas para revisao manual.
- NAO remove rotas automaticamente para evitar regressoes.

Execute dentro da pasta backend:
    python reorganizacao_pacote5.py
"""

from pathlib import Path
from datetime import datetime
import re
import shutil

ROOT = Path.cwd()
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_DIR = ROOT / f"backup_reorganizacao_pacote5_{STAMP}"
REPORT = ROOT / "README_reorganizacao_pacote5_resultado.md"


def backup_file(path: Path):
    if path.exists():
        BACKUP_DIR.mkdir(exist_ok=True)
        target = BACKUP_DIR / path.name
        shutil.copy2(path, target)
        print(f"[backup] {path} -> {target}")


def ensure_gitignore():
    gitignore = ROOT.parent / ".gitignore"
    existing = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""

    additions = [
        "# Backups e arquivos temporarios do saneamento/reorganizacao",
        "backend/backup_reorganizacao_*/",
        "backend/backup_reorganizacao_pacote*/",
        "backend/*.bak",
        "backend/*.sqbpro",
        "backend/routers/*.bak*",
        "backend/routers/*.backup*",
        "backend/README_reorganizacao_pacote*_resultado.md",
        "# Python",
        "__pycache__/",
        "*.pyc",
        "# Ambientes virtuais",
        "venv/",
        ".venv/",
        "backend/venv/",
        "frontend/venv/",
        "# Node",
        "node_modules/",
        "frontend/node_modules/",
        "frontend/dist/",
    ]

    missing = [line for line in additions if line not in existing]

    if missing:
        with gitignore.open("a", encoding="utf-8") as f:
            f.write("\n" + "\n".join(missing) + "\n")
        print(f"[ok] .gitignore atualizado: {gitignore}")
    else:
        print("[ok] .gitignore ja continha os padroes principais")


def find_routes(path: Path):
    if not path.exists():
        return []

    text = path.read_text(encoding="utf-8", errors="ignore")
    pattern = re.compile(
        r'@router\.(get|post|put|delete|patch)\("([^"]+)"\)\s*\ndef\s+([a-zA-Z0-9_]+)',
        re.M
    )
    return [
        {"method": m.group(1).upper(), "path": m.group(2), "function": m.group(3)}
        for m in pattern.finditer(text)
    ]


def write_report():
    files = [
        ROOT / "routers" / "consultorio.py",
        ROOT / "routers" / "agenda.py",
        ROOT / "routers" / "pacientes.py",
        ROOT / "routers" / "notificacoes.py",
        ROOT / "routers" / "auditoria.py",
        ROOT / "routers" / "atendimento_rapido.py",
        ROOT / "routers" / "indicadores_consultorio.py",
    ]

    all_routes = []
    for f in files:
        for route in find_routes(f):
            route["file"] = str(f.relative_to(ROOT))
            all_routes.append(route)

    seen = {}
    duplicates = []
    for r in all_routes:
        key = (r["method"], r["path"])
        if key in seen:
            duplicates.append((seen[key], r))
        else:
            seen[key] = r

    lines = [
        "# Resultado - Reorganizacao Pacote 5",
        "",
        f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        "",
        "## Acoes realizadas",
        "",
        "- Backup dos arquivos principais em pasta local.",
        "- Atualizacao do `.gitignore` para evitar versionamento de backups, `.bak`, `.sqbpro`, `venv`, `node_modules` e `dist`.",
        "- Varredura de rotas nos modulos principais.",
        "- Nenhuma rota foi removida automaticamente.",
        "",
        "## Total de rotas encontradas",
        "",
        str(len(all_routes)),
        "",
        "## Rotas potencialmente duplicadas",
        "",
    ]

    if duplicates:
        for a, b in duplicates:
            lines.append(f"- `{a['method']} {a['path']}` em `{a['file']}` / `{b['file']}`")
    else:
        lines.append("Nenhuma duplicidade exata de metodo + caminho foi detectada entre os modulos analisados.")

    lines += [
        "",
        "## Proxima revisao manual sugerida",
        "",
        "1. Conferir se `consultorio.py` ainda contem rotas ja migradas para `agenda.py`, `pacientes.py` e `notificacoes.py`.",
        "2. Se houver duplicidade funcional sem duplicidade exata de caminho, remover manualmente apenas depois de testar Swagger e frontend.",
        "3. Fazer novo commit/tag apos validacao.",
        "",
        "## Comandos de validacao",
        "",
        "```bash",
        "python -m py_compile routers/consultorio.py",
        "python -m py_compile routers/agenda.py",
        "python -m py_compile routers/pacientes.py",
        "python -m py_compile routers/notificacoes.py",
        "python -m py_compile main.py",
        "uvicorn main:app --reload",
        "```",
    ]

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"[ok] relatorio criado: {REPORT}")


def main():
    print("== Pacote 5 - Limpeza Final ==")

    for relative in [
        "main.py",
        "routers/consultorio.py",
        "routers/agenda.py",
        "routers/pacientes.py",
        "routers/notificacoes.py",
        "models/consultorio_models.py",
        "schemas/consultorio_schemas.py",
    ]:
        backup_file(ROOT / relative)

    ensure_gitignore()
    write_report()

    print("\nConcluido.")
    print("Nenhuma rota foi removida automaticamente.")
    print("Leia README_reorganizacao_pacote5_resultado.md antes de qualquer remocao manual.")


if __name__ == "__main__":
    main()
