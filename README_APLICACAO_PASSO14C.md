# Passo 14C — Motor de Cuidado Farmacêutico + redução progressiva de redundâncias

Este pacote adiciona contratos canônicos para o Consultório Farmacêutico sem remover rotas legadas ainda.

## Conteúdo

- Backend:
  - novos modelos: PRM, metas terapêuticas, ações do plano e avaliação de complexidade;
  - novo serviço `services/cuidado_farmaceutico.py`;
  - novo router `routers/cuidado_farmaceutico.py`;
  - inclusão do router no `main.py`.
- Frontend:
  - nova página base `CuidadoFarmaceutico.jsx` para dashboard/estrutura do motor de cuidado;
  - CSS próprio.
- Testes:
  - `test_cuidado_farmaceutico.py`;
  - smoke tests com `/consultorio/cuidado/opcoes` e `/consultorio/cuidado/dashboard`.

## Como aplicar

Sobrescreva/adicone os arquivos nos mesmos caminhos do projeto.

Depois rode:

```cmd
cd backend
uvicorn main:app --reload
```

Em outro terminal:

```cmd
pytest -q tests
python tests\smoke_tests.py
```

## Rotas novas

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

## Observação sobre redundâncias

Este pacote não remove rotas duplicadas imediatamente. Ele cria a camada canônica. A próxima fase deve migrar a tela principal do Consultório para consumir `/resumo-cuidado` e, depois, descontinuar rotas duplicadas com segurança.
