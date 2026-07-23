"""Migrações simples do banco de dados.

Este arquivo concentra pequenos ajustes incrementais de estrutura que antes ficavam
misturados no main.py. Ele não substitui uma ferramenta formal de migração, como
Alembic, mas mantém compatibilidade com o estágio atual do projeto.
"""

from database import Base, engine


def _adicionar_coluna_se_nao_existir(conn, tabela: str, definicao_coluna: str) -> None:
    """Executa ALTER TABLE ignorando erro quando a coluna já existe."""
    try:
        conn.exec_driver_sql(f"ALTER TABLE {tabela} ADD COLUMN {definicao_coluna}")
        conn.commit()
    except Exception:
        conn.rollback()


def aplicar_migracoes_simples() -> None:
    """Cria tabelas e aplica migrações simples compatíveis com SQLite/PostgreSQL."""
    Base.metadata.create_all(bind=engine)

    with engine.connect() as conn:
        _adicionar_coluna_se_nao_existir(
            conn,
            "users",
            "categoria_profissional VARCHAR DEFAULT 'Farmacêutico'",
        )
        _adicionar_coluna_se_nao_existir(conn, "intervencoes", "created_by INTEGER")
        _adicionar_coluna_se_nao_existir(conn, "intervencoes", "updated_by INTEGER")
        _adicionar_coluna_se_nao_existir(conn, "intervencoes", "ativo BOOLEAN DEFAULT TRUE")
        _adicionar_coluna_se_nao_existir(conn, "intervencoes", "supervisor_id INTEGER")
        _adicionar_coluna_se_nao_existir(conn, "intervencoes", "motivo_inativacao TEXT")

        # Passo 14E.2B — farmacoterapia estruturada e seleção assistida de medicamentos
        _adicionar_coluna_se_nao_existir(conn, "medicamentos_uso", "catalogo_medicamento_id INTEGER")
        _adicionar_coluna_se_nao_existir(conn, "medicamentos_uso", "frequencia_uso VARCHAR")
        _adicionar_coluna_se_nao_existir(conn, "medicamentos_uso", "horarios_uso TEXT")
        _adicionar_coluna_se_nao_existir(conn, "medicamentos_uso", "uso_se_necessario BOOLEAN DEFAULT FALSE")
        _adicionar_coluna_se_nao_existir(conn, "medicamentos_uso", "uso_off_label VARCHAR DEFAULT 'NAO_AVALIADO' NOT NULL")
        _adicionar_coluna_se_nao_existir(conn, "medicamentos_uso", "justificativa_off_label TEXT")
        _adicionar_coluna_se_nao_existir(conn, "medicamentos_uso", "evidencia_off_label TEXT")

        # Passo 14E.2C.5B.1 — ciclo de vida da farmacoterapia
        _adicionar_coluna_se_nao_existir(conn, "medicamentos_uso", "status_farmacoterapia VARCHAR DEFAULT 'EM_USO'")
        _adicionar_coluna_se_nao_existir(conn, "medicamentos_uso", "data_status DATETIME")
        _adicionar_coluna_se_nao_existir(conn, "medicamentos_uso", "motivo_status VARCHAR")
        _adicionar_coluna_se_nao_existir(conn, "medicamentos_uso", "tipo_suspensao VARCHAR")
        _adicionar_coluna_se_nao_existir(conn, "medicamentos_uso", "observacao_status TEXT")
        _adicionar_coluna_se_nao_existir(conn, "medicamentos_uso", "substituido_por_medicamento_id INTEGER")
        _adicionar_coluna_se_nao_existir(conn, "medicamentos_uso", "prm_relacionado_id INTEGER")
        _adicionar_coluna_se_nao_existir(conn, "medicamentos_uso", "intervencao_relacionada_id INTEGER")

        _adicionar_coluna_se_nao_existir(conn, "catalogo_medicamentos", "principio_ativo VARCHAR")
        _adicionar_coluna_se_nao_existir(conn, "catalogo_medicamentos", "nome_comercial VARCHAR")
        _adicionar_coluna_se_nao_existir(conn, "catalogo_medicamentos", "laboratorio VARCHAR")
        _adicionar_coluna_se_nao_existir(conn, "catalogo_medicamentos", "registro_anvisa VARCHAR")
        _adicionar_coluna_se_nao_existir(conn, "catalogo_medicamentos", "classe_terapeutica VARCHAR")


        # Passo 14E.2C.3A — metas terapêuticas estruturadas
        _adicionar_coluna_se_nao_existir(conn, "metas_terapeuticas", "intervencao_farmacoterapia_id INTEGER")
        _adicionar_coluna_se_nao_existir(conn, "metas_terapeuticas", "categoria VARCHAR")
        _adicionar_coluna_se_nao_existir(conn, "metas_terapeuticas", "subcategoria VARCHAR")
        _adicionar_coluna_se_nao_existir(conn, "metas_terapeuticas", "valor_atual VARCHAR")
        _adicionar_coluna_se_nao_existir(conn, "metas_terapeuticas", "data_inicial DATE")
        _adicionar_coluna_se_nao_existir(conn, "metas_terapeuticas", "data_prevista DATE")
        _adicionar_coluna_se_nao_existir(conn, "metas_terapeuticas", "data_conclusao DATE")
        _adicionar_coluna_se_nao_existir(conn, "metas_terapeuticas", "origem VARCHAR DEFAULT 'CONSULTA'")
        _adicionar_coluna_se_nao_existir(conn, "metas_terapeuticas", "codigo_catalogo VARCHAR")
        _adicionar_coluna_se_nao_existir(conn, "metas_terapeuticas", "versao_catalogo VARCHAR DEFAULT '2026.06'")

