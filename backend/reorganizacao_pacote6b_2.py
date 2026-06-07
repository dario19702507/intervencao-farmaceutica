"""
Pacote 6B-2 - Remocao do codigo legado de Bioimpedancia do consultorio.py

Objetivo:
- Fazer backup automatico de routers/consultorio.py
- Remover do consultorio.py os blocos de Bioimpedancia ja migrados para routers/bioimpedancia.py
- Nao alterar routers/bioimpedancia.py
- Gerar relatorio local com o que foi removido

Execute dentro da pasta backend:
    python reorganizacao_pacote6b_2.py
"""

from pathlib import Path
from datetime import datetime
import re

BASE = Path.cwd()
CONSULTORIO = BASE / "routers" / "consultorio.py"
BACKUP_DIR = BASE / "backup_reorganizacao_pacote6b_2"
RELATORIO = BASE / "README_reorganizacao_pacote6b_2_resultado.md"

ROTAS_ALVO = [
    ('@router.get("/paciente-simplificado/{paciente_id}/bioimpedancia-historico")', 'historico_bioimpedancia_paciente'),
    ('@router.get("/paciente-simplificado/{paciente_id}/bioimpedancia-comparativo")', 'comparativo_bioimpedancia_paciente'),
    ('@router.get("/bioimpedancia/{bioimpedancia_id}/laudo-pdf")', 'laudo_bioimpedancia_pdf'),
]

FUNCOES_ALVO = [
    "classificar_imc",
    "classificar_gordura_visceral",
    "calcular_bioimpedancia",
]


def fazer_backup():
    BACKUP_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = BACKUP_DIR / f"consultorio_{stamp}.py"
    destino.write_text(CONSULTORIO.read_text(encoding="utf-8"), encoding="utf-8")
    return destino


def encontrar_fim_bloco(texto: str, inicio: int) -> int:
    """Encontra o inicio do proximo decorator @router ou def/class no nivel zero."""
    padrao = re.compile(r"\n(?=@router\.|def |class )")
    match = padrao.search(texto, inicio + 1)
    return match.start() + 1 if match else len(texto)


def remover_bloco_por_decorator(texto: str, decorator: str):
    inicio = texto.find(decorator)
    if inicio == -1:
        return texto, False, 0
    fim = encontrar_fim_bloco(texto, inicio)
    removido = texto[inicio:fim]
    novo = texto[:inicio] + "\n" + texto[fim:]
    return novo, True, removido.count("\n") + 1


def remover_funcao_top_level(texto: str, nome_funcao: str):
    padrao = re.compile(rf"\ndef {re.escape(nome_funcao)}\s*\(")
    match = padrao.search(texto)
    if not match:
        # funcao pode estar no inicio absoluto
        if texto.startswith(f"def {nome_funcao}("):
            inicio = 0
        else:
            return texto, False, 0
    else:
        inicio = match.start() + 1

    fim = encontrar_fim_bloco(texto, inicio)
    removido = texto[inicio:fim]
    novo = texto[:inicio] + "\n" + texto[fim:]
    return novo, True, removido.count("\n") + 1


def main():
    if not CONSULTORIO.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {CONSULTORIO}")

    backup = fazer_backup()
    texto = CONSULTORIO.read_text(encoding="utf-8")
    linhas_antes = texto.count("\n") + 1

    removidos = []
    nao_encontrados = []

    for decorator, nome in ROTAS_ALVO:
        texto, ok, linhas = remover_bloco_por_decorator(texto, decorator)
        if ok:
            removidos.append(("rota", nome, linhas))
        else:
            nao_encontrados.append(("rota", nome))

    for nome in FUNCOES_ALVO:
        texto, ok, linhas = remover_funcao_top_level(texto, nome)
        if ok:
            removidos.append(("funcao", nome, linhas))
        else:
            nao_encontrados.append(("funcao", nome))

    # Limpeza leve de linhas em branco excessivas
    texto = re.sub(r"\n{4,}", "\n\n\n", texto)

    CONSULTORIO.write_text(texto, encoding="utf-8")
    linhas_depois = texto.count("\n") + 1

    rel = []
    rel.append("# Resultado - Reorganizacao Pacote 6B-2\n")
    rel.append(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
    rel.append("## Acoes realizadas\n")
    rel.append(f"- Backup criado em: `{backup}`")
    rel.append("- Remocao cirurgica de blocos de Bioimpedancia ja migrados para `routers/bioimpedancia.py`.")
    rel.append("- Nenhum outro modulo foi alterado.\n")
    rel.append("## Blocos removidos\n")
    if removidos:
        for tipo, nome, linhas in removidos:
            rel.append(f"- {tipo}: `{nome}` ({linhas} linhas)")
    else:
        rel.append("- Nenhum bloco removido.")
    rel.append("\n## Blocos nao encontrados\n")
    if nao_encontrados:
        for tipo, nome in nao_encontrados:
            rel.append(f"- {tipo}: `{nome}`")
    else:
        rel.append("- Todos os blocos alvo foram encontrados.")
    rel.append("\n## Linhas\n")
    rel.append(f"- Antes: {linhas_antes}")
    rel.append(f"- Depois: {linhas_depois}")
    rel.append(f"- Reducao aproximada: {linhas_antes - linhas_depois}")
    rel.append("\n## Validacao recomendada\n")
    rel.append("```bash")
    rel.append("python -m py_compile routers/consultorio.py")
    rel.append("python -m py_compile routers/bioimpedancia.py")
    rel.append("python -m py_compile main.py")
    rel.append("uvicorn main:app --reload")
    rel.append("```")
    rel.append("\n## Rotas a testar no Swagger\n")
    rel.append("- GET `/consultorio/paciente-simplificado/{paciente_id}/bioimpedancia-historico`")
    rel.append("- GET `/consultorio/paciente-simplificado/{paciente_id}/bioimpedancia-comparativo`")
    rel.append("- GET `/consultorio/bioimpedancia/{bioimpedancia_id}/laudo-pdf`")

    RELATORIO.write_text("\n".join(rel), encoding="utf-8")

    print("Pacote 6B-2 concluido.")
    print(f"Backup: {backup}")
    print(f"Relatorio: {RELATORIO}")
    print(f"Linhas: {linhas_antes} -> {linhas_depois}")


if __name__ == "__main__":
    main()
