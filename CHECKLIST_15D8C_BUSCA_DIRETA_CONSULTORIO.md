# 15D.8C — Busca direta de paciente no Consultório

## Objetivo

Evitar o carregamento completo da lista de pacientes na aba **Consultório → Pacientes e Prontuários**, substituindo por busca direta por paciente específico.

## Alterações realizadas

### Backend

Arquivo alterado:

- `backend/routers/conversao_clinica.py`

Incluído endpoint:

- `GET /consultorio/pacientes-clinicos/buscar`

Parâmetros:

- `termo`: nome, CPF, CNS, telefone, bairro ou nome da mãe
- `limit`: limite de resultados, máximo 50

Também foi ajustado o endpoint legado:

- `GET /consultorio/pacientes-clinicos`

para usar paginação simples (`limit` e `offset`) em vez de retornar toda a base por padrão.

### Frontend

Arquivo alterado:

- `frontend/src/pages/consultorio/Consultorio.jsx`

A aba **Pacientes e Prontuários** agora:

- não carrega todos os pacientes ao abrir;
- exibe campo de busca por nome, CPF, CNS ou telefone;
- busca automaticamente após 3 caracteres com pequeno atraso;
- permite busca manual pelo botão **Buscar**;
- exibe apenas os pacientes encontrados;
- mantém o botão **Abrir prontuário**.

## Validação local sugerida

Backend:

```bash
python -m py_compile backend/routers/conversao_clinica.py
```

Frontend:

```bash
cd frontend
npm run build
```

## Testes funcionais

1. Abrir **Consultório → Pacientes e Prontuários**.
2. Confirmar que a lista completa não é carregada inicialmente.
3. Buscar por nome.
4. Buscar por CPF.
5. Buscar por CNS.
6. Buscar por telefone.
7. Selecionar paciente e abrir prontuário.
8. Conferir se evolução, medicamentos, plano de cuidado e timeline continuam carregando.

## Deploy

Como há alteração de backend e frontend:

- Render: deploy do backend.
- Vercel: redeploy do frontend.
