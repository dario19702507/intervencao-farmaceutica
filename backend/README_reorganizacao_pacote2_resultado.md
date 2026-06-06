# Reorganização Pacote 2 aplicada em 05/06/2026 16:45:17

Este pacote fez uma refatoração conservadora, sem remover rotas do `consultorio.py`.

## Alterações realizadas

1. Criou backup em `backup_reorganizacao_pacote2/`.
2. Criou `routers/agenda.py` como destino planejado das rotas da Agenda.
3. Corrigiu a auditoria da rota `POST /consultorio/agenda`:
   - antes usava `evento.id`, mas o objeto correto é `agenda`;
   - agora usa `db.flush()` antes de registrar auditoria.
4. Adicionou listas padronizadas:
   - `TIPOS_EVENTO_AGENDA`;
   - `STATUS_AGENDA`;
   - `SERVICOS_ORIGEM_AGENDA`.
5. Criou o modelo `ConfiguracaoSistema`.
6. Criou funções auxiliares:
   - `obter_configuracao()`;
   - `obter_configuracao_int()`;
   - `criar_configuracoes_padrao()`.
7. Criou rota:
   - `GET /consultorio/configuracoes`.
8. Ajustou alertas de renovação para usar configurações:
   - `dias_alerta_renovacao`;
   - `dias_alerta_urgente`.
9. Adicionou auditoria em:
   - atualização de agenda;
   - alteração de status da agenda.
10. Corrigiu `obter_ou_criar_paciente_agenda()` para retornar o paciente criado.

## Testes sugeridos

```bash
python -m py_compile routers/consultorio.py
uvicorn main:app --reload
```

Depois testar no Swagger ou frontend:

- `GET /consultorio/configuracoes`
- `POST /consultorio/agenda`
- `PUT /consultorio/agenda/{agenda_id}`
- `POST /consultorio/agenda/{agenda_id}/status`
- verificar auditoria:

```sql
SELECT * FROM auditoria_sistema ORDER BY id DESC LIMIT 20;
```

## Observação importante

Este pacote ainda não removeu as rotas de Agenda do `consultorio.py`. A extração real para `routers/agenda.py` deve ser feita no próximo pacote, após estes testes passarem.
