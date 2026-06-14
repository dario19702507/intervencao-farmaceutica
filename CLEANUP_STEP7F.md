# Passo 7F — Conversão e Cadastro Clínico

Arquivos alterados:

- backend/main.py
- backend/routers/pacientes_consultorio.py
- backend/routers/conversao_clinica.py

Rotas movidas para `routers/conversao_clinica.py`:

- POST /consultorio/converter-para-clinico/{paciente_simplificado_id}
- PUT /consultorio/paciente-clinico/{paciente_id}/identificacao
- PUT /consultorio/paciente-clinico/{paciente_id}/dados-clinicos
- GET /consultorio/pacientes-clinicos
- GET /consultorio/buscar-paciente
- GET /consultorio/paciente-clinico/{paciente_id}

Observação: `routers/consultorio_clinico.py` permanece como arquivo antigo/dormante, não incluído no `main.py`. Não deve ser incluído novamente sem revisão, pois contém rotas duplicadas e imports antigos.
