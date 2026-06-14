"""Aplica o Passo 14E.2C.3A — Metas Terapêuticas Estruturadas.

Executar na raiz do projeto:
    python scripts\aplicar_passo14E2C3A.py

O script é idempotente: pode ser executado mais de uma vez sem duplicar imports,
routers, colunas do modelo ou smoke tests.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def patch_model() -> None:
    path = ROOT / "backend" / "models" / "consultorio_models.py"
    text = read(path)
    if "# Passo 14E.2C.3A — metas estruturadas" in text:
        print("OK: modelo MetaTerapeutica já contém campos estruturados")
        return
    marker = '    problema_id = Column(Integer, ForeignKey("problemas_farmacoterapeuticos.id"), nullable=True, index=True)\n'
    insert = marker + '''
    # Passo 14E.2C.3A — metas estruturadas
    intervencao_farmacoterapia_id = Column(Integer, ForeignKey("intervencoes_farmacoterapia.id"), nullable=True, index=True)
    categoria = Column(String, nullable=True, index=True)  # CONTROLE_CLINICO, ADESAO, SEGURANCA, PROCESSO_ASSISTENCIAL, OUTRA
    subcategoria = Column(String, nullable=True, index=True)
    valor_atual = Column(String, nullable=True)
    data_inicial = Column(Date, nullable=True)
    data_prevista = Column(Date, nullable=True, index=True)
    data_conclusao = Column(Date, nullable=True)
    origem = Column(String, default="CONSULTA", index=True)
    codigo_catalogo = Column(String, nullable=True, index=True)
    versao_catalogo = Column(String, default="2026.06", index=True)
'''
    if marker not in text:
        raise SystemExit("ERRO: ponto de inserção não encontrado em MetaTerapeutica")
    text = text.replace(marker, insert, 1)
    # relacionamento opcional, se ainda não existir.
    rel_marker = '    problema = relationship("ProblemaFarmacoterapeutico")\n'
    if rel_marker in text and '    intervencao = relationship("IntervencaoFarmacoterapia")\n' not in text[text.find('class MetaTerapeutica'): text.find('class AcaoPlanoCuidado')]:
        text = text.replace(rel_marker, rel_marker + '    intervencao = relationship("IntervencaoFarmacoterapia")\n', 1)
    write(path, text)
    print("OK: modelo MetaTerapeutica atualizado")


def patch_migrations() -> None:
    path = ROOT / "backend" / "migrations.py"
    text = read(path)
    if "Passo 14E.2C.3A — metas terapêuticas estruturadas" in text:
        print("OK: migrations.py já atualizado")
        return
    anchor = '        _adicionar_coluna_se_nao_existir(conn, "catalogo_medicamentos", "classe_terapeutica VARCHAR")\n'
    bloco = '''

        # Passo 14E.2C.3A — metas terapêuticas estruturadas
        _adicionar_coluna_se_nao_existir(conn, "metas_terapeuticas", "intervencao_farmacoterapia_id INTEGER")
        _adicionar_coluna_se_nao_existir(conn, "metas_terapeuticas", "categoria VARCHAR")
        _adicionar_coluna_se_nao_existir(conn, "metas_terapeuticas", "subcategoria VARCHAR")
        _adicionar_coluna_se_nao_existir(conn, "metas_terapeuticas", "valor_atual VARCHAR")
        _adicionar_coluna_se_nao_existir(conn, "metas_terapeuticas", "data_inicial DATE")
        _adicionar_coluna_se_nao_existir(conn, "metas_terapeuticas", "data_prevista DATE")
        _adicionar_coluna_se_nao_existir(conn, "metas_terapeuticas", "data_conclusao DATE")
        _adicionar_coluna_se_nao_existir(conn, "metas_terapeuticas", "origem VARCHAR DEFAULT 'CONSULTA'")
        _adicionar_coluna_se_nao_existir(conn, "metas_terapeuticas", "codigo_catalogo VARCHAR")
        _adicionar_coluna_se_nao_existir(conn, "metas_terapeuticas", "versao_catalogo VARCHAR DEFAULT '2026.06'")
'''
    if anchor in text:
        text = text.replace(anchor, anchor + bloco, 1)
    else:
        # fallback: acrescenta antes do fim da função
        text += "\n" + bloco
    write(path, text)
    print("OK: migrations.py atualizado")


def patch_main() -> None:
    path = ROOT / "backend" / "main.py"
    text = read(path)
    if "metas_terapeuticas_router" not in text:
        import_anchor = "from routers.cuidado_farmaceutico import router as cuidado_farmaceutico_router\n"
        if import_anchor not in text:
            raise SystemExit("ERRO: import do cuidado_farmaceutico_router não encontrado em backend/main.py")
        text = text.replace(import_anchor, import_anchor + "from routers.metas_terapeuticas import router as metas_terapeuticas_router\n", 1)
    if "app.include_router(metas_terapeuticas_router)" not in text:
        include_anchor = "app.include_router(cuidado_farmaceutico_router)\n"
        if include_anchor not in text:
            raise SystemExit("ERRO: include_router do cuidado_farmaceutico_router não encontrado em backend/main.py")
        text = text.replace(include_anchor, include_anchor + "app.include_router(metas_terapeuticas_router)\n", 1)
    write(path, text)
    print("OK: backend/main.py atualizado")


def patch_smoke() -> None:
    path = ROOT / "tests" / "smoke_tests.py"
    text = read(path)
    endpoints = [
        '("GET", "/consultorio/metas/opcoes"),',
        '("GET", "/consultorio/metas/dashboard"),',
    ]
    for endpoint in endpoints:
        if endpoint not in text:
            marker = '("GET", "/consultorio/cuidado/prm-indicadores"),'
            if marker in text:
                text = text.replace(marker, marker + "\n    " + endpoint, 1)
            else:
                text = text.replace("\n]", "\n    " + endpoint + "\n]", 1)
    write(path, text)
    print("OK: tests/smoke_tests.py atualizado")


def main() -> int:
    patch_model()
    patch_migrations()
    patch_main()
    patch_smoke()
    print("\nPasso 14E.2C.3A aplicado. Rode: pytest -q tests && python tests\\smoke_tests.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
