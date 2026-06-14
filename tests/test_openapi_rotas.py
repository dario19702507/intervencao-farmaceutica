import requests

ROTAS_OBRIGATORIAS = [
    "/auth/login",
    "/me",
    "/indicadores",
    "/consultorio/pacientes-clinicos",
    "/consultorio/dashboard-servicos",
    "/consultorio/triagem-risco",
    "/consultorio/dashboard-farmacoterapeutico",
    "/consultorio/dashboard-efetividade-cuidado",
    "/consultorio/agenda/dashboard",
    "/consultorio/catalogo-medicamentos",
    "/consultorio/agenda/opcoes",
]


def test_openapi_contem_rotas_criticas(api_url):
    response = requests.get(f"{api_url}/openapi.json", timeout=15)
    assert response.status_code == 200, response.text
    paths = response.json().get("paths", {})
    for rota in ROTAS_OBRIGATORIAS:
        assert rota in paths, f"Rota ausente no OpenAPI: {rota}"
