# Ajuste 13B.1 — Relatórios em formato tabular

Este pacote corrige a exportação dos relatórios gerenciais.

## Ajustes

- CSV agora usa separador `;`, compatível com Excel em configuração pt-BR.
- CSV inclui BOM UTF-8 para preservar acentos.
- PDF agora usa tabelas com cabeçalhos e linhas, em página paisagem.
- Indicadores, eventos, vigências e documentos rejeitados são apresentados em seções tabulares.

## Arquivo alterado

- `backend/routers/relatorios_gerenciais.py`

## Teste

Depois de substituir, rode:

```cmd
pytest -q tests
python tests\smoke_tests.py
```

Depois teste os botões CSV/PDF na tela de Relatórios Gerenciais.
