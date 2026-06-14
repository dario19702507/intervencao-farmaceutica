# Saneamento técnico — Passo 1

## O que foi feito

1. Mantido como ponto de entrada oficial apenas `backend/main.py`.
2. Removidos do pacote saneado arquivos que não devem compor o código-fonte ativo:
   - ambientes virtuais (`venv`);
   - `node_modules`;
   - `dist`;
   - `__pycache__` e arquivos `.pyc`;
   - bancos locais `.db` e `.sqbpro`;
   - arquivos `.env` reais;
   - backups antigos;
   - scripts temporários de saneamento/reorganização.
3. Criados arquivos de exemplo de ambiente:
   - `backend/.env.example`;
   - `frontend/.env.example`.
4. Padronizado o frontend para usar apenas:
   - `frontend/src/api/api.js`.
5. Removido o duplicado:
   - `frontend/src/api.js`.
6. Removidos arquivos de backup do frontend:
   - `App_backup.jsx`;
   - `style_backup.css`;
   - `Consultorio.bak.jsx`;
   - duplicata sem extensão `IndicadoresCientificos`.

## O que ainda NÃO foi alterado

Este passo não altera lógica clínica, regras de negócio nem endpoints. A separação real do arquivo gigante `routers/consultorio.py` será feita no passo 2.

## Próximo passo recomendado

Passo 2: centralizar banco, autenticação e modelos em arquivos próprios:

- `backend/database.py`
- `backend/auth.py`
- `backend/models/intervencao_models.py`
- revisão gradual do `routers/consultorio.py`
