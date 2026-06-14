# Passo 15A.0 — Identidade institucional e documentos de impressão

## Conteúdo

Esta entrega implementa os últimos ajustes documentais antes da preparação para homologação multiusuário.

### Inclui

1. Logos da Farmácia Escola e UFMS no sistema:
   - `frontend/public/logos/farmacia_escola.png`
   - `frontend/public/logos/ufms.png`
   - cabeçalho do sistema atualizado
   - tela de login atualizada

2. Logos e cabeçalho institucional no backend:
   - `backend/assets/logos/farmacia_escola.png`
   - `backend/assets/logos/ufms.png`
   - novo serviço institucional: `backend/services/documentos_institucionais.py`

3. Declaração de serviço farmacêutico com resultado do serviço prestado:
   - PA: sistólica/diastólica, FC e classificação
   - glicemia: valor, condição e classificação
   - bioimpedância: peso, IMC, gordura corporal e classificação
   - pico de fluxo: valor, percentual previsto e classificação

4. Relatórios e documentos institucionais:
   - cabeçalho com logos nos PDFs principais
   - rodapé com data/hora de emissão e responsável
   - planilhas gerenciais com identificação institucional e logos quando suportado

5. Impressões clínicas do consultório:
   - prontuário PDF
   - plano de cuidado PDF
   - evoluções clínicas PDF
   - orientações farmacêuticas PDF

6. Central de relatórios/impressões:
   - links para relatórios gerenciais
   - consultório
   - serviços rápidos
   - analytics

## Arquivos alterados/adicionados

### Backend

- `backend/assets/logos/farmacia_escola.png`
- `backend/assets/logos/ufms.png`
- `backend/services/documentos_institucionais.py`
- `backend/services/relatorios_consultorio.py`
- `backend/routers/consultorio.py`
- `backend/routers/relatorios_gerenciais.py`
- `backend/schemas/consultorio_schemas.py`

### Frontend

- `frontend/public/logos/farmacia_escola.png`
- `frontend/public/logos/ufms.png`
- `frontend/src/components/layout/Topbar.jsx`
- `frontend/src/pages/login.jsx`
- `frontend/src/pages/consultorio/Consultorio.jsx`
- `frontend/src/pages/relatorios/Relatorios.jsx`
- `frontend/src/pages/relatorios_gerenciais/RelatoriosGerenciais.jsx`
- `frontend/src/style.css`

## Novos endpoints de impressão clínica

```txt
GET /consultorio/paciente-clinico/{id}/plano-cuidado-pdf
GET /consultorio/paciente-clinico/{id}/evolucoes-clinicas-pdf
GET /consultorio/paciente-clinico/{id}/orientacoes-farmaceuticas-pdf
```

## Como aplicar

Extraia o conteúdo do ZIP na raiz do projeto, substituindo os arquivos existentes.

Depois rode:

```cmd
cd backend
python -m py_compile services\documentos_institucionais.py services\relatorios_consultorio.py routers\consultorio.py routers\relatorios_gerenciais.py schemas\consultorio_schemas.py
```

Depois suba o backend:

```cmd
uvicorn main:app --reload
```

Em outro terminal:

```cmd
pytest -q tests
python tests\smoke_tests.py
```

No frontend:

```cmd
cd frontend
npm run build
npm run dev
```

## Observação

A estrutura foi mantida conservadora: não altera banco, não cria migrations e não muda regras clínicas. A entrega foca em identidade institucional, documentos gerados e impressão clínica.
