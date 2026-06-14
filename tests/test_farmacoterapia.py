
def test_dashboard_farmacoterapeutico(get):
    response = get("/consultorio/dashboard-farmacoterapeutico")
    assert isinstance(response.json(), dict)


def test_alertas_pendentes(get):
    response = get("/consultorio/alertas-pendentes")
    assert response.status_code == 200
