# Passo 6I — Alertas clínicos e pendências

## Alterações realizadas

- Criado `backend/services/alertas_clinicos.py`.
- Movida a lógica de alertas pendentes, alertas clínicos consolidados, resolução de alertas e dashboards relacionados.
- Mantidos os endpoints originais em `routers/consultorio.py`, agora como wrappers.
- Também movidas as funções de série temporal e classificação de risco populacional por estarem diretamente acopladas à resolutividade dos alertas.

## Endpoints preservados

- `GET /consultorio/alertas-pendentes`
- `GET /consultorio/alertas-clinicos-consolidados`
- `POST /consultorio/alertas-clinicos/resolver`
- `GET /consultorio/alertas-clinicos/resolucoes`
- `GET /consultorio/dashboard-resolucao-alertas`
- `GET /consultorio/relatorio-resolucao-alertas-pdf`
- `GET /consultorio/dashboard-serie-temporal`
- `GET /consultorio/classificacao-risco-populacional`
