# Passo 15A.0.4 — Central de Impressão

## Objetivo
Centralizar em uma única tela os principais documentos imprimíveis do sistema, sem alterar o backend.

## Arquivos incluídos
- frontend/src/pages/relatorios/Relatorios.jsx
- frontend/src/style.css

## O que foi implementado
- Central de Impressão em `Relatórios e Impressões`.
- Seleção de paciente clínico para impressão de:
  - Prontuário clínico.
  - Prontuário longitudinal.
  - Plano de cuidado.
  - Evoluções clínicas.
  - Orientações farmacêuticas.
- Impressão de declaração de serviço por ID do atendimento rápido.
- Impressão de laudo de bioimpedância por ID.
- Atalho para relatórios gerenciais, Analytics, Documentos, Consultório e Serviços rápidos.
- Impressão de relatório de resolução de alertas.

## Aplicação
Extraia o pacote na raiz do projeto, substituindo os arquivos indicados.

Depois execute:

```cmd
cd frontend
npm run build
npm run dev
```

Opcionalmente, valide também:

```cmd
pytest -q tests
python tests\smoke_tests.py
```
