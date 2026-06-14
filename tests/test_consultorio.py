
def test_pacientes_clinicos(get):
    response = get("/consultorio/pacientes-clinicos")
    assert response.status_code == 200


def test_dashboard_servicos(get):
    response = get("/consultorio/dashboard-servicos")
    assert isinstance(response.json(), dict)


def test_triagem_risco(get):
    response = get("/consultorio/triagem-risco")
    assert response.status_code == 200


def test_dashboard_efetividade_cuidado(get):
    response = get("/consultorio/dashboard-efetividade-cuidado")
    assert isinstance(response.json(), dict)
