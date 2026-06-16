# 15D.4 — Agenda CEAF integrada à agenda existente

## Objetivo
Expandir a agenda existente para operar com pacientes CEAF sem criar uma agenda paralela.

## Incluído

- Busca de pacientes CEAF no formulário da agenda.
- Carregamento automático de dados CEAF ao selecionar paciente:
  - nome;
  - telefone;
  - medicamento prescrito;
  - situação LME;
  - início do medicamento/vigência;
  - fim da vigência;
  - vínculo com paciente clínico e paciente da agenda, quando existente.
- Geração automática de agenda CEAF a partir da data fim de vigência.
- Reagendamento manual com motivo obrigatório.
- Histórico de alterações da agenda.
- Cancelamento, falta e conclusão mantendo o fluxo de status existente.
- Colunas novas adicionadas de forma idempotente em `agenda_integrada`.
- Nova tabela `agenda_historico`.

## Endpoints novos

- `GET /consultorio/agenda/pacientes-ceaf/buscar`
- `GET /consultorio/agenda/pacientes-ceaf/{paciente_ceaf_id}/contexto`
- `POST /consultorio/agenda/gerar-ceaf`
- `POST /consultorio/agenda/{agenda_id}/reagendar`
- `GET /consultorio/agenda/{agenda_id}/historico`

## Arquivos alterados

- `backend/models/consultorio_models.py`
- `backend/routers/consultorio.py`
- `backend/schemas/consultorio_schemas.py`
- `frontend/src/pages/agenda/AgendaIntegrada.jsx`
- `frontend/src/style.css`

## Validação local realizada

```bash
python -m py_compile backend/routers/consultorio.py backend/models/consultorio_models.py backend/schemas/consultorio_schemas.py
cd frontend
npm install --no-audit --no-fund
npm run build
```

O build frontend foi concluído com sucesso no ambiente de geração do patch.

## Pós-aplicação

Após aplicar, fazer commit e deploy no Render e Vercel.

No Swagger, conferir:

- CEAF aparece na agenda.
- `POST /consultorio/agenda/gerar-ceaf` funciona.
- `POST /consultorio/agenda/{id}/reagendar` funciona.

No frontend, conferir:

- Agenda → Agenda.
- Novo cadastro/evento.
- Buscar paciente CEAF.
- Selecionar paciente e verificar preenchimento automático.
- Reagendar compromisso com motivo.
- Visualizar histórico.
