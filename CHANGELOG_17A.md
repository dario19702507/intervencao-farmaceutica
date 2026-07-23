# Patch 17A — data real do atendimento e uso off-label

## Alterações

- Serviços rápidos: campo manual de data e hora, com preenchimento atual por padrão.
- Consultório: evolução clínica aceita data e hora retrospectivas.
- Auditoria preservada: `criado_em` continua indicando quando o registro entrou no sistema.
- Datas futuras são recusadas pelo backend.
- Farmacoterapia: situação off-label (`não avaliado`, `não`, `sim`).
- Quando off-label é `sim`, indicação e justificativa clínica são obrigatórias.
- Campo opcional para evidência, protocolo ou referência.
- Identificação off-label na tela, no prontuário PDF e nas orientações farmacêuticas.
- Migração automática e SQL alternativo para Supabase.

## Observação sobre dispensação

Os eventos de dispensação registrados pela Agenda Integrada já utilizam a data do evento informada manualmente. Este patch mantém essa lógica e concentra a nova separação entre data do atendimento e data do registro nos serviços rápidos e nas evoluções clínicas.
