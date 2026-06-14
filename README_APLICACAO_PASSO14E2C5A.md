# Passo 14E.2C.5A — Ajustes de Usabilidade Clínica do Consultório

Este pacote não altera backend, banco de dados ou endpoints.

## Objetivo

Reduzir ambiguidade entre intervenção, meta, ação do plano e plano narrativo.

## Alterações

- Aba **6. Metas** renomeada para **6. Metas e ações**.
- Aba **7. Plano** renomeada para **7. Plano narrativo**.
- Inclusão de orientação clínica na aba Metas e ações:
  - PRM = problema identificado;
  - Intervenção = conduta clínica;
  - Meta = resultado esperado;
  - Ação = tarefa com responsável, prazo e status.
- Ajuste da descrição do plano narrativo para evitar dupla digitação.

## Aplicação

Copie o arquivo:

```txt
frontend/src/pages/consultorio/Consultorio.jsx
```

Depois rode:

```cmd
cd frontend
npm run dev
```

## Validação esperada

- Consultório abre normalmente.
- Aba 6 exibe Metas e ações.
- Aba 7 exibe Plano narrativo.
- Formulários de metas e ações continuam funcionando.
