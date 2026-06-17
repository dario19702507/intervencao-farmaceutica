# 15D.8D — Correção de endpoints opcionais do Consultório

## Objetivo
Evitar que falhas ou lentidão em endpoints complementares impeçam a abertura do prontuário.

## Ajustes
- `services/atencao_farmaceutica.py`: limita a varredura de pacientes e evita que falha em um paciente derrube toda a central.
- `CuidadoFarmaceutico.jsx`: troca `Promise.all` por `Promise.allSettled`, reduz limite inicial e permite carregamento parcial.
- `Consultorio.jsx`: medicamentos e demais blocos opcionais passam a falhar de forma não bloqueante.

## Validação
1. Abrir Consultório → Pacientes e prontuários.
2. Buscar paciente por nome/CPF/CNS/telefone.
3. Abrir prontuário.
4. Confirmar que o prontuário abre mesmo se algum bloco complementar estiver temporariamente indisponível.
5. Verificar no Swagger:
   - GET /consultorio/atencao-farmaceutica/dashboard
   - GET /consultorio/atencao-farmaceutica/pendencias?limite=80&limite_pacientes=80
   - GET /consultorio/paciente-clinico/{id}/medicamentos
