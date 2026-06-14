# 15B.3 — Ajuste fino de ambiente para homologação multiusuário

## Objetivo
Preparar o sistema para um piloto controlado com múltiplos usuários, reduzindo riscos de exposição indevida, erro de configuração e duplicidade de dados.

## Antes de subir para homologação

1. Gerar uma chave segura:

```bash
cd backend
python scripts/gerar_secret_key.py
```

2. Configurar no Render, em Environment:

```text
APP_ENV=homologation
DATABASE_URL=postgresql+psycopg2://...
SECRET_KEY=<valor gerado pelo script>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
ALLOWED_ORIGINS=https://seu-frontend.vercel.app
SEED_ADMIN=false
```

3. Configurar no Vercel, em Environment Variables:

```text
VITE_API_URL=https://seu-backend.onrender.com
```

4. Confirmar no Supabase:

```text
RLS habilitado nas tabelas públicas
backup/exportação realizada antes do piloto
usuários de teste criados com perfis definidos
```

5. Rodar localmente:

```bash
cd backend
python scripts/pre_homologacao_check.py
python -m py_compile main.py auth.py permissions.py scripts/pre_homologacao_check.py scripts/gerar_secret_key.py
```

6. Rodar frontend:

```bash
cd frontend
npm run build
```

## Roteiro mínimo do piloto com 2 usuários

Usuário 1 deve registrar paciente, atendimento rápido, evolução clínica e impressão. Usuário 2 deve, simultaneamente, registrar outro paciente e outra evolução. Em seguida, testar se um perfil de leitura consegue visualizar, mas não consegue alterar dados clínicos.

## Critérios para liberar fase com 5 usuários

A fase seguinte só deve ocorrer se não houver erro 500 recorrente, falha de login, duplicidade de salvamento, perda de dados, exposição sem login, erro de CORS ou lentidão crítica ao salvar.
