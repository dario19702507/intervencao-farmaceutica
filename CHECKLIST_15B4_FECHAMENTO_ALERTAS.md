# 15B.4 — Fechamento dos alertas de pré-homologação

Este patch consolida os pontos que o script ainda sinalizava como atenção após o 15B.3.

## Arquivos incluídos

- `backend/main.py`
- `backend/auth.py`
- `backend/scripts/pre_homologacao_check.py`
- `frontend/src/api/api.js`
- `CHECKLIST_15B4_FECHAMENTO_ALERTAS.md`

## O que foi reforçado

1. Controle explícito de ambiente por `APP_ENV`.
2. Bloqueio de `SECRET_KEY` ausente ou insegura em homologação/produção.
3. Criação do usuário admin padrão somente quando `SEED_ADMIN=true`.
4. Detecção mais clara de `X-Request-ID` e bloqueio de duplicidade no frontend.
5. Script de checagem atualizado para reduzir falso alerta em ambiente local.

## Como validar

No backend:

```bash
python scripts/pre_homologacao_check.py
```

Para teste local, é aceitável que o ambiente esteja como `APP_ENV=development`. Antes de subir no Render, configure `APP_ENV=homologation` e preencha `SECRET_KEY`, `DATABASE_URL` e `ALLOWED_ORIGINS`.
