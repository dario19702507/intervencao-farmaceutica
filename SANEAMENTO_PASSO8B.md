# Saneamento técnico - Passo 8B

Este pacote foi saneado para continuidade do desenvolvimento local e versionamento.

## Ações realizadas

- Removidos arquivos `.env` reais.
- Removidos bancos locais `.db`, `.sqlite`, `.sqlite3`.
- Removidas pastas `venv`, `.venv`, `node_modules`, `dist`, `build`, `__pycache__` e `.git`.
- Removidos arquivos de backup com padrões `.bak`, `backup`, `Copia/Cópia`.
- Criados `backend/.env.example` e `frontend/.env.example`.
- Atualizado `.gitignore` para evitar novo vazamento de credenciais, bancos e artefatos locais.

## Contagem

- Itens removidos: 399
- Arquivos Python restantes: 64
- Routers encontrados: 26
- Services encontrados: 8

## Atenção

Credenciais que já foram expostas anteriormente devem ser rotacionadas no provedor correspondente, principalmente Supabase/Render/Vercel. Remover o arquivo do repositório evita novos vazamentos, mas não invalida uma chave que já circulou.

## Candidatos sensíveis remanescentes

- main-old.py
- main.py
- backend/auth.py

## Limpeza complementar

- Removidos `main.py` e `main-old.py` da raiz, pois a entrada oficial é `backend/main.py`.
- Removidos arquivos `CLEANUP_STEP*` e `README_PASSO*` para reduzir ruído operacional.
- Removidos diretórios vazios/obsoletos de backup.

## Candidatos sensíveis após limpeza complementar

- SANEAMENTO_PASSO8B.md [supabase]

## Limpeza de scripts antigos

- Removido `backend/FarmaciaEscola.env`.
- Removido `backend/intervencoes.sqbpro`.
- Removido `backend/reorganizacao_pacote1.py`.
- Removido `backend/reorganizacao_pacote2.py`.
- Removido `backend/reorganizacao_pacote3.py`.
- Removido `backend/reorganizacao_pacote4.py`.
- Removido `backend/reorganizacao_pacote5.py`.
- Removido `backend/reorganizacao_pacote5b.py`.
- Removido `backend/reorganizacao_pacote6a.py`.
- Removido `backend/reorganizacao_pacote6a_b.py`.
- Removido `backend/reorganizacao_pacote6b_1.py`.
- Removido `backend/reorganizacao_pacote6b_2.py`.
- Removido `backend/reorganizacao_pacote6c_1.py`.
- Removido `backend/reorganizacao_pacote6c_2.py`.
- Removido `backend/reorganizacao_pacote6d_1.py`.
- Removido `backend/saneamento_pacote1.py`.
- Removido `backend/saneamento_pacote2.py`.
- Removido `backend/README_reorganizacao_pacote2_resultado.md`.
- Removido `backend/README_reorganizacao_pacote5b_resultado.md`.
- Removido `backend/README_reorganizacao_pacote5_resultado.md`.
- Removido `backend/README_reorganizacao_pacote6a_b_resultado.md`.
- Removido `backend/README_reorganizacao_pacote6a_resultado.md`.
- Removido `backend/README_reorganizacao_pacote6b_1_resultado.md`.
- Removido `backend/README_reorganizacao_pacote6b_2_resultado.md`.
- Removido `backend/README_reorganizacao_pacote6c_1_resultado.md`.
- Removido `backend/README_reorganizacao_pacote6c_2_resultado.md`.
- Removido `backend/README_saneamento_pacote1.md`.
- Removido `backend/README_saneamento_pacote2.md`.
- Removido `backend/inspecionar_farmacoterapia.py`.
- Removido `backend/migrar_sqlite_para_supabase.py`.

## Varredura final de credenciais

Nenhum candidato sensível evidente encontrado pela varredura final.