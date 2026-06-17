# 15D.7A — Catálogo simplificado de medicamentos (backend)

## Objetivo
Criar a base simplificada de medicamentos para uso futuro no Consultório Farmacêutico, farmacoterapia estruturada e intervenções, sem acoplar imediatamente ao cadastro CEAF.

## Decisão técnica
Foi reutilizada a tabela existente `catalogo_medicamentos`, evitando a criação de uma segunda tabela concorrente. Foram adicionados campos compatíveis com o catálogo simplificado:

- `via_administracao`
- `codigo_atc`
- `fonte_dados`
- `nome_normalizado`

## Endpoints criados

- `GET /medicamentos`
- `GET /medicamentos/buscar`
- `GET /medicamentos/resumo`
- `GET /medicamentos/{id}`
- `POST /medicamentos`
- `PUT /medicamentos/{id}`
- `POST /medicamentos/{id}/ativar?ativo=true|false`
- `POST /medicamentos/importar-csv`

## Importação CSV
O importador aceita CSV/TXT delimitado por `;`, `,` ou tabulação. Cabeçalhos aceitos incluem variações como:

- princípio ativo / substância / fármaco
- nome comercial / produto / medicamento
- concentração
- forma farmacêutica
- via de administração
- registro ANVISA
- classe terapêutica
- código ATC
- laboratório / empresa detentora
- apresentação
- componente

## Validação sugerida

```bash
python -m py_compile backend/routers/medicamentos.py backend/main.py backend/models/consultorio_models.py
```

Depois do deploy no Render, verificar no Swagger:

```text
/medicamentos
/medicamentos/buscar
/medicamentos/importar-csv
```

## Observação operacional
Esta etapa cria a fundação do catálogo. A integração com consultório/farmacoterapia deve ser feita em etapa posterior, para evitar alteração simultânea de fluxo clínico.
