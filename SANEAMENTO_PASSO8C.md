# Passo 8C - Testes de fumaça e saneamento de rotas duplicadas

## Ajustes aplicados

- Removidas do `backend/routers/consultorio.py` as rotas científicas que já estavam no router modular `backend/routers/indicadores_cientificos.py`.
- Reordenado `backend/main.py` para registrar `consultorio_router` por último, reduzindo risco de o router legado interceptar rotas especializadas.
- Removido `backend/farmacoterapia.py` da raiz do backend, pois havia duplicidade/confusão com `backend/routers/farmacoterapia.py` e `backend/services/farmacoterapia.py`.
- Atualizados os inventários em `docs/inventario_endpoints_passo8C.csv` e `docs/rotas_duplicadas_passo8C.csv`.

## Validações realizadas

- Compilação Python: `python -m py_compile $(find . -name '*.py')` concluída sem erros.
- Duplicidades em runtime: **0**.
- Duplicidades apenas estáticas, em routers não registrados ou arquivos remanescentes: **21**.
- Tamanho atual de `consultorio.py`: **2235 linhas**.

## Como testar localmente

1. Inicie o backend:

```bash
cd backend
uvicorn main:app --reload
```

2. Em outro terminal, execute:

```bash
python tests/smoke_tests.py
```

3. Verifique no Swagger se as rotas críticas aparecem uma única vez:

- `GET /me`
- `GET /consultorio/pacientes-clinicos`
- `GET /consultorio/dashboard-servicos`
- `GET /consultorio/dashboard-farmacoterapeutico`
- `GET /consultorio/dashboard-efetividade-cuidado`
- `GET /consultorio/indicadores-cientificos`

## Observação

As duplicidades estáticas restantes devem ser revisadas posteriormente porque algumas pertencem a routers antigos não registrados no `main.py`, como `consultorio_clinico.py`, `relatorios_cientificos.py` e `bioimpedancia.py`. Como não estão ativos no runtime, não foram removidas nesta etapa para evitar regressão.
