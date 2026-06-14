# Passo 14E.2C.1B — Indicadores Automáticos de PRM

## Objetivo

Aproveitar os PRM padronizados do passo 14E.2C.1A para gerar indicadores automáticos globais e por paciente, sem depender de texto livre.

## O que foi incluído

- Novo serviço `montar_indicadores_prm` em `backend/services/cuidado_farmaceutico.py`.
- Novo endpoint global:

```txt
GET /consultorio/cuidado/prm-indicadores
```

- Novo endpoint por paciente:

```txt
GET /consultorio/paciente-clinico/{paciente_id}/prm-indicadores
```

- Smoke test atualizado.
- Teste automatizado para o endpoint global.

## Indicadores gerados

O endpoint retorna:

- total de PRM;
- PRM ativos, abertos, em acompanhamento, resolvidos e não resolvidos;
- PRM por categoria: Necessidade, Efetividade, Segurança e Adesão;
- PRM por subcategoria;
- PRM por natureza: potencial ou manifesto;
- PRM por criticidade;
- PRM por status;
- PRM por desfecho;
- PRM por origem;
- PRM por causa/fator contribuinte;
- PRM abertos há 30 dias ou mais;
- PRM abertos há 60 dias ou mais;
- taxa de resolução;
- taxa de padronização;
- tempo médio e mediano de resolução;
- pacientes prioritários;
- lista de pendências de PRM.

## Observação clínica

Os indicadores contam episódios de PRM, preservando os registros legados sem forçar migração automática. A taxa de padronização considera presença de subcategoria, natureza e criticidade estruturadas.

## Como aplicar

Copie os arquivos do pacote para os mesmos caminhos do projeto.

Depois execute:

```cmd
pytest -q tests
python tests\smoke_tests.py
```

## Arquivos alterados

```txt
backend/services/cuidado_farmaceutico.py
backend/routers/cuidado_farmaceutico.py
tests/test_cuidado_farmaceutico.py
tests/smoke_tests.py
```
