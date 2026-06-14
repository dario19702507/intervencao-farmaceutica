# Passo 11D.1 — Vigência Padrão de 6 Meses

Este ajuste atualiza o motor de vigência documental para a regra institucional definida:

- vigência automática = data de início + 6 meses - 1 dia;
- inclusão mantém início calculado por lançamento + 30 dias, com ajuste do dia 23 para o dia 01 do mês subsequente;
- renovação antecipada mantém início após o término do laudo vigente;
- renovação vencida até 3 meses mantém início por cadastro + 8 dias, com ajuste do dia 23;
- exceções continuam possíveis por edição manual da vigência, com motivo obrigatório e histórico/auditoria.

Substitua somente os arquivos do backend e testes incluídos neste pacote.

Após substituir, execute:

```cmd
pytest -q tests
python tests\smoke_tests.py
```
