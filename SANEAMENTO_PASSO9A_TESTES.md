# Passo 9A — Suíte inicial de testes automatizados

Este pacote adiciona uma estrutura inicial de testes para reduzir risco de regressão após a refatoração modular do backend.

## Arquivos adicionados/atualizados

- `tests/conftest.py`
- `tests/test_auth.py`
- `tests/test_core.py`
- `tests/test_consultorio.py`
- `tests/test_farmacoterapia.py`
- `tests/test_openapi_rotas.py`
- `tests/smoke_tests.py`
- `tests/README_TESTES.md`
- `backend/requirements.txt` atualizado com `requests` e `pytest`

## Como executar

Com o backend rodando:

```cmd
python tests\smoke_tests.py
pytest -q tests
```

## Observação

Os testes desta etapa são testes de integração contra o backend local ativo. Eles não criam um banco de testes isolado ainda. Essa separação deve ser feita em uma etapa posterior, quando forem criados testes de POST/PUT/DELETE.
