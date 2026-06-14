# Passo 12B — Frontend do OCR Documental

Este pacote adiciona a tela **OCR Documental** ao frontend.

## O que foi incluído

- Seleção de paciente.
- Seleção de pacote/processo documental.
- Listagem dos documentos vinculados ao pacote.
- Extração individual por documento.
- Extração em lote de todos os documentos do pacote.
- Visualização das extrações já realizadas.
- Visualização do texto extraído.
- Visualização dos campos sugeridos.
- Aviso de segurança: os dados extraídos não atualizam automaticamente paciente, processo, vigência, agenda, notificações ou WhatsApp.

## Arquivos alterados/adicionados

- `frontend/src/pages/documentos/OCRDocumental.jsx`
- `frontend/src/pages/documentos/OCRDocumental.css`
- `frontend/src/App.jsx`
- `frontend/src/components/layout/Sidebar.jsx`

## Como aplicar

Substitua/adicone somente os arquivos do frontend.

Depois execute:

```cmd
cd frontend
npm run dev
```

## Backend necessário

Este frontend usa rotas do Passo 12A:

- `GET /consultorio/documentos/ocr/opcoes`
- `POST /consultorio/documentos/{documento_id}/ocr/extrair`
- `GET /consultorio/documentos/{documento_id}/ocr`
- `GET /consultorio/processos-documentais/{processo_id}/ocr`

