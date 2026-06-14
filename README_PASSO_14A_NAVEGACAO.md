# Passo 14A — Reorganização da navegação do frontend

Este pacote altera somente o frontend.

## Arquivos alterados

- `frontend/src/components/layout/Sidebar.jsx`
- `frontend/src/components/layout/MainLayout.jsx`
- `frontend/src/components/layout/Topbar.jsx`
- `frontend/src/style.css`

## O que muda

- A barra lateral deixa de ser uma lista única extensa.
- Os itens passam a ser agrupados em seções expansíveis:
  - Início
  - Atendimento
  - Agenda e CEAF
  - Documentos
  - Relatórios e Indicadores
  - Cadastros e Sistema
- O topo da tela passa a mostrar título e subtítulo de acordo com a página ativa.
- As rotas e páginas existentes foram mantidas.
- Não há alteração no backend.

## Como aplicar

Substitua/adicone os arquivos nas pastas correspondentes e rode:

```cmd
cd frontend
npm run dev
```

Se quiser validar build:

```cmd
npm run build
```
