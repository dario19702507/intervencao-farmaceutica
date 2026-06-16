# 15D.5A — Ajustes de contadores, filtros e alertas CEAF

## Objetivo
Corrigir inconsistências observadas na Agenda Integrada após a implantação da conciliação mensal CEAF.

## Ajustes realizados

1. **Contadores da Agenda Integrada**
   - Os cartões "Hoje", "Próximos 7 dias" e "Pendentes" passam a considerar apenas eventos operacionais confirmados.
   - Retiradas previstas foram separadas em cartão próprio, evitando inflar indevidamente os compromissos do dia.
   - Eventos encerrados, como cancelados, realizados, concluídos e reagendados, não entram nos indicadores ativos.

2. **Central de alertas**
   - A central passa a considerar dados CEAF diretamente.
   - LME vencida entra como risco de interrupção.
   - LME vencendo em 15 dias entra como renovação urgente.
   - LME vencendo entre 16 e 30 dias entra como renovação recomendada.
   - Dispensações/retiradas de amanhã agora são calculadas por tipo de evento, e não apenas pela origem "dispensação".

3. **Filtros da Agenda Integrada**
   - Removido o filtro específico "CEAF" da lista visual.
   - Dispensação passa a ser interpretada pelo tipo de evento de retirada, independentemente da origem.
   - Renovação de laudo passa a ser interpretada pelo tipo de evento de renovação, independentemente da origem.

4. **Conciliação mensal CEAF**
   - A verificação de retirada já existente passa a olhar a agenda de forma transversal, sem depender exclusivamente da origem CEAF.
   - Retiradas cadastradas como dispensação, mas vinculadas ao paciente CEAF, passam a ser consideradas na conciliação.
   - Mantida a regra de não duplicar retiradas no mesmo mês.

## Arquivos alterados

- backend/routers/consultorio.py
- frontend/src/pages/agenda/AgendaIntegrada.jsx
- frontend/src/style.css

## Validação sugerida

Backend:

```bash
cd backend
python -m py_compile routers/consultorio.py
```

Frontend:

```bash
cd frontend
npm run build
```

Deploy:

- Render: necessário, pois houve alteração no backend.
- Vercel: necessário, pois houve alteração no frontend.
