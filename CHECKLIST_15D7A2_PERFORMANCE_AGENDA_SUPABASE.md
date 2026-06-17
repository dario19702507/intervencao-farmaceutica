# 15D.7A.2 — Otimização crítica de performance Agenda/CEAF

## Objetivo
Reduzir a lentidão observada após a importação de pacientes CEAF, geração de agenda e integração dos alertas/notificações.

## Ajustes backend
- `GET /consultorio/agenda` agora aceita `limit`, `offset`, `paciente` e `somente_ativos`.
- A listagem da agenda aplica limite seguro por padrão.
- Eventos encerrados ficam fora da carga inicial quando `somente_ativos=true`.
- A busca por paciente pode ser feita diretamente no backend.
- A conciliação CEAF deixou de fazer uma consulta por paciente para verificar retirada mensal.
- Alertas CEAF passam a usar mapa mensal de retiradas pré-carregado.
- A central de notificações usa `count()` para cartões e limita listas retornadas.

## Ajustes frontend
- A agenda integrada passa a carregar no máximo 150 eventos por vez.
- A busca por paciente é enviada ao backend quando houver 3 ou mais caracteres.
- O carregamento é debounced para evitar chamadas a cada tecla sem intervalo.
- A central de notificações é carregada inicialmente apenas como resumo, sem listas pesadas.

## Validação local
- `python -m py_compile backend/routers/consultorio.py` executado com sucesso.
- `npm run build` não foi concluído neste ambiente por permissão local do binário Vite (`vite: Permission denied`). Rodar no Windows/Vercel após aplicar.

## Testes recomendados
1. Abrir Agenda → Visão Geral: esperado < 10 segundos.
2. Abrir Agenda → Agenda: esperado < 10 segundos.
3. Abrir Agenda → Conciliação CEAF: esperado < 10 segundos.
4. Filtrar paciente por nome/CPF/CNS: esperado retornar lista sem travar a tela.
5. Selecionar Status = Todos apenas quando necessário.
6. Evitar usar período Todos sem filtro por paciente durante homologação.

## Deploy necessário
- Render: sim.
- Vercel: sim.
