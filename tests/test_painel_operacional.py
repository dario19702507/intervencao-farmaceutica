def test_painel_operacional(get):
    r = get('/consultorio/painel-operacional')
    data = r.json()
    assert 'resumo' in data
    assert 'listas' in data
    assert 'retiradas_hoje' in data['resumo']
    assert 'processos_incompletos' in data['resumo']
    assert 'documentos_rejeitados' in data['resumo']
    assert data['regras']['whatsapp_documental']
