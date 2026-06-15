# 15D.2 — Tela Pacientes CEAF no frontend

## Objetivo
Disponibilizar no sistema a visualização dos pacientes importados do CEAF, no menu **Atendimento/Pacientes → Pacientes CEAF**, consumindo os endpoints criados no 15D.1.

## Arquivos alterados

- `frontend/src/navigation/catalog.jsx`
- `frontend/src/pages/pacientes/PacientesCeaf.jsx`
- `frontend/src/style.css`

## Funcionalidades implementadas

- Nova rota: `/atendimento/pacientes-ceaf`
- Novo item no menu lateral: **Atendimento → Pacientes CEAF**
- Consulta ao resumo CEAF: `GET /ceaf/pacientes/resumo`
- Listagem paginada: `GET /ceaf/pacientes`
- Detalhamento: `GET /ceaf/pacientes/{id}`
- Filtros por busca geral, medicamento, município, situação da LME e vigência
- Classificação visual de vigência: vigente, a vencer e vencida

## Observação operacional
A conversão para paciente clínico ainda não foi habilitada nesta etapa. A recomendação é validar primeiro a deduplicação entre CEAF, pacientes clínicos e prontuário longitudinal.

## Validação sugerida

```bash
cd frontend
npm run build
```

Depois publicar no Vercel e confirmar se aparece:

- Atendimento → Pacientes CEAF
- Cards de resumo CEAF
- Listagem dos pacientes importados
- Filtros funcionando
- Detalhes de paciente abrindo corretamente
