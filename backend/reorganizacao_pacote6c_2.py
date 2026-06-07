from pathlib import Path
from datetime import datetime
import re

BASE = Path.cwd()
CONSULTORIO = BASE / 'routers' / 'consultorio.py'
BACKUP_DIR = BASE / f"backup_reorganizacao_pacote6c_2_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
README = BASE / 'README_reorganizacao_pacote6c_2_resultado.md'

ROTAS_REMOVER = {
    ('post', '/converter-para-clinico/{paciente_simplificado_id}'),
    ('put', '/paciente-clinico/{paciente_id}/identificacao'),
    ('put', '/paciente-clinico/{paciente_id}/dados-clinicos'),
    ('post', '/prontuario/{prontuario_id}/evolucao'),
    ('get', '/prontuario/{prontuario_id}/evolucoes'),
    ('post', '/evolucao/{evolucao_id}/vincular-intervencao'),
    ('post', '/evolucao/{evolucao_id}/desfecho'),
    ('get', '/evolucao/{evolucao_id}/desfechos'),
    ('get', '/dashboard-desfechos'),
    ('get', '/paciente-clinico/{paciente_clinico_id}/timeline'),
    ('get', '/paciente-clinico/{paciente_clinico_id}/prontuario-longitudinal-pdf'),
}

# Rotas adicionais frequentemente migradas para consultorio_clinico.py, mas só removeremos se presentes.
ROTAS_OPCIONAIS = {
    ('post', '/paciente-clinico/{paciente_id}/medicamentos'),
    ('get', '/paciente-clinico/{paciente_id}/medicamentos'),
    ('put', '/medicamentos/{medicamento_id}'),
    ('post', '/paciente-clinico/{paciente_id}/intervencao-farmacoterapia'),
    ('get', '/paciente-clinico/{paciente_id}/intervencoes-farmacoterapia'),
    ('post', '/intervencao-farmacoterapia/{intervencao_id}/desfecho'),
}

TODAS_ROTAS = ROTAS_REMOVER | ROTAS_OPCIONAIS

DECORATOR_RE = re.compile(r'^@router\.(get|post|put|delete|patch)\("([^"]+)"')
ANY_DECORATOR_RE = re.compile(r'^@router\.(get|post|put|delete|patch)\(')
TOP_LEVEL_RE = re.compile(r'^(def |class |@router\.|[A-Za-z_][A-Za-z0-9_]*\s*=)')


def backup():
    BACKUP_DIR.mkdir(exist_ok=True)
    if CONSULTORIO.exists():
        (BACKUP_DIR / 'consultorio.py.bak').write_text(CONSULTORIO.read_text(encoding='utf-8'), encoding='utf-8')


def remover_rotas(texto: str):
    linhas = texto.splitlines(keepends=True)
    removidas = []
    novas = []
    i = 0
    while i < len(linhas):
        linha = linhas[i]
        m = DECORATOR_RE.match(linha.strip())
        if m:
            metodo, rota = m.group(1), m.group(2)
            if (metodo, rota) in TODAS_ROTAS:
                inicio = i
                i += 1
                # inclui decorators adicionais imediatamente acima da função se estiverem juntos? aqui parte do decorator atual.
                while i < len(linhas):
                    prox = linhas[i]
                    # próxima rota marca fim do bloco atual
                    if ANY_DECORATOR_RE.match(prox.strip()):
                        break
                    i += 1
                removidas.append((metodo.upper(), rota, inicio + 1, i))
                continue
        novas.append(linha)
        i += 1
    return ''.join(novas), removidas


def main():
    if not CONSULTORIO.exists():
        raise FileNotFoundError(f'Arquivo não encontrado: {CONSULTORIO}')

    original = CONSULTORIO.read_text(encoding='utf-8')
    linhas_antes = len(original.splitlines())

    backup()
    novo, removidas = remover_rotas(original)
    CONSULTORIO.write_text(novo, encoding='utf-8')

    linhas_depois = len(novo.splitlines())

    rel = []
    rel.append('# Resultado - Reorganizacao Pacote 6C-2\n')
    rel.append(f'Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}\n')
    rel.append('## Objetivo\n')
    rel.append('Remover do `routers/consultorio.py` as rotas clínicas já migradas para `routers/consultorio_clinico.py`.\n')
    rel.append('## Resultado\n')
    rel.append(f'- Linhas antes: {linhas_antes}\n')
    rel.append(f'- Linhas depois: {linhas_depois}\n')
    rel.append(f'- Redução: {linhas_antes - linhas_depois}\n')
    rel.append(f'- Backup: `{BACKUP_DIR.name}`\n')
    rel.append('## Rotas removidas\n')
    if removidas:
        for metodo, rota, ini, fim in removidas:
            rel.append(f'- `{metodo} {rota}` (linhas originais aproximadas {ini}-{fim})\n')
    else:
        rel.append('- Nenhuma rota alvo encontrada para remoção.\n')
    rel.append('\n## Comandos de validação\n')
    rel.append('```bash\n')
    rel.append('python -m py_compile routers/consultorio.py\n')
    rel.append('python -m py_compile routers/consultorio_clinico.py\n')
    rel.append('python -m py_compile main.py\n')
    rel.append('uvicorn main:app --reload\n')
    rel.append('```\n')
    rel.append('\n## Testes sugeridos no Swagger\n')
    rel.append('- `POST /consultorio/converter-para-clinico/{paciente_simplificado_id}`\n')
    rel.append('- `POST /consultorio/prontuario/{prontuario_id}/evolucao`\n')
    rel.append('- `GET /consultorio/prontuario/{prontuario_id}/evolucoes`\n')
    rel.append('- `POST /consultorio/evolucao/{evolucao_id}/desfecho`\n')
    rel.append('- `GET /consultorio/paciente-clinico/{paciente_clinico_id}/timeline`\n')
    README.write_text(''.join(rel), encoding='utf-8')
    print('Pacote 6C-2 executado.')
    print(f'Linhas antes: {linhas_antes}')
    print(f'Linhas depois: {linhas_depois}')
    print(f'Redução: {linhas_antes - linhas_depois}')
    print(f'Relatório: {README.name}')

if __name__ == '__main__':
    main()
