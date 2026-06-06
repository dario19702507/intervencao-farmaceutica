# Saneamento técnico — Pacote 1

Este pacote corrige pontos de baixo risco e alto impacto no backend:

1. Remove duplicidade e fluxo morto em `criar_proxima_dispensacao_automatica()`.
2. Consolida a criação de agendamento usando `obter_ou_criar_paciente_agenda()`.
3. Corrige a atualização de status de notificações, evitando `commit()` dentro do loop de campos.
4. Mantém backup automático do `consultorio.py` antes de qualquer alteração.

## Como usar

Copie `saneamento_pacote1.py` para a pasta `backend` do projeto e execute:

```bash
python saneamento_pacote1.py
```

Depois rode:

```bash
python -m py_compile routers/consultorio.py
uvicorn main:app --reload
```

## Testes mínimos recomendados

1. Criar novo evento na Agenda.
2. Buscar paciente no Cadastro Mestre.
3. Marcar dispensação como realizada.
4. Confirmar geração da próxima dispensação ou alerta de risco de interrupção.
5. Marcar notificação como enviada, erro e pendente.

## Observação

O script não apaga arquivos antigos nem altera o banco. Ele apenas saneia trechos críticos do `consultorio.py`.
