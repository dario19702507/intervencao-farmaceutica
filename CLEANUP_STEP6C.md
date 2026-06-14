# Passo 6C — Funções auxiliares do Consultório

Alterações realizadas:

- Criada a pasta `backend/services/`.
- Criado o arquivo `backend/services/consultorio_helpers.py`.
- Movidas para esse arquivo funções auxiliares puras usadas pelo módulo Consultório:
  - `calcular_idade`
  - `classificar_imc`
  - `classificar_gordura_visceral`
  - `calcular_bioimpedancia`
  - `calcular_risco_populacional`
  - `definir_prioridade`
  - `gerar_sugestao_conduta`
  - `dashboard_vazio`
  - `calcular_percentual`
  - `classificar_pa`
  - `classificar_glicemia`
  - `classificar_pico_fluxo`
- `routers/consultorio.py` passou a importar essas funções.
- Nenhum endpoint foi alterado.
- Nenhuma regra de banco foi alterada.
- Sintaxe Python validada com `compileall`.

Objetivo do passo:

Reduzir o tamanho e o acoplamento inicial do arquivo `routers/consultorio.py`, preparando a separação futura de serviços mais complexos.
