# Passo 12C.4 — Validação de completude do pacote documental

Este passo compara os documentos esperados para cada processo documental com os documentos recebidos e/ou classificados por OCR.

## Regra principal

- Pendências documentais geram apenas notificação interna.
- WhatsApp documental automático permanece bloqueado.
- O envio por WhatsApp deve ser manual pelo operador.

## Endpoints novos

- `GET /consultorio/processos-documentais/completude-dashboard`
- `GET /consultorio/processos-documentais/{processo_id}/completude`
- `POST /consultorio/processos-documentais/{processo_id}/validar-completude`

## Status de completude

- `COMPLETO`
- `INCOMPLETO`
- `SEM_DOCUMENTOS`
- `EM_ANALISE`

## Observação

A validação considera tanto o tipo cadastrado do documento quanto a classificação OCR/reclassificação manual mais recente.
