"""
Pacote de Reorganizacao 1 - Projeto Farmacia Escola

Execute dentro da pasta backend:
    python reorganizacao_pacote1.py
"""

from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path.cwd()
BACKUP_DIR = ROOT / "backup_reorganizacao_pacote1"
MODELS_DIR = ROOT / "models"
SCHEMAS_DIR = ROOT / "schemas"
ROUTERS_DIR = ROOT / "routers"

CONSULTORIO = ROUTERS_DIR / "consultorio.py"
MAIN = ROOT / "main.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_DIR.mkdir(exist_ok=True)

def backup_file(path: Path):
    if path.exists():
        destino = BACKUP_DIR / f"{path.name}.{timestamp}.bak"
        shutil.copy2(path, destino)
        print(f"Backup criado: {destino}")

backup_file(CONSULTORIO)
backup_file(MAIN)

MODELS_DIR.mkdir(exist_ok=True)
SCHEMAS_DIR.mkdir(exist_ok=True)
(MODELS_DIR / "__init__.py").write_text("", encoding="utf-8")
(SCHEMAS_DIR / "__init__.py").write_text("", encoding="utf-8")

models_file = MODELS_DIR / "consultorio_models.py"
if not models_file.exists():
    models_file.write_text("""\
\"\"\"
Modelos SQLAlchemy do modulo Consultorio/Agenda/Pacientes.

Primeira fase: estrutura criada, mas os modelos continuam ativos em routers/consultorio.py.
A migracao definitiva sera feita gradualmente.
\"\"\"
""", encoding="utf-8")
    print(f"Criado: {models_file}")

schemas_file = SCHEMAS_DIR / "consultorio_schemas.py"
if not schemas_file.exists():
    schemas_file.write_text("""\
\"\"\"
Schemas Pydantic do modulo Consultorio/Agenda/Pacientes.

Primeira fase: estrutura criada, mas os schemas continuam ativos em routers/consultorio.py.
A migracao definitiva sera feita gradualmente.
\"\"\"
""", encoding="utf-8")
    print(f"Criado: {schemas_file}")

utils_file = ROUTERS_DIR / "utils_consultorio.py"
if not utils_file.exists():
    utils_file.write_text("""\
\"\"\"
Funcoes auxiliares compartilhadas do modulo Consultorio.

Primeira fase: estrutura criada, mas as funcoes continuam ativas em routers/consultorio.py.
\"\"\"
""", encoding="utf-8")
    print(f"Criado: {utils_file}")

routers = [
    ("agenda.py", "Agenda"),
    ("pacientes.py", "Pacientes"),
    ("notificacoes.py", "Notificacoes"),
    ("auditoria.py", "Auditoria"),
    ("atendimento_rapido.py", "Atendimento Rapido"),
    ("indicadores_consultorio.py", "Indicadores Consultorio"),
]

for nome, tag in routers:
    path = ROUTERS_DIR / nome
    if not path.exists():
        path.write_text(f"""\
\"\"\"
Router {nome}.

Arquivo estrutural criado no Pacote de Reorganizacao 1.
As rotas ainda continuam em routers/consultorio.py.
\"\"\"

from fastapi import APIRouter

router = APIRouter(
    prefix="/consultorio",
    tags=["{tag}"]
)
""", encoding="utf-8")
        print(f"Criado: {path}")

if CONSULTORIO.exists():
    texto = CONSULTORIO.read_text(encoding="utf-8")

    trecho_errado = """    registrar_auditoria(
        db=db,
        current=current,
        modulo="agenda",
        acao="criacao",
        registro_id=evento.id,
        descricao=f"Evento criado para {evento.paciente_nome}"
    )

    db.add(agenda)
    db.commit()
    db.refresh(agenda)
"""

    trecho_correto = """    db.add(agenda)
    db.flush()
    db.refresh(agenda)

    registrar_auditoria(
        db=db,
        current=current,
        modulo="agenda",
        acao="criacao",
        registro_id=agenda.id,
        descricao=f"Evento criado para {agenda.paciente_nome}"
    )

    db.commit()
    db.refresh(agenda)
"""

    if trecho_errado in texto:
        texto = texto.replace(trecho_errado, trecho_correto)
        CONSULTORIO.write_text(texto, encoding="utf-8")
        print("Corrigida auditoria da rota POST /agenda.")
    else:
        print("Trecho evento.id nao encontrado ou ja corrigido.")

print("\nPacote 1 concluido.")
print("Agora rode:")
print("  python -m py_compile routers/consultorio.py")
print("  uvicorn main:app --reload")
