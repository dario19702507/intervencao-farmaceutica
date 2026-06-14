from services.extratores.lme_extractor import extrair_campos_lme


def test_extrator_lme_modelo_ceaf_basico():
    texto = """
Sistema Único de Saúde
Ministério da Saúde
Secretaria de Estado da Saúde
ADILSON MOACIR DOLENKEI
GERDA SAATKAMP DOLENKEI
LAUDO DE SOLICITAÇÃO, AVALIAÇÃO E AUTORIZAÇÃO DE MEDICAMENTO( S )
RILUZOL 50 MG COMP
9- CID-10 * 10- Diagnóstico
G122 DOENC DO NEURONIO MOTOR
21- Número do documento do paciente
CPF ou CNS
706.8042.3116.2227
24- Município de residência
Campo Grande
"""
    resultado = extrair_campos_lme(texto)
    campos = resultado["campos"]

    assert resultado["tipo_extrator"] == "LME_CEAF"
    assert campos["nome_paciente"] == "ADILSON MOACIR DOLENKEI"
    assert campos["nome_mae"] == "GERDA SAATKAMP DOLENKEI"
    assert campos["cid"] == "G122"
    assert "NEURONIO MOTOR" in campos["diagnostico"]
    assert campos["medicamento"] == "RILUZOL 50 MG COMP"
    assert campos["cns_paciente"] == "706.8042.3116.2227"
    assert campos["municipio"].lower() == "campo grande"
    assert resultado["confianca"] >= 0.75
