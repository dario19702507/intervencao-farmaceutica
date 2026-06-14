"""Aplica automaticamente os includes do Passo 13C.0 no backend/main.py e no smoke test.
Execute na raiz do projeto: python scripts/aplicar_passo13C0.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "backend" / "main.py"
SMOKE = ROOT / "tests" / "smoke_tests.py"

IMPORT_LINE = "from routers.migracao_intervencoes import router as migracao_intervencoes_router"
INCLUDE_LINE = "app.include_router(migracao_intervencoes_router)"
SMOKE_LINE = '    check("GET", "/consultorio/migracao-intervencoes/opcoes", token)'


def patch_main():
    text = MAIN.read_text(encoding="utf-8")
    if IMPORT_LINE not in text:
        marker = "from routers.ocr_documentos import router as ocr_documentos_router"
        if marker in text:
            text = text.replace(marker, marker + "\n" + IMPORT_LINE)
        else:
            text = IMPORT_LINE + "\n" + text
    if INCLUDE_LINE not in text:
        marker = "app.include_router(ocr_documentos_router)"
        if marker in text:
            text = text.replace(marker, marker + "\n" + INCLUDE_LINE)
        else:
            insert_after = "app = FastAPI"
            lines = text.splitlines()
            for i, line in enumerate(lines):
                if line.startswith("app.include_router"):
                    lines.insert(i, INCLUDE_LINE)
                    text = "\n".join(lines) + "\n"
                    break
            else:
                text += "\n" + INCLUDE_LINE + "\n"
    MAIN.write_text(text, encoding="utf-8")


def patch_smoke():
    if not SMOKE.exists():
        return
    text = SMOKE.read_text(encoding="utf-8")
    if "/consultorio/migracao-intervencoes/opcoes" in text:
        return
    lines = text.splitlines()
    insert_idx = None
    for i, line in enumerate(lines):
        if "/consultorio/relatorios-gerenciais/documental" in line or "/consultorio/painel-operacional" in line:
            insert_idx = i + 1
    if insert_idx is None:
        for i in range(len(lines)-1, -1, -1):
            if "check(" in lines[i]:
                insert_idx = i + 1
                break
    if insert_idx is not None:
        lines.insert(insert_idx, SMOKE_LINE)
        SMOKE.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    patch_main()
    patch_smoke()
    print("Passo 13C.0 aplicado: main.py e smoke_tests.py atualizados.")
