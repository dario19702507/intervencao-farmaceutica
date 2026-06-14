# Passo 14E.2C.3A — Metas Terapêuticas Estruturadas

Este pacote implementa a primeira etapa de padronização das metas terapêuticas, seguindo o fluxo clínico:

```text
PRM → Intervenção → Meta → Plano de Cuidado → Desfecho/Indicador
```

## O que foi incluído

- Catálogo versionado de metas terapêuticas (`2026.06`).
- Categorias: controle clínico, adesão, segurança, processo assistencial e outra.
- Subcategorias padronizadas, como PA, HbA1c, LDL, adesão, retirada regular, ausência de RAM e renovação documental.
- Campos estruturados para valor atual, valor alvo, unidade, data inicial, data prevista, data de conclusão, origem, código e versão do catálogo.
- Vínculo opcional com PRM e intervenção farmacoterapêutica.
- Compatibilidade com metas legadas já existentes.
- Dashboard inicial de metas.
- Smoke tests atualizados.

## Arquivos do pacote

```text
backend/routers/metas_terapeuticas.py
scripts/aplicar_passo14E2C3A.py
tests/test_metas_terapeuticas.py
```

## Como aplicar

Extraia o ZIP na raiz do projeto e execute:

```cmd
python scripts\aplicar_passo14E2C3A.py
```

Depois rode:

```cmd
pytest -q tests
python tests\smoke_tests.py
```

## Novos endpoints

```text
GET  /consultorio/metas/opcoes
GET  /consultorio/metas/dashboard
GET  /consultorio/metas
GET  /consultorio/metas/{id}
POST /consultorio/metas
PUT  /consultorio/metas/{id}
GET  /consultorio/paciente-clinico/{paciente_id}/metas-estruturadas
```

## Observação de segurança

O pacote não remove campos antigos nem migra metas automaticamente. As metas legadas continuam válidas e passam a aparecer com marcador de compatibilidade.
