# Passo 6A - Modelos do Consultorio separados

Ajustes realizados:

- Movidos os modelos SQLAlchemy do Consultorio de `backend/routers/consultorio.py` para `backend/models/consultorio_models.py`.
- Mantida a importacao dos modelos em `consultorio.py` para preservar compatibilidade com outros routers que ainda importam nomes a partir dele.
- Mantido `BaseConsultorio.metadata.create_all(bind=engine)` no router por enquanto, para evitar alteracao brusca no ciclo de inicializacao.

Proximo passo recomendado: separar os schemas Pydantic do Consultorio para `backend/schemas/consultorio_schemas.py`.
