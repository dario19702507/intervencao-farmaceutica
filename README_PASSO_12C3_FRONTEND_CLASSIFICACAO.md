# Passo 12C.3 — Frontend da Classificação Documental

Arquivos incluídos:

- `frontend/src/pages/documentos/OCRDocumental.jsx`
- `frontend/src/pages/documentos/OCRDocumental.css`
- `backend/routers/ocr_documentos.py`

## O que muda

- Exibe tipo documental sugerido após o OCR.
- Exibe confiança da classificação.
- Exibe se a classificação é automática ou manual.
- Permite reclassificação manual pelo operador.
- Mantém a regra: nenhuma informação é aplicada automaticamente ao cadastro, vigência, agenda ou WhatsApp.

## Observação

O arquivo `backend/routers/ocr_documentos.py` foi incluído porque a reclassificação manual precisa ser persistida no backend.
