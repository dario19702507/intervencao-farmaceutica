import os
import sqlite3
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

SQLITE_DB = "intervencoes.db"
POSTGRES_URL = os.getenv("DATABASE_URL")

if not POSTGRES_URL:
    raise Exception("DATABASE_URL não encontrado.")

TABELAS = [
    "users",
    "intervencoes",
    "pacientes_agenda",
    "pacientes_simplificados",
    "atendimentos_rapidos",
    "afericoes_pa",
    "glicemias_capilares",
    "bioimpedancias",
    "picos_fluxo",
    "pacientes_clinicos",
    "prontuarios_clinicos",
    "evolucoes_clinicas",
    "desfechos_clinicos",
    "medicamentos_uso",
    "intervencoes_farmacoterapia",
    "desfechos_intervencoes_farmacoterapia",
    "evolucoes_farmaceuticas",
    "planos_cuidado",
    "agenda_integrada",
    "capacidade_agenda",
    "configuracoes_sistema",
    "notificacoes_agenda",
    "resolucoes_alertas_clinicos",
    "auditoria_sistema",
]


BOOLEAN_COLUNAS = {
    "ativo",
    "renovado",
    "notificar_whatsapp",
    "convertido_para_consultorio",
    "aceite_verbal",
    "necessidade_retorno",
    "resolucao_problema",
    "necessidade_encaminhamento",
    "uso_continuo",
    "aceita_pelo_paciente",
    "necessidade_nova_intervencao",
    "pessoa_com_deficiencia",
    "vacinacao_influenza",
    "vacinacao_covid",
    "notificacao_vespera_enviada",
    "notificacao_dia_enviada",
    "notificacao_ultimo_mes_enviada",
    "notificacao_penultimo_mes_enviada",
    "notificacao_extra_enviada",
    "notificacao_atraso_disp_enviada",
}

def normalizar_valor(valor, coluna=None):
    if isinstance(valor, bytes):
        return valor.decode("utf-8", errors="ignore")

    if coluna in BOOLEAN_COLUNAS:
        if valor is None:
            return None
        return bool(valor)

    return valor

def tabela_existe_sqlite(conn, tabela):
    cur = conn.cursor()
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (tabela,)
    )
    return cur.fetchone() is not None


def obter_colunas_sqlite(conn, tabela):
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({tabela})")
    return [linha["name"] for linha in cur.fetchall()]


def obter_colunas_postgres(engine, tabela):
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = :tabela
                ORDER BY ordinal_position
            """),
            {"tabela": tabela}
        )
        return [row[0] for row in result.fetchall()]


def contar_postgres(engine, tabela):
    with engine.connect() as conn:
        return conn.execute(
            text(f"SELECT COUNT(*) FROM {tabela}")
        ).scalar()


def migrar_tabela(sqlite_conn, pg_engine, tabela):
    if not tabela_existe_sqlite(sqlite_conn, tabela):
        print(f"- {tabela}: não existe no SQLite, ignorada.")
        return

    colunas_sqlite = obter_colunas_sqlite(sqlite_conn, tabela)
    colunas_pg = obter_colunas_postgres(pg_engine, tabela)

    colunas = [
        c for c in colunas_sqlite
        if c in colunas_pg
    ]

    if not colunas:
        print(f"- {tabela}: nenhuma coluna compatível, ignorada.")
        return

    cursor = sqlite_conn.cursor()
    cursor.execute(f"SELECT {', '.join(colunas)} FROM {tabela}")
    linhas = cursor.fetchall()

    if not linhas:
        print(f"- {tabela}: 0 registros.")
        return

    colunas_sql = ", ".join(colunas)
    valores_sql = ", ".join([f":{c}" for c in colunas])

    if tabela == "users":
        conflito = "email"
    else:
        conflito = "id"

    sql = text(
        f"""
        INSERT INTO {tabela} ({colunas_sql})
        VALUES ({valores_sql})
        ON CONFLICT ({conflito}) DO NOTHING
        """
    )

    inseridos = 0

    with pg_engine.begin() as conn:
        for linha in linhas:
            dados = {
                c: normalizar_valor(linha[c], c)
                for c in colunas
            }

            result = conn.execute(sql, dados)

            if result.rowcount:
                inseridos += 1

    total_pg = contar_postgres(pg_engine, tabela)

    print(
        f"- {tabela}: {inseridos} inseridos | total PostgreSQL: {total_pg}"
    )


def ajustar_sequences(pg_engine):
    print("\nAjustando sequences...")

    with pg_engine.begin() as conn:
        for tabela in TABELAS:
            colunas = obter_colunas_postgres(pg_engine, tabela)

            if "id" not in colunas:
                continue

            try:
                conn.execute(
                    text(f"""
                        SELECT setval(
                            pg_get_serial_sequence('{tabela}', 'id'),
                            COALESCE((SELECT MAX(id) FROM {tabela}), 1),
                            true
                        )
                    """)
                )
                print(f"- {tabela}: sequence ajustada")
            except Exception as e:
                print(f"- {tabela}: sequence não ajustada ({e})")


def main():
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_conn.row_factory = sqlite3.Row

    pg_engine = create_engine(POSTGRES_URL)

    print("✓ SQLite conectado")
    print("✓ PostgreSQL conectado")
    print("\nIniciando migração...\n")

    for tabela in TABELAS:
        migrar_tabela(sqlite_conn, pg_engine, tabela)

    ajustar_sequences(pg_engine)

    sqlite_conn.close()

    print("\nMigração concluída.")


if __name__ == "__main__":
    main()