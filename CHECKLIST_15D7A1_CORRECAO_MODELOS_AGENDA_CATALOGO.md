# CHECKLIST 15D.7A.1 — Correção de compatibilidade entre catálogo e agenda

## Objetivo
Corrigir falha de deploy causada pela ausência do modelo `AgendaHistorico` após aplicação do patch 15D.7A.

## Arquivo alterado
- backend/models/consultorio_models.py

## Correções realizadas
- Restaurado o modelo `AgendaHistorico` usado por `routers/consultorio.py`.
- Restaurados campos de integração CEAF/reagendamento em `AgendaIntegrada`.
- Mantido o modelo do catálogo simplificado de medicamentos criado no 15D.7A.

## Validação esperada
Após aplicar o patch, o backend deve importar normalmente:

```bash
python -m py_compile backend/models/consultorio_models.py backend/routers/consultorio.py backend/main.py
```

## Deploy
Após commit/push, realizar novo deploy no Render.
