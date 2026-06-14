# Passo 11G — Frontend dos Processos/Pacotes Documentais

Este pacote adiciona a tela de **Pacotes Documentais**, permitindo criar e acompanhar processos documentais do paciente e anexar múltiplos arquivos à mesma ação operacional.

## Inclui

- Tela `ProcessosDocumentais.jsx`.
- CSS próprio `ProcessosDocumentais.css`.
- Novo item no menu lateral: **Pacotes Documentais**.
- Rota no `App.jsx`.
- Upload múltiplo: vários arquivos enviados sequencialmente ao mesmo processo documental.
- Classificação individual de cada arquivo: LAUDO, RECEITA, EXAME, DOCUMENTO_PESSOAL, TERMO ou OUTRO.
- Registro de pendência documental com notificação interna.
- Regra preservada: pendência documental **não gera WhatsApp automático**; envio ao paciente deve ser manual.

## Arquivo backend incluído

O arquivo `backend/routers/processos_documentais.py` foi incluído apenas para preservar a correção de ordem das rotas fixas:

- `/consultorio/processos-documentais/opcoes`
- `/consultorio/processos-documentais/dashboard`

antes de:

- `/consultorio/processos-documentais/{processo_id}`

Isso evita erro 422 quando o FastAPI interpreta `dashboard` como ID.

## Como aplicar

Substitua/adicone os arquivos do frontend e, se necessário, substitua também o router backend incluído.

Depois rode:

```cmd
cd frontend
npm run dev
```

E no backend:

```cmd
pytest -q tests
python tests\smoke_tests.py
```
