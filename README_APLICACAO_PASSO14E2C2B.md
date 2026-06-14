# Passo 14E.2C.2B — Visualização das Intervenções Padronizadas no Dashboard Epidemiológico

Este pacote adiciona a visualização dos indicadores de intervenções padronizadas no frontend, mantendo o backend intacto.

## Onde ficará

Analytics → Assistencial e Epidemiológico → Dashboard Epidemiológico → Intervenções

## Arquivos alterados/adicionados

- `frontend/src/pages/dashboard/DashboardEpidemiologico.jsx`
- `frontend/src/pages/analytics/IntervencoesPadronizadasIndicadores.jsx`

## Endpoint consumido

- `GET /consultorio/intervencoes-padronizadas/dashboard`

## Indicadores exibidos

- Ocorrências legadas
- Textos distintos
- Textos mapeados
- Textos não mapeados
- Taxa de mapeamento
- Intervenções por tipo padronizado
- Intervenções por grupo
- Textos legados pendentes de revisão

## Aplicação

Extraia o pacote na raiz do projeto, substituindo os arquivos indicados.

Depois rode:

```cmd
cd frontend
npm run dev
```

Não há alteração de backend nem necessidade de rodar migração.
