from services.intervencoes_padronizadas import (
    CATALOGO_INTERVENCOES,
    VERSAO_CATALOGO_INTERVENCOES,
    mapear_intervencao_legada,
)


def test_catalogo_intervencoes_tem_itens_essenciais():
    codigos = {item["codigo"] for item in CATALOGO_INTERVENCOES}
    assert VERSAO_CATALOGO_INTERVENCOES
    assert "EDUCACAO_EM_SAUDE" in codigos
    assert "ORIENTACAO_FARMACEUTICA" in codigos
    assert "CONTATO_PRESCRITOR" in codigos
    assert "AJUSTE_TERAPEUTICO_SUGERIDO" in codigos
    assert "ORIENTACAO_DOCUMENTAL" in codigos


def test_mapeamento_legado_intervencoes_basico():
    assert mapear_intervencao_legada("Educação em Saúde")["codigo_sugerido"] == "EDUCACAO_EM_SAUDE"
    assert mapear_intervencao_legada("Erro de prescrição")["codigo_sugerido"] == "CONTATO_PRESCRITOR"
    assert mapear_intervencao_legada("Técnica de uso")["codigo_sugerido"] == "ORIENTACAO_FARMACEUTICA"
    assert mapear_intervencao_legada("Orientação documental")["codigo_sugerido"] == "ORIENTACAO_DOCUMENTAL"
