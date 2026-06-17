# 15D.8 — Cadastro Mestre como aglutinador da Agenda Única

## Diagnóstico

Foi confirmado que a estrutura de cadastro mestre já existe no backend pela tabela `pacientes_agenda` e pelo modelo `PacienteAgenda`. Essa tabela já é usada pela agenda, busca de pacientes, edição cadastral e histórico operacional.

O problema observado não exigia criar uma nova tabela de paciente mestre. O ajuste adequado foi utilizar `pacientes_agenda` como identidade operacional única da Farmácia Escola e fazer o CEAF alimentar essa estrutura antes de criar compromissos.

## Ajustes realizados

- A conciliação CEAF passou a garantir vínculo/criação do paciente no cadastro mestre antes de criar retirada prevista.
- Retiradas CEAF conciliadas passaram a ser eventos comuns da agenda:
  - `servico_origem = dispensacao`
  - `tipo_evento = retirada_medicamento`
  - `status = retirada_prevista`
- A origem CEAF fica preservada apenas como referência assistencial/histórica:
  - `paciente_ceaf_id`
  - `referencia_tipo = CEAF`
  - `referencia_id`
  - `origem_importacao = CONCILIACAO_CEAF`
- Foi criado endpoint para sincronizar CEAF com o cadastro mestre sem converter todos para paciente clínico.
- A busca da agenda por paciente passou a considerar também CPF, CNS, telefone e nome do cadastro mestre.

## Novo endpoint

`POST /consultorio/agenda/pacientes-mestre/sincronizar-ceaf`

Parâmetros:

- `apenas_nao_vinculados`: padrão `true`
- `limite`: padrão `5000`

## Interpretação operacional

A conciliação CEAF deve ser usada apenas como porta de entrada para criar o primeiro compromisso mensal quando necessário. Depois disso, o paciente segue a agenda comum, sem comportamento paralelo por origem.

## Validação sugerida

1. Executar `POST /consultorio/agenda/pacientes-mestre/sincronizar-ceaf`.
2. Executar `POST /consultorio/agenda/conciliacao-ceaf/sincronizar` para o mês vigente.
3. Consultar `GET /consultorio/agenda` e verificar eventos com:
   - `servico_origem = dispensacao`
   - `tipo_evento = retirada_medicamento`
   - `status = retirada_prevista`
4. Verificar se os eventos aparecem na Agenda como compromissos comuns de dispensação.
5. Testar filtro por paciente usando nome, CPF ou CNS.

## Arquivo alterado

- `backend/routers/consultorio.py`
