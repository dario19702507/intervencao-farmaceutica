from pathlib import Path
from datetime import datetime
import re

BASE = Path.cwd()
CONSULTORIO = BASE / 'routers' / 'consultorio.py'
BACKUP_DIR = BASE / f'backup_reorganizacao_pacote5b_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
RELATORIO = BASE / 'README_reorganizacao_pacote5b_resultado.md'

ROTAS_REMOVER = [
    ('get', '/pacientes'),
    ('get', '/pacientes/{paciente_id}'),
    ('put', '/pacientes/{paciente_id}'),
    ('get', '/pacientes/{paciente_id}/historico'),
    ('post', '/agenda/pacientes'),
    ('get', '/agenda/pacientes'),
    ('get', '/agenda/pacientes/buscar'),
    ('put', '/agenda/pacientes/{paciente_id}'),
]

DECORATOR_RE = re.compile(r'^@router\.(get|post|put|delete|patch)\("([^"]+)"\)')
ANY_ROUTE_RE = re.compile(r'^@router\.(get|post|put|delete|patch)\(')


def find_function_end(lines, start_idx):
    """Return index just after a route function block.

    start_idx points to first decorator line. We scan until the next top-level
    route decorator or end of file. This is conservative for this project, where
    route functions are top-level and consecutive.
    """
    i = start_idx + 1
    while i < len(lines):
        if ANY_ROUTE_RE.match(lines[i]):
            return i
        i += 1
    return len(lines)


def main():
    if not CONSULTORIO.exists():
        raise SystemExit(f'Arquivo não encontrado: {CONSULTORIO}')

    BACKUP_DIR.mkdir(exist_ok=True)
    backup_path = BACKUP_DIR / 'consultorio.py.bak'
    original = CONSULTORIO.read_text(encoding='utf-8')
    backup_path.write_text(original, encoding='utf-8')

    lines = original.splitlines(keepends=True)
    removidos = []
    ranges_to_remove = []

    i = 0
    while i < len(lines):
        m = DECORATOR_RE.match(lines[i])
        if not m:
            i += 1
            continue

        method, path = m.group(1), m.group(2)
        if (method, path) in ROTAS_REMOVER:
            end = find_function_end(lines, i)
            snippet = ''.join(lines[i:min(end, i+8)])
            ranges_to_remove.append((i, end))
            removidos.append({
                'method': method.upper(),
                'path': path,
                'start_line': i + 1,
                'end_line': end,
                'preview': snippet.strip().splitlines()[0] if snippet.strip() else ''
            })
            i = end
        else:
            i += 1

    if ranges_to_remove:
        new_lines = []
        cursor = 0
        for start, end in ranges_to_remove:
            new_lines.extend(lines[cursor:start])
            # keep a compact marker for future review
            new_lines.append(f'\n# Rota migrada para routers/pacientes.py removida no pacote 5B: linhas originais {start+1}-{end}\n\n')
            cursor = end
        new_lines.extend(lines[cursor:])
        CONSULTORIO.write_text(''.join(new_lines), encoding='utf-8')

    report = []
    report.append('# Resultado - Reorganizacao Pacote 5B\n')
    report.append(f'Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}\n')
    report.append('## Objetivo\n')
    report.append('Remover do `routers/consultorio.py` as rotas de pacientes já migradas para `routers/pacientes.py`.\n')
    report.append('## Backup\n')
    report.append(f'- `{backup_path}`\n')
    report.append('## Rotas removidas\n')
    if removidos:
        for r in removidos:
            report.append(f'- `{r[method] if False else r["method"]} {r["path"]}` - linhas originais {r["start_line"]}-{r["end_line"]}\n')
    else:
        report.append('- Nenhuma rota alvo encontrada. Talvez já tenham sido removidas.\n')
    report.append('\n## Validação recomendada\n')
    report.append('```bash\n')
    report.append('python -m py_compile routers/consultorio.py\n')
    report.append('python -m py_compile routers/pacientes.py\n')
    report.append('python -m py_compile main.py\n')
    report.append('uvicorn main:app --reload\n')
    report.append('```\n')
    report.append('\n## Testes funcionais\n')
    report.append('- `GET /consultorio/pacientes`\n')
    report.append('- `GET /consultorio/pacientes/{id}`\n')
    report.append('- `PUT /consultorio/pacientes/{id}`\n')
    report.append('- `GET /consultorio/pacientes/{id}/historico`\n')
    report.append('- `GET /consultorio/agenda/pacientes/buscar?termo=AAA`\n')

    RELATORIO.write_text(''.join(report), encoding='utf-8')
    print('Pacote 5B concluído.')
    print(f'Rotas removidas: {len(removidos)}')
    print(f'Relatório: {RELATORIO}')
    print(f'Backup: {backup_path}')


if __name__ == '__main__':
    main()
