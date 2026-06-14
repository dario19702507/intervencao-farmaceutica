# Passo 14E.2C.1B.2 — PRM dentro do Dashboard Epidemiológico

Este pacote move a visualização dos Indicadores de PRM para dentro do Dashboard Epidemiológico, na área:

Analytics → Assistencial e Epidemiológico → Dashboard Epidemiológico → PRM

## O que muda

- Remove a subaba isolada “Indicadores de PRM” do Analytics.
- Mantém a aba principal “Assistencial e Epidemiológico”.
- Adiciona a aba interna “PRM” ao Dashboard Epidemiológico, ao lado de:
  - Visão geral
  - Serviços rápidos
  - Risco longitudinal
  - Farmacoterapia
  - Efetividade do cuidado
  - Indicadores científicos
- Mantém o mesmo endpoint:
  - GET /consultorio/cuidado/prm-indicadores
- Não altera backend.

## Arquivos alterados

- frontend/src/pages/dashboard/DashboardEpidemiologico.jsx
- frontend/src/pages/analytics/AnalyticsWorkspace.jsx
- frontend/src/pages/analytics/PrmIndicadores.jsx
- frontend/src/pages/analytics/AnalyticsWorkspace.css

## Validação

Depois de aplicar:

```cmd
cd frontend
npm run dev
```

Acesse:

Analytics → Assistencial e Epidemiológico → PRM
