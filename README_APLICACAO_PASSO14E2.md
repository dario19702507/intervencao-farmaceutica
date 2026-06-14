# Passo 14E.2 — Timeline Única do Paciente

Este pacote implementa a timeline longitudinal única do paciente no Consultório Farmacêutico.

## Objetivo

Reunir, em uma única visão cronológica, eventos de:

- CEAF: inclusão, renovação, adequação, encerramento, vigência e retirada;
- Agenda;
- Documentos e status documental;
- OCR documental;
- Consultório e evolução clínica;
- Farmacoterapia;
- PRM;
- Intervenções farmacêuticas;
- Metas terapêuticas;
- Ações do plano de cuidado;
- Desfechos.

## Arquivos alterados

- `backend/services/cuidado_farmaceutico.py`
- `backend/routers/cuidado_farmaceutico.py`
- `frontend/src/pages/consultorio/Consultorio.jsx`
- `frontend/src/style.css`
- `tests/test_cuidado_farmaceutico.py`
- `tests/smoke_tests.py`

## Novos endpoints

```txt
GET /consultorio/cuidado/timeline-unificada/opcoes
GET /consultorio/paciente-clinico/{paciente_id}/timeline-unificada
```

O endpoint `GET /consultorio/paciente-clinico/{paciente_id}/resumo-cuidado` também passa a retornar:

```txt
timeline_unificada
timeline
```

A chave `timeline` foi mantida para compatibilidade com a tela do Consultório.

## Aplicação

Copie os arquivos deste pacote para os mesmos caminhos do projeto.

Depois rode:

```cmd
pytest -q tests
python tests\smoke_tests.py
```

No frontend:

```cmd
cd frontend
npm run dev
```

## Validação visual

Abra um paciente clínico no Consultório e acesse a aba **Timeline**. A tela deverá exibir a jornada longitudinal do paciente com eventos consolidados por categoria.

## Observação

Este passo não remove rotas antigas e não altera dados existentes. Ele apenas cria um contrato canônico de timeline unificada, reduzindo a fragmentação entre módulos.
