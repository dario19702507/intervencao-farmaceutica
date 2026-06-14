
def test_opcoes_migracao_intervencoes(get):
    r = get("/consultorio/migracao-intervencoes/opcoes")
    data = r.json()
    assert data["origem_sistema"] == "APP_INTERVENCOES"
    assert data["idempotente"] is True
    assert "id" in data["campos_esperados"]


def test_dashboard_migracao_intervencoes(get):
    r = get("/consultorio/migracao-intervencoes/dashboard")
    data = r.json()
    assert "staging_por_status" in data
    assert "total_importado_final" in data



def test_painel_integracao_intervencoes(get):
    r = get("/consultorio/migracao-intervencoes/integracao-resumo")
    data = r.json()
    assert data["origem_sistema"] == "APP_INTERVENCOES"
    assert "total_staging" in data
    assert "consistencia" in data


def test_consistencia_migracao_intervencoes(get):
    r = get("/consultorio/migracao-intervencoes/consistencia")
    data = r.json()
    assert "resumo" in data
    assert "problemas" in data


def test_checkpoints_migracao_intervencoes(get):
    r = get("/consultorio/migracao-intervencoes/checkpoints")
    data = r.json()
    assert "checkpoints" in data


def test_rastreabilidade_migracao_intervencoes(get):
    r = get("/consultorio/migracao-intervencoes/rastreabilidade")
    data = r.json()
    assert "registros" in data
