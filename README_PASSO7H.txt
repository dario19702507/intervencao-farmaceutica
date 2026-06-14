PASSO 7H — Router de Indicadores Científicos

Substituir somente os arquivos do backend contidos neste pacote.

Arquivos:
- backend/main.py
- backend/routers/consultorio.py
- backend/routers/indicadores_cientificos.py

Rotas movidas para routers/indicadores_cientificos.py:
- GET /consultorio/dashboard-epidemiologico
- GET /consultorio/dashboard-antropometrico
- GET /consultorio/dashboard-cardiovascular
- GET /consultorio/dashboard-glicemico
- GET /consultorio/dashboard-efetividade-cuidado
- GET /consultorio/indicadores-cientificos
- GET /consultorio/serie-temporal-cientifica
- GET /consultorio/exportacao-cientifica-excel
- GET /consultorio/exportacao-pesquisa-anonimizada
- GET /consultorio/relatorio-cientifico-pdf

O main.py já inclui:
from routers.indicadores_cientificos import router as indicadores_cientificos_router
app.include_router(indicadores_cientificos_router)
