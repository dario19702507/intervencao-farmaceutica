# Passo 12A — OCR Base

Este pacote adiciona a primeira camada de OCR/extração documental.

## Objetivo

Extrair texto de documentos já enviados e gerar campos sugeridos para conferência humana, sem alterar automaticamente cadastro, vigência, agenda, notificações ou WhatsApp.

## Rotas novas

- `GET /consultorio/documentos/ocr/opcoes`
- `POST /consultorio/documentos/{documento_id}/ocr/extrair`
- `GET /consultorio/documentos/{documento_id}/ocr`
- `GET /consultorio/processos-documentais/{processo_id}/ocr`

## Regras de segurança

- Extrações são apenas sugestões.
- Nenhum dado do paciente é alterado automaticamente.
- Nenhuma vigência é recalculada automaticamente pelo OCR.
- O operador deve conferir antes de usar qualquer informação extraída.

## Dependência opcional recomendada

Para extração de texto em PDF pesquisável:

```cmd
pip install PyMuPDF
```

Para OCR real de imagens, etapa futura:

```cmd
pip install pytesseract
```

Além disso, o executável Tesseract precisa ser instalado no Windows.

## Testes

```cmd
pytest -q tests
python tests\smoke_tests.py
```
