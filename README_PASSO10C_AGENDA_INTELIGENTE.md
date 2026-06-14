# Passo 10C — Agenda Inteligente

Implementa as regras operacionais de agendamento da Farmácia Escola:

- Segunda-feira: 13:30 às 16:30.
- Terça-feira: 07:30 às 11:00.
- Quarta-feira: 07:30 às 11:00.
- Quinta-feira: 07:30 às 11:00 e 13:30 às 16:30.
- Sexta-feira, sábado e domingo: fechado.

## Regras implementadas

1. Próxima retirada automática respeita limite máximo de 30 dias.
2. Se D+30 cair em dia fechado, a data recua para o dia de atendimento anterior.
3. Alerta de renovação inicia no segundo mês anterior ao vencimento do laudo.
4. Alerta urgente de risco é programado no segundo mês após vencimento sem renovação.
5. O endpoint `/consultorio/agenda/opcoes` passa a retornar a configuração de atendimento.
6. Agendamentos manuais em data sem atendimento são ajustados automaticamente para o próximo dia de atendimento.

## Validação

Rode:

```cmd
pytest -q tests
python tests\smoke_tests.py
```

Teste no Swagger:

```txt
GET /consultorio/agenda/opcoes
POST /consultorio/agenda
POST /consultorio/agenda/{id}/status
POST /consultorio/agenda/gerar-alertas-renovacao
POST /consultorio/agenda/gerar-alertas-risco-interrupcao
```
