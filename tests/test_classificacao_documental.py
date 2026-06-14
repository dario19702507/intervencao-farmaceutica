from services.ocr_documentos import classificar_documento, sugerir_campos


def test_classifica_laudo_lme():
    texto = "LAUDO PARA SOLICITAÇÃO DE MEDICAMENTO DO COMPONENTE ESPECIALIZADO CID J45.5 medicamento solicitado"
    resultado = classificar_documento(texto)
    assert resultado["tipo"] == "LAUDO"
    assert resultado["confianca"] >= 0.65
    assert resultado["atualizacao_automatica"] is False


def test_classifica_receita():
    texto = "Receita médica: usar Budesonida. Posologia: tomar 1 cápsula ao dia. Uso contínuo."
    resultado = classificar_documento(texto)
    assert resultado["tipo"] == "RECEITA"
    assert resultado["confianca"] >= 0.45


def test_sugestoes_incluem_classificacao():
    sugestoes = sugerir_campos("Espirometria VEF1 CVF fluxo expiratório")
    assert sugestoes["tipo_documento_sugerido"] == "ESPIROMETRIA"
    assert "classificacao_documental" in sugestoes
