
def test_opcoes_intervencoes_padronizadas(get):
    r = get("/consultorio/intervencoes-padronizadas/opcoes")
    data = r.json()
    assert "tipos_intervencao" in data
    assert len(data["tipos_intervencao"]) >= 5
    assert data["versao_catalogo"]


def test_dashboard_intervencoes_padronizadas(get):
    r = get("/consultorio/intervencoes-padronizadas/dashboard")
    data = r.json()
    assert "resumo" in data
    assert "taxa_mapeamento" in data["resumo"]
    assert "por_tipo_padronizado" in data
