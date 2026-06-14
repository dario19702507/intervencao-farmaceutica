# Correção 12A.1 — OCR/PDF

Esta correção impede que PDFs sejam lidos como texto binário bruto. O serviço agora:

1. tenta extrair texto pesquisável via PyMuPDF;
2. tenta extrair via pypdf/PyPDF2;
3. tenta OCR de PDF imagem quando Tesseract estiver disponível;
4. se não houver texto e OCR não estiver instalado, retorna `SEM_TEXTO_EXTRAIDO` com observação, sem preencher campos com lixo binário.

Para OCR de PDF escaneado/imagem no Windows, recomenda-se instalar:

```cmd
pip install pymupdf pillow pytesseract pypdf
```

Além disso, é necessário instalar o Tesseract OCR no Windows e garantir que `tesseract.exe` esteja no PATH.

Após substituir os arquivos:

```cmd
pytest -q tests
python tests\smoke_tests.py
```
