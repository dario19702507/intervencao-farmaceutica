# 15D.6 — Alertas CEAF integrados à Agenda/Notificações (backend)

## Objetivo

Integrar os alertas derivados da base CEAF à estrutura já existente da Agenda, sem criar uma nova central paralela.

## O que foi implementado

- Motor de alertas CEAF em `backend/routers/consultorio.py`.
- Priorização dos alertas em quatro níveis operacionais:
  - crítico;
  - urgente;
  - atenção;
  - informativo.
- Integração dos alertas CEAF ao endpoint já usado pela aba **Visão Geral**:
  - `GET /consultorio/alertas-pendentes`.
- Novos endpoints de apoio:
  - `GET /consultorio/agenda/alertas-ceaf`;
  - `GET /consultorio/agenda/alertas-ceaf/resumo`;
  - `GET /consultorio/agenda/notificacoes-pendentes-ceaf`.
- Inclusão de notificações CEAF na geração já existente da aba **Notificações**:
  - `POST /consultorio/agenda/notificacoes/gerar`.
- Integração com `notificacoes_agenda`, sem envio automático de WhatsApp.

## Alertas contemplados

- LME vencida.
- LME vencendo em 7 dias.
- LME vencendo em 15 dias.
- LME vencendo em 30 dias.
- Retirada prevista para hoje.
- Retirada prevista para amanhã.
- Retirada atrasada.
- Paciente CEAF ativo sem retirada prevista/agendada/realizada no mês.

## Regras de segurança

- Não dispara WhatsApp automaticamente.
- Não cria duplicidade de notificação pendente/enviada para o mesmo evento.
- Não cria menu novo; os dados devem ser consumidos pela Visão Geral e pela aba Notificações.
- Mantém compatibilidade com a central de notificações já existente.

## Validação local

Executado:

```bash
python -m py_compile backend/routers/consultorio.py
```

## Após aplicar

```bash
git add backend/routers/consultorio.py CHECKLIST_15D6_ALERTAS_CEAF_BACKEND.md
git commit -m "Integra alertas CEAF ao backend da agenda 15D6"
git push origin main
```

Depois fazer deploy no Render.

## Testes no Swagger

Após deploy, validar:

```text
GET /consultorio/agenda/alertas-ceaf
GET /consultorio/agenda/alertas-ceaf/resumo
GET /consultorio/agenda/notificacoes-pendentes-ceaf
GET /consultorio/alertas-pendentes
POST /consultorio/agenda/notificacoes/gerar
GET /consultorio/agenda/notificacoes/listar
```
