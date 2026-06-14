# Passo 6G — Farmacoterapia

Nesta etapa foi iniciada a separação das regras farmacoterapêuticas do arquivo `backend/routers/consultorio.py`.

## Arquivos criados

- `backend/services/farmacoterapia.py`

## Regras movidas para service

- Avaliação automatizada de polifarmácia.
- Evolução farmacoterapêutica longitudinal.
- Sugestões para plano de cuidado.
- Dashboard farmacoterapêutico.

## Rotas preservadas

As rotas continuam as mesmas:

- `GET /consultorio/paciente-clinico/{paciente_id}/avaliacao-polifarmacia`
- `GET /consultorio/paciente-clinico/{paciente_id}/evolucao-farmacoterapeutica`
- `GET /consultorio/paciente-clinico/{paciente_id}/sugestoes-plano-cuidado`
- `GET /consultorio/dashboard-farmacoterapeutico`

## Resultado

O arquivo `backend/routers/consultorio.py` foi reduzido de aproximadamente 6819 para 6336 linhas.

## Observação

Esta etapa foi deliberadamente conservadora. As rotas de cadastro/listagem de medicamentos, intervenções farmacoterapêuticas e desfechos ainda permanecem no router para reduzir risco. Elas podem ser movidas em uma próxima etapa, quando criarmos routers específicos.
