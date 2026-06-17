# CHECKLIST 15D.8A — Agenda única para retiradas CEAF

## Objetivo
Corrigir a geração automática de retiradas para que pacientes CEAF sejam tratados pela mesma agenda de dispensação dos demais pacientes.

## Ajustes realizados

### Backend — `backend/routers/consultorio.py`
- A conciliação CEAF agora cria eventos comuns da agenda:
  - `servico_origem = "dispensacao"`
  - `tipo_evento = "retirada_medicamento"`
  - `status = "retirada_prevista"`
- A atualização de status passou a acionar a próxima retirada automática quando o evento realizado for uma retirada, independentemente de origem visual CEAF/dispensação.
- A lógica preserva os vínculos:
  - `paciente_id`
  - `paciente_ceaf_id`
  - `paciente_clinico_id`

### Backend — `backend/services/agenda_notificacoes.py`
- A criação automática da próxima retirada agora aceita tipos padronizados:
  - `retirada`
  - `retirada_medicamento`
  - `retirada_prevista`
  - `dispensacao`
- A próxima retirada gerada usa:
  - `servico_origem = "dispensacao"`
  - `tipo_evento = "retirada_medicamento"`
  - `status = "retirada_prevista"`
- A verificação de duplicidade considera:
  - `paciente_id`
  - `paciente_ceaf_id`
  - `paciente_clinico_id`
- Os alertas de risco de interrupção preservam os vínculos CEAF/clínico.

## Como aplicar

```bash
git add backend/routers/consultorio.py backend/services/agenda_notificacoes.py CHECKLIST_15D8A_AGENDA_UNICA_RETIRADAS_CEAF.md
git commit -m "Unifica retiradas CEAF na agenda 15D8A"
git push origin main
```

Depois fazer deploy no Render.

## Validação sugerida

1. Swagger: executar `POST /consultorio/agenda/conciliacao-ceaf/sincronizar`.
2. Consultar `GET /consultorio/agenda`.
3. Verificar eventos com:
   - `servico_origem = dispensacao`
   - `tipo_evento = retirada_medicamento`
   - `status = retirada_prevista`
   - `paciente_ceaf_id` preenchido quando aplicável.
4. No frontend: Agenda → Agenda → filtro Dispensação + status Retirada prevista.
5. Marcar uma retirada CEAF como `realizado` e verificar se o sistema cria próxima retirada prevista.

## Observação
Este patch não altera frontend. A correção é de regra de negócio no backend.
