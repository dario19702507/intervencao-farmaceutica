# Passo 7A — Modularização de Pacientes do Consultório

## Objetivo
Separar as rotas de pacientes do arquivo `backend/routers/consultorio.py`, mantendo os mesmos endpoints usados pelo frontend.

## Arquivos criados
- `backend/routers/pacientes_consultorio.py`

## Arquivos alterados
- `backend/routers/consultorio.py`
- `backend/main.py`

## Rotas movidas
- `POST /consultorio/paciente-simplificado`
- `GET /consultorio/pacientes-simplificados`
- `GET /consultorio/paciente-simplificado/{paciente_id}`
- `GET /consultorio/paciente-simplificado/{paciente_id}/historico`
- `POST /consultorio/converter-para-clinico/{paciente_simplificado_id}`
- `PUT /consultorio/paciente-clinico/{paciente_id}/identificacao`
- `PUT /consultorio/paciente-clinico/{paciente_id}/dados-clinicos`
- `GET /consultorio/pacientes-clinicos`
- `GET /consultorio/buscar-paciente`
- `GET /consultorio/paciente-clinico/{paciente_id}`

## Resultado
O arquivo `consultorio.py` foi reduzido de aproximadamente 4736 para 4379 linhas.

## Validação sugerida
Após substituir os arquivos, executar:

```bash
cd backend
uvicorn main:app --reload
```

Testar no Swagger:

- `GET /consultorio/pacientes-simplificados`
- `GET /consultorio/pacientes-clinicos`
- `GET /consultorio/buscar-paciente`
- `POST /consultorio/paciente-simplificado`
