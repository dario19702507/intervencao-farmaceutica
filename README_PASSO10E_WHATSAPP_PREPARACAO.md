# Passo 10E — Preparação para WhatsApp

Esta etapa cria uma camada segura de fila e status para WhatsApp, sem envio externo real.

## O que foi incluído

- Modelo `WhatsAppEnvio`.
- Serviço `services/whatsapp_service.py`.
- Router `routers/whatsapp.py`.
- Registro do router no `main.py`.
- Testes automatizados.
- Smoke tests atualizados.

## Rotas novas

- `GET /consultorio/whatsapp/opcoes`
- `GET /consultorio/whatsapp/dashboard`
- `GET /consultorio/whatsapp/fila`
- `POST /consultorio/whatsapp/enfileirar-notificacoes`
- `POST /consultorio/whatsapp/envio-manual`
- `POST /consultorio/whatsapp/simular-envio`
- `PUT /consultorio/whatsapp/fila/{id}/cancelar`
- `PUT /consultorio/whatsapp/fila/{id}/reenfileirar`

## Status de envio

- `PENDENTE`
- `SIMULADO`
- `ENVIADO`
- `ERRO`
- `CANCELADO`
- `BLOQUEADO`

## Observação

A rota `simular-envio` não envia mensagens externas. Ela apenas valida a fila e marca os registros como `SIMULADO`. A integração real com Evolution API ou Meta Cloud API deve ser feita em etapa posterior.
