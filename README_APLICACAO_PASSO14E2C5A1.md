# Passo 14E.2C.5A.1 — Correção de regressão de usabilidade clínica

Este pacote corrige a regressão observada após o ajuste 14E.2C.5A.

## O que corrige

- Restaura a visibilidade dos botões clínicos de inclusão/edição quando o usuário autenticado possui perfil/categoria com variações como `ADMIN`, `Farmacêutico`, `farmaceutico`, `Docente`, `Preceptor`, `Residente` ou `Estagiário`.
- Mantém bloqueio apenas para perfis explicitamente de leitura/visualização.
- Preserva os formulários existentes de medicamentos, PRM/intervenções, metas, ações do plano e evoluções.
- Acrescenta, no Plano narrativo, um resumo navegável das etapas anteriores: PRM/intervenções, metas, ações e evoluções.

## Arquivo alterado

- `frontend/src/pages/consultorio/Consultorio.jsx`

## Como aplicar

Substitua o arquivo correspondente no projeto e rode:

```cmd
cd frontend
npm run dev
```

Não há alteração no backend, banco ou endpoints.
