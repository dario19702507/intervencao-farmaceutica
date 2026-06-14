# Passo 13C.0 — Migração Segura do App de Intervenções

Este pacote cria a infraestrutura segura para importar dados do App de Intervenções já em produção no Supabase.

## Recursos

- Estrutura de staging `intervencoes_importacao_staging`.
- Checkpoints em `migracao_intervencoes_checkpoint`.
- Campos de rastreabilidade na tabela oficial `intervencoes`:
  - `origem_sistema`
  - `origem_id`
  - `batch_importacao`
  - `data_importacao`
- Importação idempotente por `origem_sistema + origem_id`.
- Consolidação controlada.
- Rollback por batch de importação.
- Dashboard de migração.

## Instalação

Copie os arquivos do pacote para a raiz do projeto e rode:

```cmd
python scripts\aplicar_passo13C0.py
```

Depois reinicie o backend:

```cmd
cd backend
uvicorn main:app --reload
```

Em outro terminal:

```cmd
pytest -q tests
python tests\smoke_tests.py
```

## Fluxo recomendado

1. Criar backup normal do projeto:

```cmd
python backup_database.py
```

2. No Swagger, executar:

```txt
POST /consultorio/migracao-intervencoes/preparar-estrutura
POST /consultorio/migracao-intervencoes/checkpoint?etapa=PRE_IMPORTACAO
POST /consultorio/migracao-intervencoes/staging/importar-json
GET  /consultorio/migracao-intervencoes/dashboard
POST /consultorio/migracao-intervencoes/consolidar
GET  /consultorio/migracao-intervencoes/dashboard
```

3. Se algo estiver errado, usar:

```txt
POST /consultorio/migracao-intervencoes/rollback?batch_importacao=<batch>
```

## Observação

Use o arquivo `intervencoes_rows.json` exportado do Supabase como fonte principal. CSV e SQL devem ficar apenas como conferência/backup.
