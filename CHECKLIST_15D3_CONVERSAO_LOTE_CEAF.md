# 15D.3 — Conversão em lote CEAF → Paciente Clínico

## Objetivo

Permitir converter registros importados do CEAF para o cadastro clínico e para o cadastro mestre de agenda/notificações, preservando a base original `pacientes_ceaf`.

## Arquivos alterados

- `backend/models/consultorio_models.py`
- `backend/routers/ceaf.py`
- `frontend/src/pages/pacientes/PacientesCeaf.jsx`
- `frontend/src/style.css`

## Endpoints adicionados

- `GET /ceaf/pacientes/conversao/resumo`
- `POST /ceaf/pacientes/{paciente_id}/converter-clinico`
- `POST /ceaf/pacientes/converter-lote`

## Regras de segurança

A conversão em lote procura duplicidades por CPF e CNS antes de criar um novo cadastro. Registros sem CPF e CNS são ignorados automaticamente para evitar duplicidade. A tabela CEAF original é preservada e recebe apenas os vínculos com `paciente_clinico_id` e `paciente_agenda_id`.

## Resultado esperado

Após o deploy, a tela **Atendimento → Pacientes CEAF** deve exibir resumo de conversão, botão de conversão em lote para os pacientes filtrados/pendentes e botão de conversão individual em cada registro.
