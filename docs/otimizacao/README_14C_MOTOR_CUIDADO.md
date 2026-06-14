# Passo 14C — Motor de Cuidado Farmacêutico e redução de redundâncias

Este pacote inicia a transformação do Consultório em um prontuário farmacêutico longitudinal, sem remover rotas legadas ainda. A estratégia é criar contratos canônicos e reduzir gradualmente a dependência de telas/rotas duplicadas.

## O que foi adicionado

- PRM estruturado por paciente.
- Metas terapêuticas com prazo, alvo, resultado e status.
- Ações do plano de cuidado vinculáveis a PRM, meta e intervenção.
- Escore automático de complexidade farmacoterapêutica.
- Resumo longitudinal de cuidado do paciente.
- Dashboard do cuidado farmacêutico.
- Endpoint canônico `/consultorio/cuidado/opcoes`.
- Smoke test atualizado.

## Rotas novas principais

- `GET /consultorio/cuidado/opcoes`
- `GET /consultorio/cuidado/dashboard`
- `GET /consultorio/paciente-clinico/{paciente_id}/resumo-cuidado`
- `GET /consultorio/paciente-clinico/{paciente_id}/complexidade-farmacoterapeutica`
- `GET /consultorio/paciente-clinico/{paciente_id}/prm`
- `POST /consultorio/paciente-clinico/{paciente_id}/prm`
- `PUT /consultorio/prm/{prm_id}/status`
- `GET /consultorio/paciente-clinico/{paciente_id}/metas-terapeuticas`
- `POST /consultorio/paciente-clinico/{paciente_id}/metas-terapeuticas`
- `PUT /consultorio/metas-terapeuticas/{meta_id}/avaliar`
- `GET /consultorio/paciente-clinico/{paciente_id}/acoes-plano-cuidado`
- `POST /consultorio/paciente-clinico/{paciente_id}/acoes-plano-cuidado`
- `PUT /consultorio/acoes-plano-cuidado/{acao_id}/status`

## Diretriz de redução de redundâncias

As rotas antigas continuam funcionando. A próxima etapa deve migrar a tela do Consultório para consumir preferencialmente `/resumo-cuidado`, e só depois descontinuar duplicidades como conversão clínica, evolução, desfecho, identificação e dados clínicos duplicados.

## Validação

Após aplicar o pacote:

```cmd
pytest -q tests
python tests\smoke_tests.py
```

