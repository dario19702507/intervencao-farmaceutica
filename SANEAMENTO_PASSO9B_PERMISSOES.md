# Passo 9B — Controle inicial de permissões por perfil

Este pacote adiciona uma camada centralizada de autorização em `backend/permissions.py`, sem alterar os endpoints existentes.

## Arquivos principais alterados

- `backend/permissions.py` — novo módulo de permissões.
- `backend/main.py` — passa a usar permissões centralizadas nas rotas principais.
- `backend/routers/consultorio.py` — funções locais de autorização passam a delegar para `permissions.py`.
- `tests/test_permissoes.py` — novos testes automatizados de permissão.
- `docs/MATRIZ_PERMISSOES_PASSO9B.md` — documentação da matriz inicial.

## Perfis padronizados

- `admin`
- `farmaceutico`
- `estagiario`
- `pesquisador`
- `visualizacao`

## Compatibilidade mantida

- `leitor` continua aceito como leitura restrita.
- `operador` continua aceito temporariamente como perfil com escrita assistencial.

## Testes recomendados

Com o backend rodando:

```cmd
pytest -q tests
python tests\smoke_tests.py
```

## Observação

Este passo não implementa ainda uma matriz fina por endpoint. Ele cria a base técnica para isso, reduzindo regras duplicadas e evitando que permissões fiquem espalhadas em vários arquivos.
