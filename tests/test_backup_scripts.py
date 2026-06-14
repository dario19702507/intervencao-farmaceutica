import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(filename):
    path = ROOT / filename
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_backup_database_script_importavel():
    module = load_module("backup_database.py")
    assert hasattr(module, "criar_backup")
    assert hasattr(module, "backup_sqlite")


def test_restore_database_script_importavel():
    module = load_module("restore_database.py")
    assert hasattr(module, "restaurar_sqlite")
    assert hasattr(module, "validar_sqlite_backup")
