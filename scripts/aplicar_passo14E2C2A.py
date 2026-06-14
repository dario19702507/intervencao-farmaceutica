"""Aplica o Passo 14E.2C.2A de forma idempotente.

Executar na raiz do projeto:
    python scripts\aplicar_passo14E2C2A.py
"""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Os arquivos do pacote devem ser extraídos diretamente na raiz do projeto.
# Este script apenas registra o novo router no main.py e atualiza o smoke test.


def copiar_arquivos() -> None:
    print("OK: arquivos do pacote já devem estar na estrutura do projeto")

def inserir_se_ausente(caminho: Path, marcador: str, texto: str, depois_de: str | None = None) -> None:
    conteudo = caminho.read_text(encoding="utf-8")
    if marcador in conteudo:
        return
    if depois_de and depois_de in conteudo:
        conteudo = conteudo.replace(depois_de, depois_de + texto, 1)
    else:
        conteudo += texto
    caminho.write_text(conteudo, encoding="utf-8")


def patch_main() -> None:
    caminho = ROOT / "backend" / "main.py"
    if not caminho.exists():
        print("AVISO: backend/main.py não encontrado; inclua o router manualmente.")
        return

    inserir_se_ausente(
        caminho,
        "intervencoes_padronizadas_router",
        "\nfrom routers.intervencoes_padronizadas import router as intervencoes_padronizadas_router",
        depois_de="from routers.atencao_farmaceutica import router as atencao_farmaceutica_router",
    )

    inserir_se_ausente(
        caminho,
        "app.include_router(intervencoes_padronizadas_router)",
        "\napp.include_router(intervencoes_padronizadas_router)",
        depois_de="app.include_router(atencao_farmaceutica_router)",
    )
    print("OK: backend/main.py atualizado")


def patch_smoke() -> None:
    caminho = ROOT / "tests" / "smoke_tests.py"
    if not caminho.exists():
        print("AVISO: tests/smoke_tests.py não encontrado; atualize manualmente.")
        return

    conteudo = caminho.read_text(encoding="utf-8")
    endpoints = [
        '("GET", "/consultorio/intervencoes-padronizadas/opcoes"),',
        '("GET", "/consultorio/intervencoes-padronizadas/dashboard"),',
    ]
    if all(e in conteudo for e in endpoints):
        print("OK: smoke_tests.py já estava atualizado")
        return

    linhas = conteudo.splitlines()
    novo = []
    dentro_endpoints = False
    inserido = False

    for linha in linhas:
        if linha.strip().startswith("ENDPOINTS") and "[" in linha:
            dentro_endpoints = True

        if dentro_endpoints and not inserido and linha.strip() == "]":
            for ep in endpoints:
                if ep not in conteudo:
                    novo.append(f"    {ep}")
            inserido = True
            dentro_endpoints = False

        novo.append(linha)

    if not inserido:
        raise RuntimeError("Não foi possível localizar a lista ENDPOINTS em tests/smoke_tests.py")

    conteudo = "\n".join(novo) + "\n"
    caminho.write_text(conteudo, encoding="utf-8")
    print("OK: tests/smoke_tests.py atualizado")


def main() -> None:
    copiar_arquivos()
    patch_main()
    patch_smoke()
    print("\nPasso 14E.2C.2A aplicado. Rode: pytest -q tests && python tests\\smoke_tests.py")


if __name__ == "__main__":
    main()
