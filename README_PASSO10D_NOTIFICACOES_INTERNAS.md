# Passo 10D — Central de Notificações Internas

Este pacote implementa a central de notificações internas para a Agenda da Farmácia Escola.

## Regra oficial de renovação

- Segundo mês anterior ao vencimento: notificação IMPORTANTE.
- Primeiro dia útil após o vencimento, se não houver renovação registrada: notificação URGENTE.

A regra respeita os dias de atendimento da Farmácia Escola já definidos na Agenda Inteligente.

## Novas rotas

- `GET /consultorio/notificacoes/opcoes`
- `GET /consultorio/notificacoes/dashboard`
- `GET /consultorio/notificacoes`
- `GET /consultorio/notificacoes/nao-lidas`
- `POST /consultorio/notificacoes`
- `POST /consultorio/notificacoes/gerar-automaticas`
- `PUT /consultorio/notificacoes/{id}/marcar-lida`
- `PUT /consultorio/notificacoes/marcar-todas-lidas`

## Testes

Após substituir os arquivos:

```cmd
pytest -q tests
python tests\smoke_tests.py
```
