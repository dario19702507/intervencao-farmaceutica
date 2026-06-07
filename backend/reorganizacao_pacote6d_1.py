from pathlib import Path
from datetime import datetime
import re

BASE = Path.cwd()
ROUTERS = BASE / 'routers'
CONSULTORIO = ROUTERS / 'consultorio.py'
FARMACO = ROUTERS / 'farmacoterapia.py'
MAIN = BASE / 'main.py'

stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
backup_dir = BASE / f'backup_reorganizacao_pacote6d_1_{stamp}'
backup_dir.mkdir(exist_ok=True)

if CONSULTORIO.exists():
    (backup_dir / f'consultorio_{stamp}.py').write_text(CONSULTORIO.read_text(encoding='utf-8'), encoding='utf-8')
if MAIN.exists():
    (backup_dir / f'main_{stamp}.py').write_text(MAIN.read_text(encoding='utf-8'), encoding='utf-8')

consultorio_text = CONSULTORIO.read_text(encoding='utf-8')

def extract_blocks(text, names):
    blocks = []
    for name in names:
        # Capture function block beginning at decorator or def until next top-level decorator/def/class or EOF
        pattern = re.compile(rf'(?ms)(^@router\.(?:get|post|put|delete|patch)\([^\n]*\)\n(?:.*?\n)*?^def\s+{re.escape(name)}\s*\([^\n]*\):.*?)(?=^@router\.|^def\s+|^class\s+|\Z)')
        m = pattern.search(text)
        if m:
            blocks.append(m.group(1).rstrip() + '\n')
            continue
        pattern2 = re.compile(rf'(?ms)(^def\s+{re.escape(name)}\s*\([^\n]*\):.*?)(?=^@router\.|^def\s+|^class\s+|\Z)')
        m = pattern2.search(text)
        if m:
            blocks.append(m.group(1).rstrip() + '\n')
    return blocks

# Most likely pharmacotherapy functions/route handlers from previous architecture.
TARGET_NAMES = [
    'cadastrar_medicamento_uso',
    'listar_medicamentos_uso',
    'atualizar_medicamento_uso',
    'inativar_medicamento_uso',
    'criar_intervencao_farmacoterapia',
    'listar_intervencoes_farmacoterapia',
    'criar_desfecho_intervencao_farmacoterapia',
    'listar_desfechos_intervencao_farmacoterapia',
    'avaliar_polifarmacia',
    'evolucao_farmacoterapeutica',
    'dashboard_farmacoterapia',
    'relatorio_farmacoterapia_pdf',
]

blocks = extract_blocks(consultorio_text, TARGET_NAMES)

# Fallback: also collect route blocks whose path/name contains farmacoterapia, medicamento, polifarmacia.
for m in re.finditer(r'(?ms)(^@router\.(?:get|post|put|delete|patch)\([^\n]*(?:farmacoterapia|medicamento|polifarmacia)[^\n]*\)\n(?:.*?\n)*?^def\s+\w+\s*\([^\n]*\):.*?)(?=^@router\.|^def\s+|^class\s+|\Z)', consultorio_text, re.I):
    block = m.group(1).rstrip() + '\n'
    if block not in blocks:
        blocks.append(block)

header = '''from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, date
from typing import Optional

# Import provisório de modelos, schemas e dependências do módulo legado.
# No pacote 6D-2/6E poderemos mover essas dependências para models/schemas/utils.
from routers.consultorio import (
    get_db_consultorio,
    get_current_user_consultorio,
    exigir_farmaceutico_ou_admin,
    exigir_pode_registrar,
    MedicamentoUso,
    IntervencaoFarmacoterapia,
    DesfechoIntervencaoFarmacoterapia,
    PacienteClinico,
    MedicamentoUsoCreate,
    IntervencaoFarmacoterapiaCreate,
    DesfechoIntervencaoFarmacoterapiaCreate,
)

router = APIRouter(
    prefix="/consultorio",
    tags=["Farmacoterapia"]
)

'''

if not blocks:
    body = '''# Nenhum bloco foi extraído automaticamente.
# Este arquivo foi criado para receber as rotas de farmacoterapia.
# Rode: findstr /N /I "farmacoterapia medicamento polifarmacia" routers\\consultorio.py
# e migre os blocos manualmente, se necessário.
'''
else:
    body = '\n\n'.join(blocks)

FARMACO.write_text(header + body, encoding='utf-8')

main_text = MAIN.read_text(encoding='utf-8')
if 'from routers.farmacoterapia import router as farmacoterapia_router' not in main_text:
    # insert near other router imports
    main_text = main_text.replace('from routers.bioimpedancia import router as bioimpedancia_router\n', 'from routers.bioimpedancia import router as bioimpedancia_router\nfrom routers.farmacoterapia import router as farmacoterapia_router\n') if 'from routers.bioimpedancia import router as bioimpedancia_router\n' in main_text else main_text.replace('from routers.consultorio import router as consultorio_router\n', 'from routers.consultorio import router as consultorio_router\nfrom routers.farmacoterapia import router as farmacoterapia_router\n')
if 'app.include_router(farmacoterapia_router)' not in main_text:
    # put after bioimpedancia router if present, otherwise after consultorio router
    if 'app.include_router(bioimpedancia_router)\n' in main_text:
        main_text = main_text.replace('app.include_router(bioimpedancia_router)\n', 'app.include_router(bioimpedancia_router)\napp.include_router(farmacoterapia_router)\n')
    else:
        main_text = main_text.replace('app.include_router(consultorio_router)\n', 'app.include_router(consultorio_router)\napp.include_router(farmacoterapia_router)\n')
MAIN.write_text(main_text, encoding='utf-8')

report = BASE / 'README_reorganizacao_pacote6d_1_resultado.md'
report.write_text(f'''# Resultado - Reorganizacao Pacote 6D-1

Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

## Ações realizadas

- Backup criado em `{backup_dir.name}`.
- Criado/atualizado `routers/farmacoterapia.py`.
- Incluído `farmacoterapia_router` no `main.py`, se ainda não existia.
- Nenhuma rota foi removida de `routers/consultorio.py` nesta etapa.

## Blocos extraídos

{len(blocks)} bloco(s) copiado(s) para `routers/farmacoterapia.py`.

## Próximos testes

```bash
python -m py_compile routers/farmacoterapia.py
python -m py_compile main.py
uvicorn main:app --reload
```

Depois valide no Swagger se as rotas de farmacoterapia aparecem e respondem.
''', encoding='utf-8')

print('Pacote 6D-1 concluído.')
print(f'Backup: {backup_dir}')
print(f'Blocos extraídos: {len(blocks)}')
print(f'Relatório: {report}')
