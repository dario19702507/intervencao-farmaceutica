# 15D.7C.1 — Correção do importador do catálogo

## Problema identificado
O CSV estava correto, mas o importador não reconhecia cabeçalhos técnicos com underscore, como:

- principio_ativo
- forma_farmaceutica
- via_administracao
- registro_anvisa
- classe_terapeutica

Com isso, todos os registros eram ignorados com a mensagem: "Sem princípio ativo ou nome de medicamento".

## Correção
Atualização dos aliases de cabeçalho em `backend/routers/medicamentos.py` para aceitar os nomes técnicos usados na aba `Importacao_Sistema`.

## Arquivos alterados
- backend/routers/medicamentos.py

## Teste esperado
Importar `catalogo_ceaf_15D7C_sem_bom_ponto_virgula.csv` ou `catalogo_ceaf_15D7C_sem_bom_virgula.csv`.

Resultado esperado na primeira importação:
- Criados: aproximadamente 320
- Ignorados: 0 ou poucos registros

Se o banco já tiver registros equivalentes e `substituir_existentes=true`:
- Atualizados: aproximadamente 320
