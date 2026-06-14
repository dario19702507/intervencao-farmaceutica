def test_metas_opcoes(get):
    r = get('/consultorio/metas/opcoes')
    data = r.json()
    assert data['versao_catalogo']
    assert 'CONTROLE_CLINICO' in data['categorias']
    assert 'PRESSAO_ARTERIAL' in data['subcategorias']['CONTROLE_CLINICO']
    assert 'ATINGIDA' in data['status']


def test_metas_dashboard(get):
    r = get('/consultorio/metas/dashboard')
    data = r.json()
    assert 'resumo' in data
    assert 'por_status' in data
    assert 'por_categoria' in data
    assert 'taxa_padronizacao' in data['resumo']
