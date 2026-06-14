# Passo 6D — Separação de agenda e notificações

Este passo separa funções auxiliares de agenda e notificações do arquivo `backend/routers/consultorio.py`.

Criado:

- `backend/services/agenda_notificacoes.py`

Funções movidas:

- `obter_ou_criar_paciente_agenda`
- `calcular_capacidade_agenda`
- `criar_proxima_dispensacao_automatica`
- `gerar_alertas_renovacao_laudo`
- `gerar_alertas_risco_interrupcao`
- `gerar_notificacoes_agenda`

Os endpoints foram preservados. O arquivo `consultorio.py` passa a importar essas funções do novo service.
