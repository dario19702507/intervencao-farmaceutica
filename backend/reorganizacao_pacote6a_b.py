from pathlib import Path
from datetime import datetime
import re

BASE = Path.cwd()
CONSULTORIO = BASE / 'routers' / 'consultorio.py'
BACKUP_DIR = BASE / f'backup_reorganizacao_pacote6a_b_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
RELATORIO = BASE / 'README_reorganizacao_pacote6a_b_resultado.md'

ROTAS_REMOVER = {
    ('post', '/paciente-simplificado'),
    ('post', '/atendimento-rapido'),
    ('post', '/afericao-pa'),
    ('post', '/glicemia'),
    ('post', '/bioimpedancia'),
    ('post', '/pico-fluxo'),
    ('get', '/pacientes-simplificados'),
    ('get', '/atendimentos-rapidos'),
    ('get', '/atendimento-rapido/{atendimento_id}/detalhes'),
    ('get', '/paciente-simplificado/{paciente_id}'),
}

# Algumas versões podem usar nomes de parâmetros diferentes.
ROTAS_PREFIXO_EXATO = {
    ('get', '/atendimento-rapido/{'),
    ('get', '/paciente-simplificado/{'),
}

DECORATOR_RE = re.compile(r'^@router\.(get|post|put|delete|patch)\("([^"]+)"')


def encontrar_blocos_rotas(texto: str):
    linhas = texto.splitlines(keepends=True)
    blocos = []
    i = 0
    while i < len(linhas):
        m = DECORATOR_RE.match(linhas[i].strip())
        if not m:
            i += 1
            continue

        metodo, path = m.group(1), m.group(2)
        remover = (metodo, path) in ROTAS_REMOVER
        if not remover:
            for metodo_pref, path_pref in ROTAS_PREFIXO_EXATO:
                if metodo == metodo_pref and path.startswith(path_pref):
                    # Evita remover PDF/declaracao ou outros sub-recursos que não foram migrados
                    if 'declaracao-pdf' not in path and 'bioimpedancia-historico' not in path:
                        remover = True
                    break

        if not remover:
            i += 1
            continue

        inicio = i
        j = i + 1
        while j < len(linhas):
            stripped = linhas[j].strip()
            # Nova rota começa outro bloco.
            if DECORATOR_RE.match(stripped):
                break
            # Uma classe/model/schema nova no nível raiz também encerra bloco, por segurança.
            if linhas[j] and not linhas[j].startswith((' ', '\t', '\n', '\r')):
                if stripped.startswith(('class ', 'def ')) and j > inicio + 1:
                    # Se for def no nível raiz, pode ser o próprio def da rota: já passou.
                    # Não quebra quando estamos dentro do bloco da rota porque funções internas são indentadas.
                    break
            j += 1

        blocos.append({
            'metodo': metodo.upper(),
            'path': path,
            'inicio': inicio,
            'fim': j,
            'linhas': j - inicio,
        })
        i = j

    return blocos, linhas


def remover_blocos(texto: str, blocos, linhas):
    remover_indices = set()
    for b in blocos:
        remover_indices.update(range(b['inicio'], b['fim']))
    novas = [linha for idx, linha in enumerate(linhas) if idx not in remover_indices]
    # Limpa excesso de linhas em branco consecutivas.
    saida = ''.join(novas)
    saida = re.sub(r'\n{4,}', '\n\n\n', saida)
    return saida


def main():
    if not CONSULTORIO.exists():
        raise SystemExit(f'Arquivo não encontrado: {CONSULTORIO}')

    texto = CONSULTORIO.read_text(encoding='utf-8')
    blocos, linhas = encontrar_blocos_rotas(texto)

    BACKUP_DIR.mkdir(exist_ok=True)
    backup_path = BACKUP_DIR / 'consultorio.py.bak'
    backup_path.write_text(texto, encoding='utf-8')

    novo_texto = remover_blocos(texto, blocos, linhas)
    CONSULTORIO.write_text(novo_texto, encoding='utf-8')

    rel = []
    rel.append('# Resultado - Reorganizacao Pacote 6A-B\n')
    rel.append(f'Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}\n')
    rel.append('## Acoes realizadas\n')
    rel.append(f'- Backup criado em `{backup_path}`.\n')
    rel.append('- Remocao cirurgica das rotas antigas de Servicos Rapidos em `routers/consultorio.py`.\n')
    rel.append('- As rotas devem permanecer ativas pelo novo modulo `routers/servicos_rapidos.py`.\n')
    rel.append('\n## Rotas removidas\n')
    if blocos:
        for b in blocos:
            rel.append(f'- `{b["metodo"]} {b["path"]}` ({b["linhas"]} linhas)\n')
    else:
        rel.append('- Nenhuma rota alvo encontrada.\n')
    rel.append('\n## Contagem de linhas\n')
    rel.append(f'- Antes: {len(linhas)}\n')
    rel.append(f'- Depois: {len(novo_texto.splitlines())}\n')
    rel.append('\n## Validacao recomendada\n')
    rel.append('```bash\n')
    rel.append('python -m py_compile routers/consultorio.py\n')
    rel.append('python -m py_compile routers/servicos_rapidos.py\n')
    rel.append('python -m py_compile main.py\n')
    rel.append('uvicorn main:app --reload\n')
    rel.append('```\n')
    rel.append('\n## Testes Swagger\n')
    rel.append('- `POST /consultorio/paciente-simplificado`\n')
    rel.append('- `POST /consultorio/atendimento-rapido`\n')
    rel.append('- `POST /consultorio/afericao-pa`\n')
    rel.append('- `POST /consultorio/glicemia`\n')
    rel.append('- `POST /consultorio/bioimpedancia`\n')
    rel.append('- `POST /consultorio/pico-fluxo`\n')
    rel.append('- `GET /consultorio/pacientes-simplificados`\n')
    rel.append('- `GET /consultorio/atendimentos-rapidos`\n')

    RELATORIO.write_text(''.join(rel), encoding='utf-8')

    print('Pacote 6A-B executado.')
    print(f'Rotas removidas: {len(blocos)}')
    print(f'Linhas antes: {len(linhas)}')
    print(f'Linhas depois: {len(novo_texto.splitlines())}')
    print(f'Relatorio: {RELATORIO}')

if __name__ == '__main__':
    main()
