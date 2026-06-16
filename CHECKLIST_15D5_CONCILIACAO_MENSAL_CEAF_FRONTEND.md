# 15D.5 — Conciliação Mensal CEAF no frontend

## Objetivo

Adicionar a aba **Conciliação CEAF** dentro de **Agenda**, consumindo os endpoints do backend 15D.5.

## Arquivos alterados

- `frontend/src/pages/agenda/AgendaWorkspace.jsx`
- `frontend/src/pages/agenda/ConciliacaoCeaf.jsx`
- `frontend/src/style.css`

## Funcionalidades adicionadas

- Nova aba **Conciliação CEAF** no workspace de Agenda.
- Seleção de mês e ano de conciliação.
- Consulta do resumo operacional da conciliação.
- Botão **Sincronizar retiradas CEAF**.
- Opção para criar pendência de renovação quando LME estiver vencida.
- Exibição de indicadores:
  - pacientes CEAF ativos;
  - retiradas previstas;
  - retiradas agendadas;
  - retiradas realizadas;
  - LME vencidas;
  - LME vencendo em 30 dias;
  - bloqueios por LME;
  - pacientes sem retirada prevista.
- Exibição do resultado da última sincronização.
- Lista de exemplos criados e bloqueados.

## Endpoints utilizados

- `GET /consultorio/agenda/conciliacao-ceaf/resumo`
- `POST /consultorio/agenda/conciliacao-ceaf/sincronizar`

## Validação sugerida

1. Fazer deploy do backend 15D.5 no Render.
2. Aplicar este patch frontend.
3. Rodar:

```bash
cd frontend
npm run build
```

4. Fazer redeploy no Vercel.
5. Acessar:

```text
Agenda → Conciliação CEAF
```

6. Validar resumo e executar uma sincronização controlada.

## Observação operacional

A sincronização não apaga agendamentos e não deve duplicar retiradas já agendadas ou realizadas no mês. Ela cria apenas retiradas previstas e pendências quando aplicável.
