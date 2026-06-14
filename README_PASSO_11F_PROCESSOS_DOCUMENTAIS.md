# Passo 11F — Pacote/Processo Documental do Paciente

Este passo cria a estrutura para vincular vários documentos a uma mesma ação administrativa/assistencial do paciente, como `INCLUSAO`, `RENOVACAO`, `ADEQUACAO` ou `ENCERRAMENTO`.

## Principais decisões de regra de negócio

1. Os documentos deixam de ser apenas arquivos isolados e podem compor um **Processo Documental**.
2. Um processo documental pode reunir laudo, receita, exames, documento pessoal, termo e outros arquivos.
3. A vigência pode ser controlada no processo e sincronizada com documentos principais, como laudo e receita.
4. Pendências documentais geram **notificação interna**, mas **não geram WhatsApp automático**.
5. WhatsApp relacionado a documentos/pedências documentais deve ser enviado apenas manualmente pelo operador.

## Novas rotas

- `GET /consultorio/processos-documentais/opcoes`
- `GET /consultorio/processos-documentais/dashboard`
- `POST /consultorio/paciente-clinico/{paciente_id}/processos-documentais`
- `GET /consultorio/paciente-clinico/{paciente_id}/processos-documentais`
- `GET /consultorio/processos-documentais/{processo_id}`
- `PUT /consultorio/processos-documentais/{processo_id}`
- `POST /consultorio/processos-documentais/{processo_id}/vincular-documento`
- `GET /consultorio/processos-documentais/{processo_id}/documentos`
- `POST /consultorio/processos-documentais/{processo_id}/notificar-pendencia`
- `PUT /consultorio/documentos/{documento_id}/desvincular-processo`

## Upload vinculado ao processo

A rota existente também passa a aceitar `processo_documental_id` no `multipart/form-data`:

- `POST /consultorio/paciente-clinico/{paciente_id}/documentos`

## Comunicação com paciente

A regra implementada é conservadora:

- Retirada, renovação e eventos objetivos podem alimentar fluxos automáticos.
- Pendência documental deve ser avaliada por operador antes de contato com o paciente.
- Para documentos, usar `POST /consultorio/whatsapp/envio-manual` quando for adequado comunicar o paciente.

## Validação

Após substituir os arquivos, executar:

```cmd
pytest -q tests
python tests\smoke_tests.py
```
