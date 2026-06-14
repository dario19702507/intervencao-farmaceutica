# Passo 13B — Relatórios Gerenciais

Inclui relatórios gerenciais em JSON, CSV e PDF para:

- operacional;
- vigências;
- documental.

## Endpoints principais

- `GET /consultorio/relatorios-gerenciais/opcoes`
- `GET /consultorio/relatorios-gerenciais/operacional`
- `GET /consultorio/relatorios-gerenciais/vigencias`
- `GET /consultorio/relatorios-gerenciais/documental`

## Exportações

- `/csv`
- `/pdf`

Exemplos:

- `GET /consultorio/relatorios-gerenciais/operacional/pdf`
- `GET /consultorio/relatorios-gerenciais/documental/csv`

## Testes

```cmd
pytest -q tests
python tests\smoke_tests.py
```
