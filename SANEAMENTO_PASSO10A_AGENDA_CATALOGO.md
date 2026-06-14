# Passo 10A — Agenda e Catálogo de Medicamentos

Implementa a base da Agenda Integrada com suporte aos tipos de evento:

- INCLUSAO
- RETIRADA
- RENOVACAO
- ADEQUACAO
- ENCERRAMENTO

Também cria o Catálogo de Medicamentos, permitindo cadastrar, listar, editar e inativar fármacos/apresentações. A Agenda passa a aceitar `medicamento_id`, permitindo vincular eventos a uma lista padronizada e evitando digitação livre inconsistente.

## Novas rotas

- `GET /consultorio/agenda/opcoes`
- `GET /consultorio/agenda/dashboard`
- `GET /consultorio/catalogo-medicamentos`
- `POST /consultorio/catalogo-medicamentos`
- `GET /consultorio/catalogo-medicamentos/{id}`
- `PUT /consultorio/catalogo-medicamentos/{id}`
- `DELETE /consultorio/catalogo-medicamentos/{id}`
- `POST /consultorio/catalogo-medicamentos/seed`

## Testes

Rode com o backend ligado:

```cmd
pytest -q tests
python tests\smoke_tests.py
```
