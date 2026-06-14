# Passo 7B.1 — Router de Serviços Rápidos

Alterações realizadas:

- Criado `backend/routers/servicos_rapidos.py`.
- Movidas as rotas básicas de serviços rápidos:
  - `POST /consultorio/atendimento-rapido`;
  - `POST /consultorio/afericao-pa`;
  - `POST /consultorio/glicemia`;
  - `POST /consultorio/bioimpedancia`;
  - `POST /consultorio/pico-fluxo`;
  - `GET /consultorio/atendimentos-rapidos`;
  - `GET /consultorio/atendimento-rapido/{atendimento_id}/detalhes`.
- Mantidos os mesmos endpoints públicos.
- Nenhuma alteração intencional no frontend.

Validação recomendada:

```bash
uvicorn main:app --reload
```

Testar no Swagger:

- `POST /consultorio/atendimento-rapido`;
- `POST /consultorio/afericao-pa`;
- `POST /consultorio/glicemia`;
- `POST /consultorio/bioimpedancia`;
- `POST /consultorio/pico-fluxo`;
- `GET /consultorio/atendimentos-rapidos`;
- `GET /consultorio/atendimento-rapido/{atendimento_id}/detalhes`.
