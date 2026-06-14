Passo 7G - Router de Farmacoterapia

Substituir somente os arquivos do backend:
- backend/main.py
- backend/routers/consultorio.py
- backend/routers/farmacoterapia.py

Rotas movidas para backend/routers/farmacoterapia.py:
- GET  /consultorio/paciente-clinico/{paciente_id}/evolucao-farmacoterapeutica
- GET  /consultorio/paciente-clinico/{paciente_id}/sugestoes-plano-cuidado
- GET  /consultorio/dashboard-farmacoterapeutico
- POST /consultorio/paciente-clinico/{paciente_id}/medicamento
- GET  /consultorio/paciente-clinico/{paciente_id}/medicamentos
- GET  /consultorio/paciente-clinico/{paciente_id}/avaliacao-polifarmacia
- POST /consultorio/paciente-clinico/{paciente_id}/intervencao-farmacoterapia
- GET  /consultorio/paciente-clinico/{paciente_id}/intervencoes-farmacoterapia
- POST /consultorio/intervencao-farmacoterapia/{intervencao_id}/desfecho
- GET  /consultorio/intervencao-farmacoterapia/{intervencao_id}/desfechos

consultorio.py: 3313 -> 3123 linhas.

Após substituir, executar:
uvicorn main:app --reload
