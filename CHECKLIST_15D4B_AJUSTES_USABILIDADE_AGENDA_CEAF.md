# 15D.4B — Ajustes de usabilidade da Agenda CEAF

## Objetivo
Ajustar a experiência de criação e visualização de agendamentos CEAF antes da fase de notificações.

## Ajustes implementados

1. Removido o bloco visual “Resumo CEAF do paciente selecionado”, reduzindo poluição da tela.
2. Ao selecionar paciente CEAF, os dados disponíveis continuam preenchendo os campos do formulário.
3. Tipo de evento inicia como “Retirada de medicamento”.
4. Campo “Data prevista” permanece limpo após seleção do paciente CEAF.
5. Para retirada de medicamento com LME vencida, o campo “Data prevista” fica bloqueado.
6. Ao tentar salvar retirada com LME vencida, o sistema exibe alerta e impede o agendamento.
7. A lista principal de compromissos passa a mostrar, por padrão, apenas compromissos ativos/passíveis de alteração.
8. Compromissos cancelados, reagendados e realizados ficam ocultos por padrão, mas continuam acessíveis pelo filtro de status.

## Arquivo alterado

- frontend/src/pages/agenda/AgendaIntegrada.jsx

## Validação recomendada

1. Abrir Agenda Integrada.
2. Criar novo evento.
3. Buscar paciente CEAF por nome, CPF ou CNS.
4. Selecionar paciente CEAF.
5. Confirmar que os campos são preenchidos, sem exibir bloco de resumo.
6. Confirmar que “Tipo de evento” vem como “Retirada de medicamento”.
7. Confirmar que “Data prevista” vem vazia.
8. Para paciente com LME vencida, confirmar que “Data prevista” fica bloqueada.
9. Verificar se cancelados/reagendados/realizados não aparecem na lista principal.
10. Usar filtro de status para visualizar cancelados, reagendados ou realizados.
