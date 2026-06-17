# 15D.6 — Alertas CEAF no frontend

## Arquivos alterados

- `frontend/src/pages/agenda/AgendaAlertas.jsx`
- `frontend/src/pages/notificacoes/NotificacoesWhatsapp.jsx`
- `frontend/src/style.css`

## Objetivo

Integrar os alertas CEAF às áreas já existentes da Agenda, sem criar novo menu:

- Aba **Visão Geral**: alertas pendentes priorizados.
- Aba **Notificações**: preparação operacional para contato/WhatsApp.

## Validação sugerida

1. Acessar `Agenda → Visão Geral`.
2. Confirmar cards CEAF críticos/urgentes/renovações.
3. Confirmar lista de alertas ordenada por prioridade.
4. Acessar `Agenda → Notificações`.
5. Clicar em `Atualizar notificações CEAF`.
6. Confirmar lista com paciente, telefone, medicamento, motivo e mensagem sugerida.

## Observação

Esta etapa não dispara WhatsApp automaticamente. Ela apenas prepara a fila lógica para o passo 15D.6A.
