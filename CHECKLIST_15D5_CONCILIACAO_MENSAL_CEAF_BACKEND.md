# 15D.5 — Conciliação Mensal CEAF (backend)

## Objetivo

Implementar o motor backend de conciliação mensal de retiradas CEAF usando a agenda integrada existente, sem criar uma agenda paralela.

## Endpoints adicionados

- `GET /consultorio/agenda/conciliacao-ceaf/resumo`
- `POST /consultorio/agenda/conciliacao-ceaf/sincronizar`

## Regras implementadas

- Paciente CEAF ativo + LME vigente + sem retirada no mês: cria evento `RETIRADA_MEDICAMENTO` com status `retirada_prevista`.
- Paciente com LME vencida ou sem vigência suficiente: não cria retirada.
- Se `criar_pendencia_renovacao=true`, cria pendência `RENOVACAO_LME` quando necessário.
- Não duplica retirada se já houver retirada prevista, agendada, reagendada, notificada, realizada ou concluída no mês.
- Usa a agenda integrada existente (`agenda_integrada`).
- Registra histórico em `agenda_historico` para eventos criados pela conciliação.

## Parâmetros

### Resumo

```http
GET /consultorio/agenda/conciliacao-ceaf/resumo?ano=2026&mes=6
```

### Sincronização

```http
POST /consultorio/agenda/conciliacao-ceaf/sincronizar?ano=2026&mes=6&criar_pendencia_renovacao=true
```

## Validação sugerida

1. Rodar `python -m py_compile backend/routers/consultorio.py`.
2. Fazer deploy no Render.
3. Testar no Swagger o endpoint de resumo.
4. Executar a sincronização em homologação.
5. Conferir se foram criados eventos `retirada_prevista` na agenda.
6. Confirmar que pacientes com LME vencida foram bloqueados para retirada.
7. Confirmar que não houve duplicidade de retirada no mesmo mês.

## Observação operacional

A conciliação cria retiradas como **previstas**, não como realizadas. A equipe deve confirmar, reagendar, concluir ou cancelar conforme o fluxo real da Farmácia Escola.
