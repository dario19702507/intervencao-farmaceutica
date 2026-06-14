
def test_opcoes_disponiveis(get):
    response = get("/opcoes")
    body = response.json()
    assert "motivos" in body
    assert "tipos_intervencao" in body


def test_indicadores_gerais(get):
    response = get("/indicadores")
    assert isinstance(response.json(), dict)


def test_listagem_intervencoes(get):
    response = get("/intervencoes")
    assert isinstance(response.json(), list)
