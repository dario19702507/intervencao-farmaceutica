# 15D.4A — Correção da busca CEAF na Agenda Integrada

## Objetivo
Corrigir o campo **Buscar paciente CEAF** na Agenda Integrada para carregar pacientes por nome, CPF, CNS ou medicamento.

## Correções aplicadas
- Adicionado `or_` aos imports SQLAlchemy em `backend/routers/consultorio.py`.
- Ajustada a busca de pacientes CEAF para considerar registros com `ativo = true` ou `ativo IS NULL`.
- Registros antigos importados antes da coluna `ativo` podem ter `NULL`, e por isso eram excluídos da busca.

## Validação recomendada
1. Deploy no Render.
2. Abrir Swagger e testar:
   - `GET /consultorio/agenda/pacientes-ceaf/buscar?termo=MARIA`
   - `GET /consultorio/agenda/pacientes-ceaf/buscar?termo=CPF`
3. No frontend, abrir Agenda Integrada e pesquisar paciente CEAF.
4. Selecionar paciente e confirmar carregamento automático de medicamento, vigência, telefone e situação LME.
