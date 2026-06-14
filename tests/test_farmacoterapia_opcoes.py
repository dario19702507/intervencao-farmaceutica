
def test_opcoes_farmacoterapia(get):
    r = get("/consultorio/farmacoterapia/opcoes")
    data = r.json()
    assert "oral" in data["vias_administracao"]
    assert "inalatória" in data["vias_administracao"]
    assert "08:00" in data["horarios_padrao"]
    assert "se necessário" in data["horarios_padrao"]
    assert "1x ao dia" in data["frequencias_uso"]
