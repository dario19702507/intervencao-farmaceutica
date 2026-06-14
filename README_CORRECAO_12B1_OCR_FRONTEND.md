# Correção 12B.1 — OCR Documental

Ajuste aplicado no frontend da tela OCR Documental.

## Correções

- O detalhe do processo agora considera a resposta correta do backend: `{ processo: {...} }`.
- A tela passa a carregar os documentos do pacote também por `GET /consultorio/processos-documentais/{id}/documentos`.
- Os botões de extração individual aparecem quando há documentos vinculados ao pacote.
- O botão "Extrair todos do pacote" fica habilitado quando há documentos carregados.
- As extrações e campos sugeridos continuam exibidos após a execução.

## Substituição

Substituir/adicionar somente no frontend:

- `frontend/src/pages/documentos/OCRDocumental.jsx`
- `frontend/src/pages/documentos/OCRDocumental.css`

Depois executar:

```cmd
cd frontend
npm run dev
```
