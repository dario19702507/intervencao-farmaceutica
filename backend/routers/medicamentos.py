"""Catálogo simplificado de medicamentos.

Passo 15D.7A - Base de medicamentos ANVISA simplificada.

A implementação reutiliza a tabela existente ``catalogo_medicamentos`` para evitar
criar uma segunda base concorrente de medicamentos. O catálogo é destinado à
padronização futura da farmacoterapia, consultório e intervenções.
"""

import csv
import io
import re
import unicodedata
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, text
from sqlalchemy.orm import Session

from database import engine
from models.consultorio_models import BaseConsultorio, CatalogoMedicamento
from routers.consultorio import get_current_user_consultorio, get_db_consultorio

BaseConsultorio.metadata.create_all(bind=engine)


def _garantir_colunas_catalogo_medicamentos() -> None:
    """Adiciona campos novos de forma idempotente em bases já existentes."""
    colunas = {
        "via_administracao": "VARCHAR",
        "codigo_atc": "VARCHAR",
        "fonte_dados": "VARCHAR",
        "nome_normalizado": "VARCHAR",
    }
    try:
        with engine.begin() as conn:
            dialecto = engine.dialect.name
            if dialecto == "sqlite":
                existentes = {linha[1] for linha in conn.execute(text("PRAGMA table_info(catalogo_medicamentos)")).fetchall()}
                for coluna, tipo in colunas.items():
                    if coluna not in existentes:
                        conn.execute(text(f"ALTER TABLE catalogo_medicamentos ADD COLUMN {coluna} {tipo}"))
            else:
                for coluna, tipo in colunas.items():
                    conn.execute(text(f"ALTER TABLE catalogo_medicamentos ADD COLUMN IF NOT EXISTS {coluna} {tipo}"))
    except Exception:
        # Não impede a inicialização; os endpoints revelarão eventual inconsistência.
        pass


_garantir_colunas_catalogo_medicamentos()

router = APIRouter(prefix="/medicamentos", tags=["Catálogo de Medicamentos"])


class MedicamentoBase(BaseModel):
    principio_ativo: str = Field(..., min_length=2)
    concentracao: Optional[str] = None
    forma_farmaceutica: Optional[str] = None
    via_administracao: Optional[str] = None
    classe_terapeutica: Optional[str] = None
    registro_anvisa: Optional[str] = None
    codigo_atc: Optional[str] = None
    nome_comercial: Optional[str] = None
    laboratorio: Optional[str] = None
    apresentacao: Optional[str] = None
    componente: Optional[str] = None
    observacoes: Optional[str] = None
    ativo: bool = True


class MedicamentoCreate(MedicamentoBase):
    pass


class MedicamentoUpdate(BaseModel):
    principio_ativo: Optional[str] = None
    concentracao: Optional[str] = None
    forma_farmaceutica: Optional[str] = None
    via_administracao: Optional[str] = None
    classe_terapeutica: Optional[str] = None
    registro_anvisa: Optional[str] = None
    codigo_atc: Optional[str] = None
    nome_comercial: Optional[str] = None
    laboratorio: Optional[str] = None
    apresentacao: Optional[str] = None
    componente: Optional[str] = None
    observacoes: Optional[str] = None
    ativo: Optional[bool] = None


def _normalizar(valor: Any) -> str:
    texto = str(valor or "").strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    texto = re.sub(r"\s+", " ", texto)
    return texto.lower().strip()


def _limpar(valor: Any) -> Optional[str]:
    if valor is None:
        return None
    texto = str(valor).strip()
    if texto in {"", "None", "nan", "NaN", "NaT"}:
        return None
    return texto


def _somente_digitos(valor: Any) -> Optional[str]:
    texto = re.sub(r"\D+", "", str(valor or ""))
    return texto or None


def _descricao_apresentacao(dados: Dict[str, Any]) -> str:
    partes = [
        dados.get("principio_ativo"),
        dados.get("concentracao"),
        dados.get("forma_farmaceutica"),
        dados.get("via_administracao"),
    ]
    return " - ".join([str(p).strip() for p in partes if p]) or str(dados.get("principio_ativo") or "Medicamento")


def _to_dict(med: CatalogoMedicamento) -> Dict[str, Any]:
    return {
        "id": med.id,
        "principio_ativo": med.principio_ativo or med.farmaco,
        "farmaco": med.farmaco,
        "nome_comercial": med.nome_comercial,
        "concentracao": med.concentracao,
        "forma_farmaceutica": med.forma_farmaceutica,
        "via_administracao": getattr(med, "via_administracao", None),
        "apresentacao": med.apresentacao,
        "classe_terapeutica": med.classe_terapeutica,
        "registro_anvisa": med.registro_anvisa,
        "codigo_atc": getattr(med, "codigo_atc", None),
        "laboratorio": med.laboratorio,
        "componente": med.componente,
        "fonte_dados": getattr(med, "fonte_dados", None),
        "ativo": med.ativo,
        "observacoes": med.observacoes,
        "criado_em": med.criado_em.isoformat() if med.criado_em else None,
        "atualizado_em": med.atualizado_em.isoformat() if med.atualizado_em else None,
        "descricao_completa": med.descricao_completa,
    }


def _aplicar_payload(med: CatalogoMedicamento, payload: Dict[str, Any], fonte: str = "manual") -> CatalogoMedicamento:
    principio = _limpar(payload.get("principio_ativo") or payload.get("farmaco"))
    if not principio:
        raise HTTPException(status_code=400, detail="Princípio ativo é obrigatório")

    med.principio_ativo = principio
    med.farmaco = principio
    med.nome_comercial = _limpar(payload.get("nome_comercial"))
    med.concentracao = _limpar(payload.get("concentracao"))
    med.forma_farmaceutica = _limpar(payload.get("forma_farmaceutica"))
    med.apresentacao = _limpar(payload.get("apresentacao")) or _descricao_apresentacao(payload)
    med.laboratorio = _limpar(payload.get("laboratorio"))
    med.registro_anvisa = _somente_digitos(payload.get("registro_anvisa")) or _limpar(payload.get("registro_anvisa"))
    med.classe_terapeutica = _limpar(payload.get("classe_terapeutica"))
    med.componente = _limpar(payload.get("componente"))
    med.observacoes = _limpar(payload.get("observacoes"))
    med.ativo = bool(payload.get("ativo", True))
    med.atualizado_em = datetime.utcnow()

    if hasattr(med, "via_administracao"):
        med.via_administracao = _limpar(payload.get("via_administracao"))
    if hasattr(med, "codigo_atc"):
        med.codigo_atc = _limpar(payload.get("codigo_atc"))
    if hasattr(med, "fonte_dados"):
        med.fonte_dados = fonte
    if hasattr(med, "nome_normalizado"):
        med.nome_normalizado = _normalizar(" ".join([str(x or "") for x in [
            med.principio_ativo,
            med.nome_comercial,
            med.concentracao,
            med.forma_farmaceutica,
            getattr(med, "via_administracao", None),
            med.registro_anvisa,
        ]]))
    return med


@router.get("")
def listar_medicamentos(
    q: Optional[str] = Query(None, description="Busca por princípio ativo, nome comercial, apresentação ou registro"),
    ativo: Optional[bool] = Query(True),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    query = db.query(CatalogoMedicamento)
    if ativo is not None:
        query = query.filter(CatalogoMedicamento.ativo == ativo)
    if q:
        termo = f"%{q.strip()}%"
        query = query.filter(or_(
            CatalogoMedicamento.farmaco.ilike(termo),
            CatalogoMedicamento.principio_ativo.ilike(termo),
            CatalogoMedicamento.nome_comercial.ilike(termo),
            CatalogoMedicamento.apresentacao.ilike(termo),
            CatalogoMedicamento.registro_anvisa.ilike(termo),
        ))
    total = query.count()
    itens = query.order_by(CatalogoMedicamento.farmaco.asc()).offset(offset).limit(limit).all()
    return {"total": total, "limit": limit, "offset": offset, "medicamentos": [_to_dict(item) for item in itens]}


@router.get("/buscar")
def buscar_medicamentos(
    termo: str = Query(..., min_length=2),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    termo_like = f"%{termo.strip()}%"
    itens = (
        db.query(CatalogoMedicamento)
        .filter(CatalogoMedicamento.ativo == True)
        .filter(or_(
            CatalogoMedicamento.farmaco.ilike(termo_like),
            CatalogoMedicamento.principio_ativo.ilike(termo_like),
            CatalogoMedicamento.nome_comercial.ilike(termo_like),
            CatalogoMedicamento.apresentacao.ilike(termo_like),
            CatalogoMedicamento.registro_anvisa.ilike(termo_like),
        ))
        .order_by(CatalogoMedicamento.farmaco.asc())
        .limit(limit)
        .all()
    )
    return {"medicamentos": [_to_dict(item) for item in itens]}


@router.get("/resumo")
def resumo_catalogo(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    total = db.query(CatalogoMedicamento).count()
    ativos = db.query(CatalogoMedicamento).filter(CatalogoMedicamento.ativo == True).count()
    registros_anvisa = db.query(CatalogoMedicamento).filter(CatalogoMedicamento.registro_anvisa.isnot(None)).count()
    formas = (
        db.query(CatalogoMedicamento.forma_farmaceutica, func.count(CatalogoMedicamento.id))
        .filter(CatalogoMedicamento.ativo == True)
        .group_by(CatalogoMedicamento.forma_farmaceutica)
        .order_by(func.count(CatalogoMedicamento.id).desc())
        .limit(10)
        .all()
    )
    return {
        "total": total,
        "ativos": ativos,
        "inativos": max(total - ativos, 0),
        "com_registro_anvisa": registros_anvisa,
        "formas_frequentes": [{"forma_farmaceutica": item[0] or "Não informada", "total": item[1]} for item in formas],
    }


@router.get("/{medicamento_id}")
def obter_medicamento(
    medicamento_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    med = db.query(CatalogoMedicamento).filter(CatalogoMedicamento.id == medicamento_id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medicamento não encontrado")
    return _to_dict(med)


@router.post("")
def criar_medicamento(
    dados: MedicamentoCreate,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    payload = dados.model_dump()
    registro = _somente_digitos(payload.get("registro_anvisa")) or _limpar(payload.get("registro_anvisa"))
    if registro:
        existente = db.query(CatalogoMedicamento).filter(CatalogoMedicamento.registro_anvisa == registro).first()
        if existente:
            raise HTTPException(status_code=409, detail="Já existe medicamento com este registro ANVISA")
    med = _aplicar_payload(CatalogoMedicamento(), payload, fonte="manual")
    db.add(med)
    db.commit()
    db.refresh(med)
    return _to_dict(med)


@router.put("/{medicamento_id}")
def atualizar_medicamento(
    medicamento_id: int,
    dados: MedicamentoUpdate,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    med = db.query(CatalogoMedicamento).filter(CatalogoMedicamento.id == medicamento_id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medicamento não encontrado")
    payload = {k: v for k, v in dados.model_dump().items() if v is not None}
    _aplicar_payload(med, payload, fonte=getattr(med, "fonte_dados", None) or "manual")
    db.commit()
    db.refresh(med)
    return _to_dict(med)


@router.post("/{medicamento_id}/ativar")
def ativar_inativar_medicamento(
    medicamento_id: int,
    ativo: bool = Query(...),
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    med = db.query(CatalogoMedicamento).filter(CatalogoMedicamento.id == medicamento_id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medicamento não encontrado")
    med.ativo = ativo
    med.atualizado_em = datetime.utcnow()
    db.commit()
    db.refresh(med)
    return _to_dict(med)


ALIASES_IMPORTACAO = {
    # Inclui tanto cabeçalhos com espaço quanto cabeçalhos técnicos com underscore.
    # Ex.: principio_ativo;concentracao;forma_farmaceutica;via_administracao
    "principio_ativo": ["principio_ativo", "principio ativo", "princípio ativo", "substancia", "substância", "farmaco", "fármaco", "nome substancia"],
    "nome_comercial": ["nome_comercial", "nome comercial", "produto", "medicamento", "nome produto", "nome do produto"],
    "concentracao": ["concentracao", "concentração", "concentracao medicamento", "concentração medicamento"],
    "forma_farmaceutica": ["forma_farmaceutica", "forma farmaceutica", "forma farmacêutica", "forma", "forma farmac"],
    "via_administracao": ["via_administracao", "via administracao", "via administração", "via", "via de administracao", "via de administração"],
    "registro_anvisa": ["registro_anvisa", "registro anvisa", "registro", "numero registro", "número registro"],
    "classe_terapeutica": ["classe_terapeutica", "classe terapeutica", "classe terapêutica", "classe", "categoria"],
    "codigo_atc": ["codigo_atc", "codigo atc", "código atc", "atc"],
    "laboratorio": ["laboratorio", "laboratório", "empresa", "empresa detentora", "detentor registro"],
    "apresentacao": ["apresentacao", "apresentação"],
    "componente": ["componente", "componente assistencia", "componente assistência"],
}


def _mapear_cabecalho(cabecalho: List[str]) -> Dict[str, int]:
    normalizados = {_normalizar(nome): idx for idx, nome in enumerate(cabecalho)}
    mapa: Dict[str, int] = {}
    for campo, aliases in ALIASES_IMPORTACAO.items():
        for alias in aliases:
            if alias in normalizados:
                mapa[campo] = normalizados[alias]
                break
    return mapa


def _ler_csv_upload(conteudo: bytes) -> List[Dict[str, Any]]:
    texto = conteudo.decode("utf-8-sig", errors="ignore")
    amostra = texto[:2048]
    try:
        dialect = csv.Sniffer().sniff(amostra, delimiters=";,\t,")
    except Exception:
        dialect = csv.excel
        dialect.delimiter = ";"
    reader = csv.reader(io.StringIO(texto), dialect)
    linhas = list(reader)
    if not linhas:
        return []
    mapa = _mapear_cabecalho(linhas[0])
    registros = []
    for linha in linhas[1:]:
        if not any(_limpar(item) for item in linha):
            continue
        item = {}
        for campo, idx in mapa.items():
            item[campo] = _limpar(linha[idx]) if idx < len(linha) else None
        registros.append(item)
    return registros


@router.post("/importar-csv")
async def importar_csv_catalogo(
    file: UploadFile = File(...),
    substituir_existentes: bool = Query(False, description="Atualiza registros existentes com mesmo registro ANVISA"),
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    nome = (file.filename or "").lower()
    if not nome.endswith((".csv", ".txt")):
        raise HTTPException(status_code=400, detail="Envie um arquivo CSV ou TXT delimitado por ; ou ,")

    conteudo = await file.read()
    linhas = _ler_csv_upload(conteudo)
    if not linhas:
        raise HTTPException(status_code=400, detail="Arquivo sem registros válidos ou cabeçalho não reconhecido")

    criados = 0
    atualizados = 0
    ignorados = 0
    erros: List[Dict[str, Any]] = []

    for idx, dados in enumerate(linhas, start=2):
        try:
            principio = _limpar(dados.get("principio_ativo") or dados.get("nome_comercial"))
            if not principio:
                ignorados += 1
                erros.append({"linha": idx, "erro": "Sem princípio ativo ou nome de medicamento"})
                continue
            dados["principio_ativo"] = principio
            registro = _somente_digitos(dados.get("registro_anvisa")) or _limpar(dados.get("registro_anvisa"))

            existente = None
            if registro:
                existente = db.query(CatalogoMedicamento).filter(CatalogoMedicamento.registro_anvisa == registro).first()
            if not existente:
                # fallback evita duplicação grosseira quando a base não possui registro ANVISA
                existente = (
                    db.query(CatalogoMedicamento)
                    .filter(func.lower(CatalogoMedicamento.farmaco) == principio.lower())
                    .filter(CatalogoMedicamento.concentracao == _limpar(dados.get("concentracao")))
                    .filter(CatalogoMedicamento.forma_farmaceutica == _limpar(dados.get("forma_farmaceutica")))
                    .first()
                )

            if existente:
                if substituir_existentes:
                    _aplicar_payload(existente, dados, fonte="importacao_csv")
                    atualizados += 1
                else:
                    ignorados += 1
                continue

            med = _aplicar_payload(CatalogoMedicamento(), dados, fonte="importacao_csv")
            db.add(med)
            criados += 1
        except Exception as exc:
            ignorados += 1
            erros.append({"linha": idx, "erro": str(exc)[:200]})

    db.commit()
    return {
        "arquivo": file.filename,
        "total_linhas": len(linhas),
        "criados": criados,
        "atualizados": atualizados,
        "ignorados": ignorados,
        "erros": erros[:50],
    }
