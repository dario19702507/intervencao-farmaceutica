# Passo 14E.6.1A — Painel de Integração das Intervenções

Este pacote implementa a primeira etapa de governança da integração entre o App de Intervenções em produção e o Sistema Farmácia Escola.

## Objetivo

Manter o App de Intervenções funcionando normalmente enquanto o Sistema Farmácia Escola passa a acompanhar, auditar e validar a integração dos dados importados.

## O que foi incluído

### Backend

Novos endpoints administrativos em `/consultorio/migracao-intervencoes`:

- `GET /integracao-resumo`
- `GET /checkpoints`
- `GET /consistencia`
- `GET /rastreabilidade`

Esses endpoints não alteram dados. Eles apenas consolidam informações de staging, checkpoints, consistência e rastreabilidade.

### Frontend

Nova aba **Integração** dentro do workspace **Analytics**, evitando criar mais um item isolado no menu lateral.

A aba possui:

- Resumo
- Sincronização
- Checkpoints
- Consistência
- Rastreabilidade

### Testes

Foram atualizados:

- `tests/test_migracao_intervencoes.py`
- `tests/smoke_tests.py`

## Arquivos alterados/adicionados

- `backend/services/migracao_intervencoes.py`
- `backend/routers/migracao_intervencoes.py`
- `frontend/src/pages/analytics/AnalyticsWorkspace.jsx`
- `frontend/src/pages/analytics/IntegracaoIntervencoes.jsx`
- `frontend/src/pages/analytics/IntegracaoIntervencoes.css`
- `tests/smoke_tests.py`
- `tests/test_migracao_intervencoes.py`

## Como aplicar

Copie os arquivos do pacote para as mesmas pastas no projeto.

Depois rode o backend:

```cmd
cd backend
uvicorn main:app --reload
```

Em outro terminal, na raiz do projeto:

```cmd
pytest -q tests
python tests\smoke_tests.py
```

Para o frontend:

```cmd
cd frontend
npm run dev
```

## Observação

No sandbox, o `npm run build` não pôde ser validado porque o executável local do Vite está sem permissão de execução neste ambiente. Os arquivos alterados são React/CSS e devem ser validados no ambiente Windows do projeto.
