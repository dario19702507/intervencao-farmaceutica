# Pacote 2 de saneamento estrutural

Este pacote aplica uma refatoração incremental no backend, com foco em segurança e manutenção, sem dividir ainda o `consultorio.py` em vários arquivos.

## O que ele faz

1. Cria backup automático de `routers/consultorio.py`.
2. Saneia a função `criar_proxima_dispensacao_automatica`.
3. Consolida o `POST /consultorio/agenda` usando o Cadastro Mestre (`pacientes_agenda`).
4. Corrige a rota de atualização de status de notificações.
5. Reposiciona `BaseConsultorio.metadata.create_all(bind=engine)` para depois dos modelos principais.
6. Cria índices úteis no SQLite.

## Como executar

Copie `saneamento_pacote2.py` para a pasta `backend` e rode:

```bash
python saneamento_pacote2.py
python -m py_compile routers/consultorio.py
uvicorn main:app --reload
```

## Testes sugeridos

Depois de iniciar o backend, teste:

1. Criar agendamento com paciente já existente.
2. Criar agendamento com paciente novo.
3. Marcar dispensação como `realizado`.
4. Confirmar geração da próxima dispensação ou alerta de risco.
5. Abrir Central de Notificações e alterar status para `enviada`, `erro`, `pendente`.
6. Abrir `Pacientes > Histórico`.

## Observação

Este pacote ainda não divide fisicamente o `consultorio.py` em `agenda.py`, `pacientes.py`, etc. Essa divisão deve ser feita no Pacote 3, depois que estes testes estiverem estáveis.
