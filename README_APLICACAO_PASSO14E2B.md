# Passo 14E.2B — Farmacoterapia estruturada e seleção assistida de medicamentos

Este pacote implementa a padronização inicial da farmacoterapia no Consultório Farmacêutico, mantendo compatibilidade com os registros antigos.

## Objetivo

Transformar o registro de medicamentos de uso do paciente de texto totalmente livre para **seleção assistida**, preservando a possibilidade de digitação manual quando o medicamento não estiver no catálogo.

## Principais mudanças

### Backend

- Ampliação de `MedicamentoUso` com campos estruturados:
  - `catalogo_medicamento_id`
  - `frequencia_uso`
  - `horarios_uso`
  - `uso_se_necessario`
- Ampliação de `CatalogoMedicamento` com campos compatíveis com futura base Anvisa/CMED:
  - `principio_ativo`
  - `nome_comercial`
  - `laboratorio`
  - `registro_anvisa`
  - `classe_terapeutica`
- Novo endpoint:
  - `GET /consultorio/farmacoterapia/opcoes`
- Compatibilidade com bancos existentes via migração simples e fallback no router.
- Avaliação farmacoterapêutica passa a considerar ausência de horários estruturados como sinal de complexidade/risco operacional.

### Frontend

Na aba **Farmacoterapia** do Consultório:

- Campo de busca no catálogo de medicamentos.
- Seleção assistida de medicamento padronizado.
- Campo manual quando o medicamento não existir no catálogo.
- Seleção padronizada de via de administração.
- Seleção padronizada de frequência.
- Seleção de horário/orientação de uso.
- Campo “uso se necessário”.

## Como aplicar

Copie os arquivos do pacote sobre o projeto atual, preservando os mesmos caminhos.

Depois rode:

```cmd
pytest -q tests
python tests\smoke_tests.py
```

No frontend:

```cmd
cd frontend
npm install
npm run dev
```

## Observação

O build do frontend não foi validado no sandbox porque o `node_modules` recebido contém dependência nativa do Rolldown incompatível com Linux. Em ambiente local, rode `npm install` antes do build/dev.

## Segurança operacional

Nenhum dado antigo é perdido. Os campos livres continuam existindo e seguem compatíveis. A seleção via catálogo é assistida, não obrigatória.
