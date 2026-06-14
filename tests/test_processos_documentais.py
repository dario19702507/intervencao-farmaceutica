"""Testes do Passo 11F - Processos/Pacotes Documentais."""


def test_opcoes_processos_documentais(get):
    r = get("/consultorio/processos-documentais/opcoes")
    data = r.json()
    assert "INCLUSAO" in data["tipos_processo"]
    assert "RENOVACAO" in data["tipos_processo"]
    assert data["documentos_recomendados"]["INCLUSAO"]
    assert "somente manual" in data["regra_whatsapp_documental"].lower()


def test_dashboard_processos_documentais(get):
    r = get("/consultorio/processos-documentais/dashboard")
    data = r.json()
    assert "total" in data
    assert "regra_whatsapp_documental" in data
