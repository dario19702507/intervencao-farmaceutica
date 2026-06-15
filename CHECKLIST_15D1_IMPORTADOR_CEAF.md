# 15D.1 — Importador CEAF + tabela `pacientes_ceaf`

## Objetivo

Criar uma etapa segura de preparação de dados para homologação, mantendo o cadastro CEAF separado dos prontuários clínicos. A importação não sobrescreve `pacientes_clinicos` nem altera dados assistenciais já existentes.

## Arquivos alterados

- `backend/models/consultorio_models.py`
- `backend/routers/ceaf.py`
- `backend/main.py`
- `backend/requirements.txt`
- `backend/scripts/importar_pacientes_ceaf.py`
- `CHECKLIST_15D1_IMPORTADOR_CEAF.md`

## Nova tabela

`pacientes_ceaf`

Campos principais:

- `cpf`
- `cns`
- `nome`
- `medicamento_prescrito`
- `municipio`
- `logradouro`
- `numero_residencia`
- `complemento_residencia`
- `data_fim_vigencia`
- `situacao_lme`
- `data_inicio_medicamento`
- `telefone`
- `telefone_comercial`
- `telefone_celular`
- `chave_importacao`
- `lote_importacao`

## Endpoints criados

- `POST /ceaf/pacientes/importar-planilha`
- `GET /ceaf/pacientes`
- `GET /ceaf/pacientes/resumo`
- `GET /ceaf/pacientes/{paciente_id}`

## Como aplicar

Após extrair o patch:

```bash
cd backend
python -m pip install -r requirements.txt
git add .
git commit -m "15D1 importador CEAF"
git push origin main
```

No Render, faça novo deploy. Como o `requirements.txt` recebeu `xlrd==2.0.1`, use:

```text
Manual Deploy → Clear build cache & deploy
```

## Como importar pelo Swagger

1. Acesse `/docs`.
2. Faça login em `POST /auth/login`.
3. Clique em `Authorize` e cole o token no formato `Bearer TOKEN`.
4. Acesse `POST /ceaf/pacientes/importar-planilha`.
5. Envie a planilha `.xls`, `.xlsx` ou `.csv`.

## Como importar por script

```bash
python backend/scripts/importar_pacientes_ceaf.py \
  --arquivo "C:\caminho\planilha_ceaf.xls" \
  --api-url https://sistema-integrado-de-atencao-farmaceutica.onrender.com \
  --email admin@farmacia.local \
  --senha sua_senha
```

## Validação pós-importação

No Swagger, execute:

```text
GET /ceaf/pacientes/resumo
```

Resultado esperado para a planilha enviada: aproximadamente 584 registros válidos, dependendo de linhas vazias ou duplicadas.

## Observações

- A importação usa `chave_importacao` para evitar duplicidades.
- Registros existentes podem ser atualizados quando `atualizar_existentes=true`.
- Esta etapa não cria automaticamente pacientes clínicos; a conversão será tratada em etapa posterior.
