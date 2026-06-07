from pathlib import Path

linhas = Path("routers/consultorio.py").read_text(
    encoding="utf-8"
).splitlines()

alvos = [5099, 5132, 5727, 5812, 6072]

for alvo in alvos:
    print("\n" + "=" * 80)
    print(f"ALVO: {alvo}")
    print("=" * 80)

    inicio = max(1, alvo - 50)
    fim = min(len(linhas), alvo + 50)

    for i in range(inicio, fim):
        linha = linhas[i - 1]

        if (
            linha.lstrip().startswith("@router")
            or linha.lstrip().startswith("def ")
        ):
            print(f"{i}: {linha}")