def test_opcoes_cuidado_farmaceutico(get):
    response = get("/consultorio/cuidado/opcoes")
    data = response.json()
    assert "prm_categorias" in data
    assert "prm_catalogo" in data
    assert "prm_naturezas" in data
    assert "prm_criticidades" in data
    assert "prm_desfechos" in data
    assert "NECESSIDADE" in data["prm_catalogo"]
    assert "METADADOS" not in data["prm_catalogo"]
    assert "metas_parametros" in data
    assert "regra" in data


def test_dashboard_cuidado_farmaceutico(get):
    response = get("/consultorio/cuidado/dashboard")
    data = response.json()
    assert isinstance(data, dict)
    assert "prms_abertos" in data
    assert "metas_ativas" in data


def test_opcoes_timeline_unificada(get):
    response = get("/consultorio/cuidado/timeline-unificada/opcoes")
    data = response.json()
    assert "categorias" in data
    assert "CEAF" in data["categorias"]
    assert "DOCUMENTOS" in data["categorias"]
    assert "PRM" in data["categorias"]


def test_indicadores_prm_globais(get):
    response = get("/consultorio/cuidado/prm-indicadores")
    data = response.json()
    assert "resumo" in data
    assert "distribuicoes" in data
    assert "tempos" in data
    assert "por_categoria" in data["distribuicoes"]
    assert "taxa_padronizacao_percentual" in data["resumo"]
    assert data["catalogo"]["sistema_codificacao"] == "PRM_FE_NEES_V1"
