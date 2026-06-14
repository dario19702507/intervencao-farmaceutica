# Passo 12F — Governança documental: status por documento

Este pacote adiciona controle de status documental aos documentos vinculados ao paciente e aos processos documentais.

## Status documental

- `PENDENTE`: documento esperado, ainda não recebido.
- `RECEBIDO`: documento anexado, ainda não validado.
- `VALIDADO`: documento conferido e aceito pela equipe.
- `REJEITADO`: documento inadequado, ilegível, vencido ou divergente.
- `SUBSTITUIDO`: documento antigo substituído por nova versão.

## Regra de completude

A partir deste passo, a completude do processo documental considera somente documentos com:

```txt
status_documental = VALIDADO
```

Documentos apenas recebidos, rejeitados ou substituídos não completam exigências do pacote documental.

## WhatsApp documental

Permanece a regra de segurança já aprovada:

```txt
Pendência documental não gera WhatsApp automático.
WhatsApp documental somente manual pelo operador.
```

## Novas rotas

```txt
GET /consultorio/documentos/status-opcoes
GET /consultorio/documentos/status-dashboard
PUT /consultorio/documentos/{documento_id}/status-documental
GET /consultorio/documentos/{documento_id}/status-historico
```

## Testes

Após substituir os arquivos, rode:

```cmd
pytest -q tests
python tests\smoke_tests.py
```
