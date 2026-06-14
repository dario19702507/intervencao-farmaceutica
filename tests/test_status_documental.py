
def test_opcoes_status_documental(get):
    r = get("/consultorio/documentos/status-opcoes")
    data = r.json()
    assert "VALIDADO" in data["status_documental"]
    assert "REJEITADO" in data["status_documental"]
    assert data["whatsapp_documental"]


def test_dashboard_status_documental(get):
    r = get("/consultorio/documentos/status-dashboard")
    data = r.json()
    assert "por_status_documental" in data
    assert "validados" in data
    assert "recebidos_pendentes_de_validacao" in data
