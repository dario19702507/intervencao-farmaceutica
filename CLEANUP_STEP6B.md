# Passo 6B — Schemas do Consultório

Ajustes realizados:

- Criado `backend/schemas/consultorio_schemas.py`.
- Movidas as classes Pydantic do Consultório para o novo arquivo.
- `backend/routers/consultorio.py` passou a importar os schemas.
- Mantidos os endpoints e nomes de classes.
- Corrigidos imports de `Date` e `relationship` em `models/consultorio_models.py`, preservando a validação feita no Passo 6A.

Teste recomendado:

```bash
cd backend
python -m py_compile main.py routers/consultorio.py models/consultorio_models.py schemas/consultorio_schemas.py
uvicorn main:app --reload
```
