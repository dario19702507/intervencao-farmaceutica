
def test_relatorios_gerenciais_opcoes(get):
    r = get("/consultorio/relatorios-gerenciais/opcoes")
    data = r.json()
    assert "OPERACIONAL" in data["tipos_relatorio"]
    assert "PDF" in data["formatos_exportacao"]
    assert "XLSX" in data["formatos_exportacao"]


def test_relatorio_operacional(get):
    r = get("/consultorio/relatorios-gerenciais/operacional")
    data = r.json()
    assert data["tipo"] == "OPERACIONAL"
    assert "indicadores" in data


def test_relatorio_vigencias(get):
    r = get("/consultorio/relatorios-gerenciais/vigencias")
    data = r.json()
    assert data["tipo"] == "VIGENCIAS"
    assert "indicadores" in data


def test_relatorio_documental(get):
    r = get("/consultorio/relatorios-gerenciais/documental")
    data = r.json()
    assert data["tipo"] == "DOCUMENTAL"
    assert "indicadores" in data


def test_relatorios_gerenciais_xlsx_endpoints_exist(get):
    # Não valida conteúdo binário para manter o teste leve; garante que as rotas estejam registradas.
    for path in [
        "/consultorio/relatorios-gerenciais/operacional/xlsx",
        "/consultorio/relatorios-gerenciais/vigencias/xlsx",
        "/consultorio/relatorios-gerenciais/documental/xlsx",
    ]:
        r = get(path)
        assert r.status_code == 200
        assert "spreadsheetml" in r.headers.get("content-type", "")
