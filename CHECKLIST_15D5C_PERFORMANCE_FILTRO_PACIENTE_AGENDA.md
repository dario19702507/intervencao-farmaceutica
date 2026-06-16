# 15D.5C — Performance da agenda e filtro por paciente

## Objetivo

Reduzir a lentidão percebida após a importação dos pacientes CEAF e a geração de muitos compromissos de agenda, acrescentando um filtro direto por paciente.

## Arquivos alterados

- `frontend/src/pages/agenda/AgendaIntegrada.jsx`

## Ajustes realizados

- A agenda passa a abrir inicialmente com período de 7 dias, reduzindo a carga inicial.
- Foi adicionado o campo `Localizar paciente` nos filtros da agenda.
- O filtro localiza por:
  - nome do paciente;
  - CPF, quando retornado pelo backend;
  - CNS, quando retornado pelo backend;
  - telefone;
  - medicamento;
  - situação do laudo.
- A lista visível de compromissos foi limitada a 150 registros por vez.
- Quando houver mais de 150 registros filtrados, o sistema exibe orientação para refinar por paciente, status ou período.
- Eventos encerrados continuam ocultos por padrão quando o filtro de status estiver em `Ativos / passíveis de alteração`.

## Validação sugerida

1. Abrir Agenda Integrada.
2. Confirmar que o período inicial é 7 dias.
3. Pesquisar um paciente pelo nome.
4. Pesquisar pelo medicamento.
5. Alterar o período para 30/90 dias.
6. Confirmar que a agenda não trava mesmo com grande volume de eventos.
7. Confirmar que ações como Realizado, Reagendar, Faltou e Cancelar continuam funcionando.

## Observação

Este patch é frontend. Não exige deploy no Render, apenas no Vercel.
