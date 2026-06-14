# Passo 13A — Painel Operacional da Farmácia Escola

Este pacote cria uma tela e um endpoint consolidado para a rotina operacional da Farmácia Escola.

## Backend

Novo endpoint:

- `GET /consultorio/painel-operacional`

O endpoint consolida:

- eventos de hoje;
- eventos de amanhã;
- retiradas de hoje;
- retiradas atrasadas;
- laudos vencendo em 60 dias;
- laudos vencidos;
- processos documentais incompletos;
- documentos rejeitados;
- notificações não lidas e urgentes;
- fila WhatsApp pendente.

## Frontend

Nova tela:

- `Painel Operacional`

Arquivos principais:

- `frontend/src/pages/operacional/PainelOperacional.jsx`
- `frontend/src/pages/operacional/PainelOperacional.css`

## Testes

Novo teste:

- `tests/test_painel_operacional.py`

Smoke test atualizado com:

- `GET /consultorio/painel-operacional`

## Validação

Com o backend ativo:

```cmd
pytest -q tests
python tests\smoke_tests.py
```
