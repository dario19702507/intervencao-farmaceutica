# Passo 14E.2C.2B.1 — Separação entre Integração e Intervenções Padronizadas

Este pacote corrige a regressão de usabilidade observada após a inclusão dos indicadores de intervenções padronizadas no Dashboard Epidemiológico.

## Objetivo

Separar claramente dois fluxos diferentes:

- **Intervenções Padronizadas**: análise clínica e indicadores assistenciais, dentro do Dashboard Epidemiológico.
- **Integração das Intervenções**: governança da migração, staging, checkpoints, consistência e rastreabilidade dos dados importados do App de Intervenções.

## Arquivos alterados/adicionados

```txt
frontend/src/pages/analytics/AnalyticsWorkspace.jsx
frontend/src/pages/analytics/IntegracaoIntervencoes.jsx
frontend/src/pages/analytics/IntegracaoIntervencoes.css
```

## Resultado esperado

No Analytics, aparecerá novamente a aba:

```txt
Integração das Intervenções
```

Com subtelas internas:

```txt
Resumo
Sincronização
Checkpoints
Consistência
Rastreabilidade
```

## Backend

Não há alteração de backend. O painel usa endpoints já existentes e validados:

```txt
GET /consultorio/migracao-intervencoes/integracao-resumo
GET /consultorio/migracao-intervencoes/dashboard
GET /consultorio/migracao-intervencoes/checkpoints
GET /consultorio/migracao-intervencoes/consistencia
GET /consultorio/migracao-intervencoes/rastreabilidade
```

## Validação

Após aplicar, rode:

```cmd
cd frontend
npm run dev
```

Opcionalmente, mantenha a validação geral:

```cmd
pytest -q tests
python tests\smoke_tests.py
```

