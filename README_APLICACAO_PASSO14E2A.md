# Passo 14E.2A — Centro de Atenção Farmacêutica / Motor de Pendências Assistenciais

## Objetivo

Implementar um motor de pendências para transformar a timeline, a farmacoterapia estruturada, os documentos, a agenda e o cuidado farmacêutico em uma fila ativa de trabalho farmacêutico.

A primeira versão apenas identifica, classifica e prioriza pendências. Nenhum PRM, meta, plano, documento, retirada ou processo é encerrado automaticamente.

## Novos endpoints

- `GET /consultorio/atencao-farmaceutica/opcoes`
- `GET /consultorio/atencao-farmaceutica/dashboard`
- `GET /consultorio/atencao-farmaceutica/pendencias`
- `GET /consultorio/atencao-farmaceutica/paciente/{paciente_id}/pendencias`

## Categorias avaliadas

- Assistencial: PRM aberto, intervenção sem desfecho, meta vencida, ação do plano atrasada.
- CEAF: laudo vencido, laudo próximo do vencimento, retirada atrasada.
- Documental: pacote incompleto, documento rejeitado, documento sem conferência.
- Farmacoterapêutica: polifarmácia, complexidade alta/muito alta, adesão baixa, horários não estruturados, medicamento não padronizado, medicamento de alto risco.

## Arquivos alterados/adicionados

- `backend/services/atencao_farmaceutica.py`
- `backend/routers/atencao_farmaceutica.py`
- `backend/main.py`
- `frontend/src/pages/consultorio/CuidadoFarmaceutico.jsx`
- `frontend/src/pages/consultorio/CuidadoFarmaceutico.css`
- `frontend/src/navigation/catalog.jsx`
- `tests/smoke_tests.py`
- `tests/test_atencao_farmaceutica.py`

## Validação

Após aplicar os arquivos, execute:

```cmd
pytest -q tests
python tests\smoke_tests.py
```

No frontend:

```cmd
cd frontend
npm install
npm run dev
```

A tela ficará disponível em:

```txt
/atendimento/centro-atencao
```

Também há redirects legados:

```txt
/cuidado-farmaceutico
/centro-atencao-farmaceutica
```
