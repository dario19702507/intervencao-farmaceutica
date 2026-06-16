# 15D.2D — Ajuste de altura e rolagem do menu lateral

## Objetivo
Garantir que a sidebar permaneça fechada por padrão, mas tenha área útil e rolagem interna suficientes para exibir todos os itens ao abrir uma seção, especialmente **Atendimento → Pacientes CEAF**.

## Arquivo alterado
- `frontend/src/style.css`

## Ajustes aplicados
- Sidebar com `height: 100vh` e layout em coluna.
- Cabeçalho da sidebar fixo no topo da barra lateral.
- Navegação agrupada com rolagem interna própria.
- Redução leve de espaçamentos verticais nos itens do menu.
- Correção de visibilidade do último item em seções longas.
- Ajuste responsivo para mobile/tablet.

## Como validar
1. Entrar pelo link inicial do Vercel.
2. Confirmar que a sidebar inicia com seções fechadas.
3. Abrir a seção **Atendimento**.
4. Confirmar que **Pacientes CEAF** aparece sem ficar cortado.
5. Testar rolagem da sidebar quando houver muitos itens.
6. Confirmar que a área principal do sistema não é afetada.
