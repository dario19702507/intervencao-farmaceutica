# Passo 6F — Indicadores e dashboards do Consultório

Ajustes realizados:

- Criado `backend/services/indicadores_consultorio.py`.
- Movida a regra de montagem de `/consultorio/dashboard-servicos`.
- Movida a regra de montagem de `/consultorio/triagem-risco`.
- Movida a função comum `aplicar_filtros_atendimento`.
- Mantidos os endpoints originais e seus parâmetros.
- `routers/consultorio.py` continua responsável pela exposição das rotas, mas a regra de negócio principal desses indicadores passou para o service.

Validação recomendada:

```bash
cd backend
uvicorn main:app --reload
```

Depois testar no Swagger:

- `GET /consultorio/dashboard-servicos`
- `GET /consultorio/triagem-risco`
