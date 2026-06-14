# Passo 11B — Validade Documental

Este pacote acrescenta controle operacional de validade para documentos de pacientes clínicos.

## Regras implementadas

- Documentos com `data_validade` são classificados automaticamente em:
  - `VALIDO`;
  - `VENCE_EM_60_DIAS`;
  - `VENCE_EM_30_DIAS`;
  - `VENCIDO`;
  - `VENCIDO_URGENTE`;
  - `SEM_VALIDADE`.
- Para LAUDO e RECEITA, o sistema pode gerar notificações internas automáticas.
- Laudo/receita vencido passa a ser prioridade `URGENTE` a partir do primeiro dia de atendimento da Farmácia Escola após o vencimento.

## Rotas novas

- `GET /consultorio/documentos/validade-dashboard`
- `GET /consultorio/documentos/vencimentos`
- `POST /consultorio/documentos/gerar-notificacoes-validade`

## Testes

```cmd
pytest -q tests
python tests\smoke_tests.py
```
