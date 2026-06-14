"""Serviços de migração segura do App de Intervenções.

Passo 13C.0
- carrega exportação JSON do Supabase para tabela de staging;
- valida registros;
- consolida de forma idempotente na tabela oficial `intervencoes`;
- mantém batch_id, origem_sistema e origem_id para rastreabilidade;
- permite rollback lógico da última consolidação importada.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Iterable

from sqlalchemy import text
from sqlalchemy.orm import Session

ORIGEM_SISTEMA_PADRAO = "APP_INTERVENCOES"
STATUS_PENDENTE = "PENDENTE"
STATUS_VALIDADO = "VALIDADO"
STATUS_REJEITADO = "REJEITADO"
STATUS_IMPORTADO = "IMPORTADO"
STATUS_DUPLICADO = "DUPLICADO"

CAMPOS_ESPERADOS = [
    "id",
    "data_atendimento",
    "paciente_nome",
    "data_nascimento",
    "tipo_atendimento",
    "motivo_atendimento",
    "comorbidade",
    "tipos_intervencao",
    "resultado",
    "observacoes",
    "profissional_id",
    "created_at",
    "updated_at",
    "created_by",
    "updated_by",
    "ativo",
    "supervisor_id",
    "motivo_inativacao",
]


def _dialeto(db: Session) -> str:
    try:
        return db.bind.dialect.name
    except Exception:
        return "sqlite"


def _exec(db: Session, sql: str, params: dict[str, Any] | None = None):
    return db.execute(text(sql), params or {})


def garantir_estrutura_migracao(db: Session) -> None:
    """Cria staging/checkpoints e adiciona colunas de rastreabilidade na tabela oficial."""
    dialect = _dialeto(db)

    if dialect == "postgresql":
        _exec(db, """
        CREATE TABLE IF NOT EXISTS migracao_intervencoes_checkpoint (
            id SERIAL PRIMARY KEY,
            checkpoint_id VARCHAR(80) UNIQUE NOT NULL,
            etapa VARCHAR(80) NOT NULL,
            descricao TEXT,
            total_intervencoes INTEGER DEFAULT 0,
            total_staging INTEGER DEFAULT 0,
            total_importadas INTEGER DEFAULT 0,
            criado_por VARCHAR(255),
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        _exec(db, """
        CREATE TABLE IF NOT EXISTS intervencoes_importacao_staging (
            id SERIAL PRIMARY KEY,
            batch_id VARCHAR(80) NOT NULL,
            origem_sistema VARCHAR(80) NOT NULL DEFAULT 'APP_INTERVENCOES',
            origem_id INTEGER NOT NULL,
            status VARCHAR(40) NOT NULL DEFAULT 'PENDENTE',
            erro TEXT,
            payload_json TEXT,
            data_atendimento DATE,
            paciente_nome VARCHAR(255),
            data_nascimento DATE,
            tipo_atendimento VARCHAR(120),
            motivo_atendimento VARCHAR(255),
            comorbidade VARCHAR(255),
            tipos_intervencao TEXT,
            resultado VARCHAR(255),
            observacoes TEXT,
            profissional_id_original INTEGER,
            created_by_original INTEGER,
            updated_by_original INTEGER,
            supervisor_id_original INTEGER,
            ativo BOOLEAN DEFAULT TRUE,
            motivo_inativacao TEXT,
            created_at_original TIMESTAMP,
            updated_at_original TIMESTAMP,
            intervencao_id_destino INTEGER,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        for col_sql in [
            "ALTER TABLE intervencoes ADD COLUMN IF NOT EXISTS origem_sistema VARCHAR(80)",
            "ALTER TABLE intervencoes ADD COLUMN IF NOT EXISTS origem_id INTEGER",
            "ALTER TABLE intervencoes ADD COLUMN IF NOT EXISTS batch_importacao VARCHAR(80)",
            "ALTER TABLE intervencoes ADD COLUMN IF NOT EXISTS data_importacao TIMESTAMP",
        ]:
            _exec(db, col_sql)
    else:
        _exec(db, """
        CREATE TABLE IF NOT EXISTS migracao_intervencoes_checkpoint (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            checkpoint_id TEXT UNIQUE NOT NULL,
            etapa TEXT NOT NULL,
            descricao TEXT,
            total_intervencoes INTEGER DEFAULT 0,
            total_staging INTEGER DEFAULT 0,
            total_importadas INTEGER DEFAULT 0,
            criado_por TEXT,
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        _exec(db, """
        CREATE TABLE IF NOT EXISTS intervencoes_importacao_staging (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id TEXT NOT NULL,
            origem_sistema TEXT NOT NULL DEFAULT 'APP_INTERVENCOES',
            origem_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'PENDENTE',
            erro TEXT,
            payload_json TEXT,
            data_atendimento DATE,
            paciente_nome TEXT,
            data_nascimento DATE,
            tipo_atendimento TEXT,
            motivo_atendimento TEXT,
            comorbidade TEXT,
            tipos_intervencao TEXT,
            resultado TEXT,
            observacoes TEXT,
            profissional_id_original INTEGER,
            created_by_original INTEGER,
            updated_by_original INTEGER,
            supervisor_id_original INTEGER,
            ativo BOOLEAN DEFAULT 1,
            motivo_inativacao TEXT,
            created_at_original DATETIME,
            updated_at_original DATETIME,
            intervencao_id_destino INTEGER,
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
            atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        # SQLite não suporta ADD COLUMN IF NOT EXISTS em versões antigas.
        existing_cols = {row[1] for row in _exec(db, "PRAGMA table_info(intervencoes)").fetchall()}
        add_cols = {
            "origem_sistema": "ALTER TABLE intervencoes ADD COLUMN origem_sistema TEXT",
            "origem_id": "ALTER TABLE intervencoes ADD COLUMN origem_id INTEGER",
            "batch_importacao": "ALTER TABLE intervencoes ADD COLUMN batch_importacao TEXT",
            "data_importacao": "ALTER TABLE intervencoes ADD COLUMN data_importacao DATETIME",
        }
        for col, sql in add_cols.items():
            if col not in existing_cols:
                _exec(db, sql)

    db.commit()


def _parse_date(value: Any) -> date | None:
    if value in (None, "", "null"):
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    text_value = str(value).strip()
    try:
        return date.fromisoformat(text_value[:10])
    except ValueError:
        return None


def _parse_datetime(value: Any) -> datetime | None:
    if value in (None, "", "null"):
        return None
    if isinstance(value, datetime):
        return value
    text_value = str(value).strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text_value)
    except ValueError:
        try:
            return datetime.fromisoformat(text_value.split(".")[0])
        except Exception:
            return None


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return True
    return str(value).strip().lower() in {"true", "1", "sim", "yes"}


def _normalizar_linha(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "origem_id": row.get("id"),
        "data_atendimento": _parse_date(row.get("data_atendimento")),
        "paciente_nome": (row.get("paciente_nome") or "").strip(),
        "data_nascimento": _parse_date(row.get("data_nascimento")),
        "tipo_atendimento": (row.get("tipo_atendimento") or "").strip(),
        "motivo_atendimento": (row.get("motivo_atendimento") or "").strip(),
        "comorbidade": (row.get("comorbidade") or "").strip(),
        "tipos_intervencao": (row.get("tipos_intervencao") or "").strip(),
        "resultado": (row.get("resultado") or "").strip(),
        "observacoes": row.get("observacoes") or "",
        "profissional_id_original": row.get("profissional_id"),
        "created_by_original": row.get("created_by"),
        "updated_by_original": row.get("updated_by"),
        "supervisor_id_original": row.get("supervisor_id"),
        "ativo": _parse_bool(row.get("ativo")),
        "motivo_inativacao": row.get("motivo_inativacao"),
        "created_at_original": _parse_datetime(row.get("created_at")),
        "updated_at_original": _parse_datetime(row.get("updated_at")),
        "payload_json": json.dumps(row, ensure_ascii=False, default=str),
    }


def _validar_linha(n: dict[str, Any]) -> tuple[str, str | None]:
    faltantes = []
    for campo in ["origem_id", "data_atendimento", "paciente_nome", "tipo_atendimento", "motivo_atendimento", "comorbidade", "tipos_intervencao", "resultado"]:
        if not n.get(campo):
            faltantes.append(campo)
    if faltantes:
        return STATUS_REJEITADO, "Campos obrigatórios ausentes/inválidos: " + ", ".join(faltantes)
    return STATUS_VALIDADO, None


def carregar_json_bytes(data: bytes) -> list[dict[str, Any]]:
    payload = json.loads(data.decode("utf-8-sig"))
    if isinstance(payload, dict):
        # Suporta formatos comuns: {"rows": [...]}, {"data": [...]}
        for key in ("rows", "data", "items", "intervencoes"):
            if isinstance(payload.get(key), list):
                payload = payload[key]
                break
    if not isinstance(payload, list):
        raise ValueError("O arquivo JSON precisa conter uma lista de intervenções ou um objeto com chave rows/data/items/intervencoes.")
    return [row for row in payload if isinstance(row, dict)]


def criar_checkpoint(db: Session, etapa: str, descricao: str | None, usuario_email: str | None = None) -> dict[str, Any]:
    garantir_estrutura_migracao(db)
    checkpoint_id = f"chk_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    total_intervencoes = _exec(db, "SELECT COUNT(*) FROM intervencoes").scalar() or 0
    total_staging = _exec(db, "SELECT COUNT(*) FROM intervencoes_importacao_staging").scalar() or 0
    total_importadas = _exec(db, "SELECT COUNT(*) FROM intervencoes WHERE origem_sistema = :origem", {"origem": ORIGEM_SISTEMA_PADRAO}).scalar() or 0
    _exec(db, """
        INSERT INTO migracao_intervencoes_checkpoint
        (checkpoint_id, etapa, descricao, total_intervencoes, total_staging, total_importadas, criado_por)
        VALUES (:checkpoint_id, :etapa, :descricao, :total_intervencoes, :total_staging, :total_importadas, :criado_por)
    """, {
        "checkpoint_id": checkpoint_id,
        "etapa": etapa,
        "descricao": descricao,
        "total_intervencoes": total_intervencoes,
        "total_staging": total_staging,
        "total_importadas": total_importadas,
        "criado_por": usuario_email,
    })
    db.commit()
    return {
        "checkpoint_id": checkpoint_id,
        "etapa": etapa,
        "total_intervencoes": total_intervencoes,
        "total_staging": total_staging,
        "total_importadas": total_importadas,
    }


def importar_para_staging(db: Session, rows: Iterable[dict[str, Any]], usuario_email: str | None = None) -> dict[str, Any]:
    garantir_estrutura_migracao(db)
    batch_id = f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    inseridos = 0
    rejeitados = 0
    duplicados = 0

    for row in rows:
        n = _normalizar_linha(row)
        if not n.get("origem_id"):
            rejeitados += 1
            continue

        exists_staging = _exec(db, """
            SELECT id FROM intervencoes_importacao_staging
            WHERE origem_sistema = :origem AND origem_id = :origem_id
            LIMIT 1
        """, {"origem": ORIGEM_SISTEMA_PADRAO, "origem_id": n["origem_id"]}).first()
        exists_final = _exec(db, """
            SELECT id FROM intervencoes
            WHERE origem_sistema = :origem AND origem_id = :origem_id
            LIMIT 1
        """, {"origem": ORIGEM_SISTEMA_PADRAO, "origem_id": n["origem_id"]}).first()
        if exists_staging or exists_final:
            duplicados += 1
            continue

        status, erro = _validar_linha(n)
        if status == STATUS_REJEITADO:
            rejeitados += 1
        else:
            inseridos += 1

        _exec(db, """
            INSERT INTO intervencoes_importacao_staging
            (batch_id, origem_sistema, origem_id, status, erro, payload_json,
             data_atendimento, paciente_nome, data_nascimento, tipo_atendimento,
             motivo_atendimento, comorbidade, tipos_intervencao, resultado, observacoes,
             profissional_id_original, created_by_original, updated_by_original, supervisor_id_original,
             ativo, motivo_inativacao, created_at_original, updated_at_original)
            VALUES
            (:batch_id, :origem_sistema, :origem_id, :status, :erro, :payload_json,
             :data_atendimento, :paciente_nome, :data_nascimento, :tipo_atendimento,
             :motivo_atendimento, :comorbidade, :tipos_intervencao, :resultado, :observacoes,
             :profissional_id_original, :created_by_original, :updated_by_original, :supervisor_id_original,
             :ativo, :motivo_inativacao, :created_at_original, :updated_at_original)
        """, {
            **n,
            "batch_id": batch_id,
            "origem_sistema": ORIGEM_SISTEMA_PADRAO,
            "status": status,
            "erro": erro,
        })

    db.commit()
    criar_checkpoint(db, "STAGING_IMPORTADO", f"Carga para staging {batch_id}", usuario_email)
    return {"batch_id": batch_id, "inseridos_validos": inseridos, "rejeitados": rejeitados, "duplicados_ignorados": duplicados}


def _usuario_existe(db: Session, user_id: Any) -> bool:
    if user_id is None:
        return False
    return bool(_exec(db, "SELECT id FROM users WHERE id = :id", {"id": user_id}).first())


def _resolver_usuario(db: Session, original_id: Any, fallback_id: int | None, nullable: bool = False) -> int | None:
    if _usuario_existe(db, original_id):
        return int(original_id)
    if nullable:
        return None
    return fallback_id


def consolidar_batch(db: Session, batch_id: str | None, usuario_id: int, usuario_email: str | None = None) -> dict[str, Any]:
    garantir_estrutura_migracao(db)
    params = {"status": STATUS_VALIDADO}
    where_batch = ""
    if batch_id:
        where_batch = " AND batch_id = :batch_id"
        params["batch_id"] = batch_id

    rows = _exec(db, f"""
        SELECT * FROM intervencoes_importacao_staging
        WHERE status = :status {where_batch}
        ORDER BY origem_id
    """, params).mappings().all()

    importados = 0
    duplicados = 0
    rejeitados = 0
    erros = []
    consolidation_batch = f"consol_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

    for row in rows:
        exists_final = _exec(db, """
            SELECT id FROM intervencoes
            WHERE origem_sistema = :origem AND origem_id = :origem_id
            LIMIT 1
        """, {"origem": row["origem_sistema"], "origem_id": row["origem_id"]}).first()
        if exists_final:
            duplicados += 1
            _exec(db, "UPDATE intervencoes_importacao_staging SET status = :status WHERE id = :id", {"status": STATUS_DUPLICADO, "id": row["id"]})
            continue

        profissional_id = _resolver_usuario(db, row["profissional_id_original"], usuario_id)
        created_by = _resolver_usuario(db, row["created_by_original"], usuario_id, nullable=True)
        updated_by = _resolver_usuario(db, row["updated_by_original"], usuario_id, nullable=True)
        supervisor_id = _resolver_usuario(db, row["supervisor_id_original"], None, nullable=True)

        try:
            result = _exec(db, """
                INSERT INTO intervencoes
                (data_atendimento, paciente_nome, data_nascimento, tipo_atendimento,
                 motivo_atendimento, comorbidade, tipos_intervencao, resultado, observacoes,
                 profissional_id, created_by, updated_by, supervisor_id, created_at, updated_at,
                 ativo, motivo_inativacao, origem_sistema, origem_id, batch_importacao, data_importacao)
                VALUES
                (:data_atendimento, :paciente_nome, :data_nascimento, :tipo_atendimento,
                 :motivo_atendimento, :comorbidade, :tipos_intervencao, :resultado, :observacoes,
                 :profissional_id, :created_by, :updated_by, :supervisor_id, :created_at, :updated_at,
                 :ativo, :motivo_inativacao, :origem_sistema, :origem_id, :batch_importacao, :data_importacao)
            """, {
                "data_atendimento": row["data_atendimento"],
                "paciente_nome": row["paciente_nome"],
                "data_nascimento": row["data_nascimento"],
                "tipo_atendimento": row["tipo_atendimento"],
                "motivo_atendimento": row["motivo_atendimento"],
                "comorbidade": row["comorbidade"],
                "tipos_intervencao": row["tipos_intervencao"],
                "resultado": row["resultado"],
                "observacoes": row["observacoes"],
                "profissional_id": profissional_id,
                "created_by": created_by,
                "updated_by": updated_by,
                "supervisor_id": supervisor_id,
                "created_at": row["created_at_original"] or datetime.utcnow(),
                "updated_at": row["updated_at_original"] or datetime.utcnow(),
                "ativo": row["ativo"],
                "motivo_inativacao": row["motivo_inativacao"],
                "origem_sistema": row["origem_sistema"],
                "origem_id": row["origem_id"],
                "batch_importacao": consolidation_batch,
                "data_importacao": datetime.utcnow(),
            })
            # lastrowid funciona no SQLite; em Postgres pode não retornar. Buscamos pelo par origem.
            destino = _exec(db, "SELECT id FROM intervencoes WHERE origem_sistema = :origem AND origem_id = :origem_id", {"origem": row["origem_sistema"], "origem_id": row["origem_id"]}).first()
            destino_id = destino[0] if destino else None
            _exec(db, """
                UPDATE intervencoes_importacao_staging
                SET status = :status, intervencao_id_destino = :destino_id, atualizado_em = CURRENT_TIMESTAMP
                WHERE id = :id
            """, {"status": STATUS_IMPORTADO, "destino_id": destino_id, "id": row["id"]})
            importados += 1
        except Exception as exc:
            rejeitados += 1
            erro = str(exc)[:1000]
            erros.append({"origem_id": row["origem_id"], "erro": erro})
            _exec(db, "UPDATE intervencoes_importacao_staging SET status = :status, erro = :erro WHERE id = :id", {"status": STATUS_REJEITADO, "erro": erro, "id": row["id"]})

    db.commit()
    criar_checkpoint(db, "CONSOLIDADO", f"Consolidação {consolidation_batch}", usuario_email)
    return {"batch_importacao": consolidation_batch, "importados": importados, "duplicados": duplicados, "rejeitados": rejeitados, "erros": erros[:20]}


def dashboard_migracao(db: Session) -> dict[str, Any]:
    garantir_estrutura_migracao(db)
    staging_status = {}
    for row in _exec(db, "SELECT status, COUNT(*) AS total FROM intervencoes_importacao_staging GROUP BY status").mappings().all():
        staging_status[row["status"]] = row["total"]

    total_final_importado = _exec(db, "SELECT COUNT(*) FROM intervencoes WHERE origem_sistema = :origem", {"origem": ORIGEM_SISTEMA_PADRAO}).scalar() or 0
    total_final_ativo = _exec(db, "SELECT COUNT(*) FROM intervencoes WHERE origem_sistema = :origem AND ativo = :ativo", {"origem": ORIGEM_SISTEMA_PADRAO, "ativo": True}).scalar() or 0
    checkpoints = [dict(r) for r in _exec(db, """
        SELECT checkpoint_id, etapa, descricao, total_intervencoes, total_staging, total_importadas, criado_por, criado_em
        FROM migracao_intervencoes_checkpoint
        ORDER BY id DESC LIMIT 10
    """).mappings().all()]

    batches = [dict(r) for r in _exec(db, """
        SELECT batch_id, status, COUNT(*) AS total
        FROM intervencoes_importacao_staging
        GROUP BY batch_id, status
        ORDER BY batch_id DESC
        LIMIT 50
    """).mappings().all()]

    return {
        "origem_sistema": ORIGEM_SISTEMA_PADRAO,
        "staging_por_status": staging_status,
        "total_importado_final": total_final_importado,
        "total_importado_ativo": total_final_ativo,
        "ultimos_checkpoints": checkpoints,
        "batches": batches,
    }



def listar_checkpoints_migracao(db: Session, limite: int = 50) -> dict[str, Any]:
    """Lista checkpoints da migração para o painel administrativo."""
    garantir_estrutura_migracao(db)
    limite = max(1, min(int(limite or 50), 200))
    rows = _exec(db, f"""
        SELECT checkpoint_id, etapa, descricao, total_intervencoes, total_staging,
               total_importadas, criado_por, criado_em
        FROM migracao_intervencoes_checkpoint
        ORDER BY id DESC
        LIMIT {limite}
    """).mappings().all()
    return {"total": len(rows), "checkpoints": [dict(r) for r in rows]}


def avaliar_consistencia_migracao(db: Session) -> dict[str, Any]:
    """Executa validações não destrutivas sobre staging e dados já importados."""
    garantir_estrutura_migracao(db)

    def count(sql: str, params: dict[str, Any] | None = None) -> int:
        return int(_exec(db, sql, params or {}).scalar() or 0)

    problemas = []

    regras = [
        {
            "codigo": "STAGING_SEM_PACIENTE",
            "descricao": "Registros em staging sem nome de paciente.",
            "criticidade": "CRITICA",
            "total": count("""
                SELECT COUNT(*) FROM intervencoes_importacao_staging
                WHERE paciente_nome IS NULL OR TRIM(paciente_nome) = ''
            """),
            "acao_sugerida": "Revisar o arquivo exportado antes da consolidação.",
        },
        {
            "codigo": "STAGING_SEM_DATA",
            "descricao": "Registros em staging sem data de atendimento válida.",
            "criticidade": "CRITICA",
            "total": count("""
                SELECT COUNT(*) FROM intervencoes_importacao_staging
                WHERE data_atendimento IS NULL
            """),
            "acao_sugerida": "Corrigir a data de atendimento no sistema de origem ou rejeitar o registro.",
        },
        {
            "codigo": "STAGING_SEM_TIPO_INTERVENCAO",
            "descricao": "Registros em staging sem tipo de intervenção.",
            "criticidade": "MODERADA",
            "total": count("""
                SELECT COUNT(*) FROM intervencoes_importacao_staging
                WHERE tipos_intervencao IS NULL OR TRIM(tipos_intervencao) = ''
            """),
            "acao_sugerida": "Padronizar a classificação antes de usar em relatórios assistenciais.",
        },
        {
            "codigo": "STAGING_REJEITADOS",
            "descricao": "Registros rejeitados na validação de staging.",
            "criticidade": "CRITICA",
            "total": count("""
                SELECT COUNT(*) FROM intervencoes_importacao_staging
                WHERE status = :status
            """, {"status": STATUS_REJEITADO}),
            "acao_sugerida": "Abrir a rastreabilidade e corrigir a origem do problema antes de consolidar.",
        },
        {
            "codigo": "STAGING_DUPLICADOS",
            "descricao": "Registros duplicados detectados por origem_sistema + origem_id.",
            "criticidade": "INFORMATIVA",
            "total": count("""
                SELECT COUNT(*) FROM intervencoes_importacao_staging
                WHERE status = :status
            """, {"status": STATUS_DUPLICADO}),
            "acao_sugerida": "Conferir se são importações repetidas esperadas.",
        },
        {
            "codigo": "FINAL_SEM_RASTREABILIDADE",
            "descricao": "Registros finais oriundos do App sem origem_id ou batch de importação.",
            "criticidade": "MODERADA",
            "total": count("""
                SELECT COUNT(*) FROM intervencoes
                WHERE origem_sistema = :origem
                  AND (origem_id IS NULL OR batch_importacao IS NULL OR TRIM(batch_importacao) = '')
            """, {"origem": ORIGEM_SISTEMA_PADRAO}),
            "acao_sugerida": "Verificar se houve importação manual fora do fluxo de migração segura.",
        },
    ]

    for regra in regras:
        if regra["total"] > 0:
            problemas.append(regra)

    resumo = {
        "criticos": sum(1 for p in problemas if p["criticidade"] == "CRITICA"),
        "moderados": sum(1 for p in problemas if p["criticidade"] == "MODERADA"),
        "informativos": sum(1 for p in problemas if p["criticidade"] == "INFORMATIVA"),
        "registros_afetados": sum(int(p["total"] or 0) for p in problemas),
    }

    return {
        "ok": resumo["criticos"] == 0,
        "resumo": resumo,
        "problemas": problemas,
        "mensagem": "Validação concluída. Nenhum dado foi alterado.",
    }


def rastreabilidade_migracao(db: Session, limite: int = 100, status: str | None = None, batch_id: str | None = None) -> dict[str, Any]:
    """Consulta registros de staging e destino para auditoria da integração."""
    garantir_estrutura_migracao(db)
    limite = max(1, min(int(limite or 100), 500))
    params: dict[str, Any] = {}
    filtros = []
    if status:
        filtros.append("s.status = :status")
        params["status"] = status
    if batch_id:
        filtros.append("s.batch_id = :batch_id")
        params["batch_id"] = batch_id
    where = "WHERE " + " AND ".join(filtros) if filtros else ""

    rows = _exec(db, f"""
        SELECT s.id, s.batch_id, s.origem_sistema, s.origem_id, s.status, s.erro,
               s.paciente_nome, s.data_atendimento, s.tipo_atendimento,
               s.motivo_atendimento, s.comorbidade, s.tipos_intervencao, s.resultado,
               s.ativo, s.motivo_inativacao, s.intervencao_id_destino,
               s.criado_em, s.atualizado_em,
               i.batch_importacao, i.data_importacao
        FROM intervencoes_importacao_staging s
        LEFT JOIN intervencoes i ON i.id = s.intervencao_id_destino
        {where}
        ORDER BY s.id DESC
        LIMIT {limite}
    """, params).mappings().all()

    return {
        "total_retornado": len(rows),
        "limite": limite,
        "filtros": {"status": status, "batch_id": batch_id},
        "registros": [dict(r) for r in rows],
    }


def resumo_integracao_intervencoes(db: Session) -> dict[str, Any]:
    """Retorna resumo consolidado para o Painel de Integração das Intervenções."""
    garantir_estrutura_migracao(db)
    dashboard = dashboard_migracao(db)
    consistencia = avaliar_consistencia_migracao(db)
    checkpoints = listar_checkpoints_migracao(db, limite=5)

    total_staging = sum(int(v or 0) for v in dashboard.get("staging_por_status", {}).values())
    ultimo_checkpoint = checkpoints["checkpoints"][0] if checkpoints["checkpoints"] else None
    ultimo_batch = dashboard.get("batches", [None])[0] if dashboard.get("batches") else None

    return {
        "origem_sistema": ORIGEM_SISTEMA_PADRAO,
        "total_staging": total_staging,
        "total_importado_final": dashboard.get("total_importado_final", 0),
        "total_importado_ativo": dashboard.get("total_importado_ativo", 0),
        "staging_por_status": dashboard.get("staging_por_status", {}),
        "ultimo_checkpoint": ultimo_checkpoint,
        "ultimo_batch": ultimo_batch,
        "consistencia": consistencia.get("resumo", {}),
        "fluxo_recomendado": [
            "Manter o App de Intervenções como sistema mestre durante a transição.",
            "Importar novos lotes para staging.",
            "Validar consistência e rastreabilidade.",
            "Consolidar somente após conferência administrativa.",
            "Manter checkpoints antes e depois de cada consolidação.",
        ],
    }


def rollback_batch_importacao(db: Session, batch_importacao: str, usuario_email: str | None = None) -> dict[str, Any]:
    """Remove da tabela oficial apenas registros importados por um batch de consolidação.

    Preserva staging e checkpoints para auditoria. Não afeta registros manuais.
    """
    garantir_estrutura_migracao(db)
    ids = [row[0] for row in _exec(db, "SELECT id FROM intervencoes WHERE batch_importacao = :batch", {"batch": batch_importacao}).fetchall()]
    if not ids:
        return {"removidos": 0, "batch_importacao": batch_importacao}

    _exec(db, "DELETE FROM intervencoes WHERE batch_importacao = :batch", {"batch": batch_importacao})
    _exec(db, """
        UPDATE intervencoes_importacao_staging
        SET status = :status, intervencao_id_destino = NULL, atualizado_em = CURRENT_TIMESTAMP
        WHERE intervencao_id_destino IS NOT NULL
    """, {"status": STATUS_VALIDADO})
    db.commit()
    criar_checkpoint(db, "ROLLBACK", f"Rollback do batch {batch_importacao}", usuario_email)
    return {"removidos": len(ids), "batch_importacao": batch_importacao}
