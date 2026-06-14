"""Testes do Passo 12E - Pré-preenchimento assistido."""


def test_opcoes_preenchimento_assistido(get):
    r = get("/consultorio/preenchimento-assistido/opcoes")
    data = r.json()
    assert data["atualizacao_automatica"] is False
    assert "DOCUMENTOS_VALIDADOS" in data["fontes_autorizadas"]
    assert "cid" in data["campos_assistidos"]


def test_sugestoes_processo_inexistente_retorna_404(get):
    get("/consultorio/processos-documentais/999999/preenchimento-assistido", expected_status=404)
