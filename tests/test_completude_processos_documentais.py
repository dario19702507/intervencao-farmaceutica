"""Testes do Passo 12C.4 - Validação de completude do pacote documental."""


def test_dashboard_completude_processos_documentais(get):
    r = get("/consultorio/processos-documentais/completude-dashboard")
    data = r.json()
    assert "total_processos" in data
    assert "por_status" in data
    assert data["whatsapp_documental_automatico"] is False
    assert "somente manual" in data["regra_whatsapp_documental"].lower()


def test_opcoes_incluem_documentos_recomendados(get):
    r = get("/consultorio/processos-documentais/opcoes")
    data = r.json()
    assert "documentos_recomendados" in data
    assert "INCLUSAO" in data["documentos_recomendados"]
    assert "RENOVACAO" in data["documentos_recomendados"]
