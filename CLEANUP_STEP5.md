# Passo 5 — Separação dos schemas Pydantic

Ajustes realizados:

- Criada a pasta `backend/schemas/`.
- Criado o arquivo `backend/schemas/core.py`.
- Criado o arquivo `backend/schemas/__init__.py`.
- Movidos do `main.py` para `schemas/core.py` os schemas:
  - `Token`
  - `UserOut`
  - `PasswordReset`
  - `ChangeOwnPassword`
  - `InativarPayload`
  - `IntervencaoCreate`
  - `IntervencaoOut`
  - `Indicadores`
  - `UserCreate`
- Atualizado o `main.py` para importar os schemas de `schemas.core`.
- Removidos imports desnecessários de Pydantic do `main.py`.
- Conferida a sintaxe Python dos arquivos alterados.

Objetivo: reduzir o tamanho do `main.py` sem alterar os endpoints existentes.
