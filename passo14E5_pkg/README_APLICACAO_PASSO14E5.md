# Passo 14E.5 — Workspace Analytics

Este pacote consolida os módulos de inteligência, indicadores e relatórios em uma única área de frontend.

## O que muda

- Cria `frontend/src/pages/analytics/AnalyticsWorkspace.jsx`.
- Cria `frontend/src/pages/analytics/AnalyticsWorkspace.css`.
- Atualiza `frontend/src/navigation/catalog.jsx`.
- Reduz o menu lateral para um único item em Inteligência: **Analytics**.
- Mantém redirects antigos:
  - `/dashboard-epidemiologico`
  - `/indicadores-cientificos`
  - `/relatorios-gerenciais`
  - `/relatorios`
  - `/inteligencia/epidemiologia`
  - `/inteligencia/ciencia`
  - `/inteligencia/relatorios`

## Abas internas

- Visão Executiva
- Assistencial e Epidemiológico
- Científico
- Relatórios

## Backend

Não há alteração no backend.

## Como aplicar

Copie os arquivos deste pacote para a raiz do projeto, sobrescrevendo quando solicitado.

Depois execute:

```cmd
cd frontend
npm run dev
```

Se desejar validar build:

```cmd
npm run build
```

## Observação

Este passo consolida a navegação. Ele não remove os componentes antigos, apenas os passa a consumir dentro do workspace único de Analytics.
