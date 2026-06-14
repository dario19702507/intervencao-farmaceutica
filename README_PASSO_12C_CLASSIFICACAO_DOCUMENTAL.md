# Passo 12C.1 + 12C.2 — Classificação Documental Automática

Este pacote acrescenta a classificação automática do documento a partir do texto extraído pelo OCR.

## O que muda

- O serviço `services/ocr_documentos.py` passa a classificar documentos como:
  - `LAUDO`
  - `RECEITA`
  - `ESPIROMETRIA`
  - `EXAME_LABORATORIAL`
  - `DOCUMENTO_PESSOAL`
  - `TERMO_ESCLARECIMENTO`
  - `OUTROS`
- A classificação é salva dentro dos `campos_sugeridos` da extração OCR.
- O retorno da extração passa a trazer:
  - `classificacao_documental`
  - `tipo_documento_sugerido`
  - `confianca_classificacao`
- Nada é atualizado automaticamente no cadastro, processo, vigência, agenda, notificação ou WhatsApp.

## Testes

```cmd
pytest -q tests
python tests\smoke_tests.py
```
