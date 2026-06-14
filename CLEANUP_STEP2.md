# Passo 2 — Centralização inicial de banco e autenticação

## Objetivo
Reduzir duplicidades estruturais sem alterar funcionalidades do sistema.

## Arquivos criados
- `backend/database.py`
- `backend/auth.py`

## Ajustes realizados
- `backend/main.py` agora importa `Base`, `engine`, `SessionLocal` e `get_db` de `database.py`.
- `backend/main.py` agora importa `SECRET_KEY`, `ALGORITHM`, `oauth2_scheme`, `hash_password`, `verify_password` e `create_access_token` de `auth.py`.
- `backend/routers/consultorio.py` passou a reutilizar o mesmo `engine` e `SessionLocal` de `database.py`.
- `backend/routers/consultorio.py` passou a reutilizar as mesmas configurações de autenticação de `auth.py`.
- Foi removida a duplicidade da classe `UserOut` em `main.py`.

## Verificação
Todos os arquivos Python foram verificados quanto à sintaxe.

## Próximo passo recomendado
Separar os modelos `User` e `Intervencao` de `main.py` para `backend/models/intervencao_models.py`, mantendo compatibilidade com as rotas existentes.
