# Passo 11D — Integração Documento → Vigência → Agenda → Notificação → WhatsApp

## O que foi implementado

- Campos de vigência no documento:
  - `operacao_vigencia`
  - `vigencia_inicio`
  - `vigencia_fim`
  - `vigencia_status`
  - `vigencia_origem_calculo`
  - `vigencia_editada_manualmente`
  - `motivo_alteracao_vigencia`
- Histórico/auditoria de alterações de vigência em `historico_vigencias_documentos`.
- Motor de cálculo automático de vigência:
  - Inclusão: lançamento + 30 dias.
  - Se início calculado for após dia 23: transfere para 01 do mês subsequente.
  - Renovação antecipada: inicia após o fim do laudo vigente.
  - Renovação vencida até 3 meses: cadastro + 8 dias, com regra do dia 23.
  - Adequação: nova data a partir do cadastro, ajustada para dia de atendimento.
- Geração automática de fluxo derivado:
  - Agenda de renovação importante.
  - Agenda urgente no primeiro dia útil após vencimento.
  - Notificação interna.
  - Fila WhatsApp simulada.
- Vigência editável pelo operador com motivo obrigatório.

## Novas rotas

- `GET /consultorio/documentos/{documento_id}/vigencia-historico`
- `PUT /consultorio/documentos/{documento_id}/vigencia`
- `POST /consultorio/documentos/{documento_id}/reprocessar-fluxo`

## Ajustes em rota existente

`POST /consultorio/paciente-clinico/{paciente_id}/documentos` agora aceita o campo opcional:

- `operacao_vigencia`: `INCLUSAO`, `RENOVACAO`, `ADEQUACAO`

## Testes

Após substituir os arquivos:

```cmd
pytest -q tests
python tests\smoke_tests.py
```
