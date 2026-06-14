# Passo 14E.2C.5B.1 — Ciclo de Vida da Farmacoterapia

Este pacote adiciona rastreabilidade longitudinal aos medicamentos em uso no Consultório Farmacêutico.

## Inclui

- Status do medicamento: `EM_USO`, `TROCADO`, `SUSPENSO`, `ENCERRADO`.
- Botões na farmacoterapia: **Trocar**, **Suspender** e **Encerrar**.
- Registro de motivo, data, observação, PRM associado e intervenção associada.
- Criação de novo medicamento quando houver troca.
- Preservação do medicamento anterior no histórico, sem exclusão.
- Eventos automáticos na Timeline Unificada.
- Campos de suporte para Analytics futuro.

## Aplicação

Extraia o pacote na raiz do projeto e rode:

```cmd
python scriptsplicar_passo14E2C5B1.py
pytest -q tests
python tests\smoke_tests.py
```

Depois teste o frontend:

```cmd
cd frontend
npm run dev
```

## Observação clínica

Troca, suspensão e encerramento não removem medicamentos. Eles registram a evolução da farmacoterapia e preservam a rastreabilidade do cuidado.
