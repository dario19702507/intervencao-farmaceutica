# Passo 14E.2C.1A — PRM Padronizados

Este pacote implementa a primeira etapa da estruturação clínica dos Problemas Relacionados a Medicamentos (PRM), preservando compatibilidade com dados antigos.

## O que foi incluído

- Catálogo versionado de PRM em quatro domínios: Necessidade, Efetividade, Segurança e Adesão.
- Subcategorias padronizadas com definições operacionais curtas.
- Natureza do PRM: Potencial ou Manifesto.
- Criticidade: Baixa, Moderada ou Alta.
- Status de fluxo: Aberto, Em acompanhamento, Resolvido, Não resolvido, Registro inválido e Descarta do/legado.
- Desfecho clínico separado do status.
- Origem do registro.
- Campo opcional de causa/fator contribuinte.
- Campo de condição de saúde relacionada.
- Sistema de codificação e versão de catálogo.
- Interface no Consultório para registrar PRM padronizado.
- Compatibilidade com registros legados por meio dos campos já existentes.

## Arquivos alterados

- backend/models/consultorio_models.py
- backend/services/cuidado_farmaceutico.py
- backend/routers/cuidado_farmaceutico.py
- frontend/src/pages/consultorio/Consultorio.jsx
- tests/test_cuidado_farmaceutico.py

## Validação recomendada

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

O build do frontend não foi validado no sandbox por incompatibilidade de dependência nativa do Rolldown/Vite presente no `node_modules` empacotado. Em ambiente local, rode `npm install` antes do build.
