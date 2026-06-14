# Passo 14E.3 — Workspace de Documentos

Este pacote consolida a navegação documental do frontend em uma única área de trabalho.

## O que muda

Antes, o menu expunha separadamente:

- Gestão Documental;
- Processos Documentais;
- OCR Documental.

Agora o menu mantém apenas:

- Documentos.

Dentro da tela Documentos há abas internas:

- Visão Geral;
- Pacotes;
- Documentos;
- OCR;
- Vigências;
- Pendências.

## O que não muda

O backend não foi alterado. Os endpoints existentes continuam sendo utilizados.

As telas antigas foram preservadas e incorporadas como subáreas do workspace, reduzindo risco de regressão:

- `DocumentosPaciente.jsx`;
- `ProcessosDocumentais.jsx`;
- `OCRDocumental.jsx`.

## Arquivos alterados/adicionados

- `frontend/src/navigation/catalog.jsx`
- `frontend/src/pages/documentos/DocumentosWorkspace.jsx`
- `frontend/src/pages/documentos/DocumentosWorkspace.css`

## Validação recomendada

```cmd
cd frontend
npm run dev
```

Depois acesse:

- `/documentos`
- `/documentos/gestao` — deve redirecionar para `/documentos`
- `/documentos/processos` — deve redirecionar para `/documentos`
- `/documentos/ocr` — deve redirecionar para `/documentos`
- `/processos-documentais` — deve redirecionar para `/documentos`
- `/ocr-documental` — deve redirecionar para `/documentos`

No backend, como não houve mudança, os testes podem ser executados apenas para segurança:

```cmd
pytest -q tests
python tests\smoke_tests.py
```
