# 15D.2B — Correção do menu desktop para Pacientes CEAF

## Objetivo
Garantir que a tela **Pacientes CEAF** fique visível também no acesso inicial pelo desktop/notebook, sem depender do usuário perceber que a seção Atendimento estava recolhida.

## Arquivos alterados
- `frontend/src/components/layout/Sidebar.jsx`
- `frontend/src/style.css`

## Ajustes realizados
- As seções do menu lateral passam a iniciar abertas.
- O usuário ainda pode recolher manualmente qualquer seção.
- A sidebar permanece rolável, evitando perda de itens em telas menores.
- O item `Pacientes CEAF` continua registrado em `catalog.jsx` e disponível em `/atendimento/pacientes-ceaf`.

## Validação recomendada
1. Fazer deploy no Vercel.
2. Abrir a URL inicial no desktop/notebook.
3. Confirmar que a seção Atendimento aparece expandida.
4. Confirmar que o item **Pacientes CEAF** aparece no menu.
5. Abrir diretamente `/atendimento/pacientes-ceaf` e confirmar carregamento.
