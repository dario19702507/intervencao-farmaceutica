# Backup e restauração do banco de dados

Este projeto agora possui dois scripts auxiliares na raiz:

- `backup_database.py`: gera backup do banco configurado em `backend/.env`.
- `restore_database.py`: restaura um backup selecionado.

## 1. Gerar backup

Com o ambiente virtual ativado, na raiz do projeto:

```cmd
python backup_database.py
```

O arquivo será criado em:

```txt
backups/
```

Exemplo:

```txt
backups/backup_sqlite_20260610_213000.db
```

## 2. Retenção automática

Por padrão, o script mantém os últimos 30 backups.

Para alterar:

```cmd
python backup_database.py --retention 60
```

## 3. Restaurar backup SQLite

Feche o backend antes de restaurar.

```cmd
python restore_database.py --file backups/backup_sqlite_20260610_213000.db
```

Para confirmar sem prompt:

```cmd
python restore_database.py --file backups/backup_sqlite_20260610_213000.db --yes
```

Antes de substituir o banco atual, o script cria uma cópia de segurança com o sufixo:

```txt
_antes_restore_YYYYMMDD_HHMMSS
```

## 4. PostgreSQL / Supabase

Quando `DATABASE_URL` iniciar com `postgresql://` ou `postgres://`, o backup usa `pg_dump`.

Requisitos:

- PostgreSQL Client Tools instalado;
- `pg_dump` e `psql` disponíveis no PATH;
- `DATABASE_URL` correta no `backend/.env`.

Backup:

```cmd
python backup_database.py
```

Restauração:

```cmd
python restore_database.py --file backups/backup_postgres_YYYYMMDD_HHMMSS.sql
```

## 5. Recomendação operacional

Antes de qualquer atualização importante:

```cmd
python backup_database.py
pytest -q tests
python tests\smoke_tests.py
```

Depois de restaurar:

```cmd
pytest -q tests
python tests\smoke_tests.py
```
