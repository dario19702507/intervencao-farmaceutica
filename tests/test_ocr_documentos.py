
def test_opcoes_ocr_documental(get):
    r = get('/consultorio/documentos/ocr/opcoes')
    data = r.json()
    assert data['atualizacao_automatica_cadastro'] is False
    assert 'PDF_TEXTO' in data['metodos']


def test_ocr_documento_inexistente_retorna_404(get):
    get('/consultorio/documentos/999999/ocr', expected_status=200)
