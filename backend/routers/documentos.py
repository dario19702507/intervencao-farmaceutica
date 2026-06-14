"""Rotas de gestao documental do Consultorio Farmaceutico.

Passo 11A: infraestrutura documental sem OCR.
Passo 11B: validade documental integrada às notificações internas.
- Upload vinculado ao paciente clinico
- Listagem por paciente
- Download seguro
- Atualizacao de metadados
- Inativacao logica
- Dashboard de vencimentos
- Notificações automáticas para receitas/laudos a vencer ou vencidos
"""

from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import engine
from models.consultorio_models import (
    BaseConsultorio,
    DocumentoPaciente,
    HistoricoVigenciaDocumento,
    HistoricoStatusDocumento,
    PacienteClinico,
    NotificacaoInterna,
    ProcessoDocumental,
)
from routers.consultorio import get_db_consultorio, get_current_user_consultorio, exigir_farmaceutico_ou_admin
from schemas.consultorio_schemas import DocumentoPacienteUpdate, VigenciaDocumentoUpdate
from services.documentos_vigencia import (
    OPERACOES_VIGENCIA,
    STATUS_VIGENCIA,
    aplicar_vigencia_calculada,
    criar_evento_notificacao_whatsapp_documento,
    recalcular_fluxo_documento,
    registrar_historico_vigencia,
    status_vigencia,
)

BaseConsultorio.metadata.create_all(bind=engine)


def _adicionar_coluna_documento_se_nao_existir(tabela: str, definicao_coluna: str) -> None:
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql(f"ALTER TABLE {tabela} ADD COLUMN {definicao_coluna}")
            conn.commit()
    except Exception:
        pass


_adicionar_coluna_documento_se_nao_existir("documentos_pacientes", "operacao_vigencia VARCHAR")
_adicionar_coluna_documento_se_nao_existir("documentos_pacientes", "vigencia_inicio DATE")
_adicionar_coluna_documento_se_nao_existir("documentos_pacientes", "vigencia_fim DATE")
_adicionar_coluna_documento_se_nao_existir("documentos_pacientes", "vigencia_status VARCHAR")
_adicionar_coluna_documento_se_nao_existir("documentos_pacientes", "vigencia_origem_calculo VARCHAR")
_adicionar_coluna_documento_se_nao_existir("documentos_pacientes", "vigencia_editada_manualmente BOOLEAN DEFAULT 0")
_adicionar_coluna_documento_se_nao_existir("documentos_pacientes", "motivo_alteracao_vigencia TEXT")
_adicionar_coluna_documento_se_nao_existir("documentos_pacientes", "processo_documental_id INTEGER")
_adicionar_coluna_documento_se_nao_existir("documentos_pacientes", "status_documental VARCHAR DEFAULT 'RECEBIDO'")
_adicionar_coluna_documento_se_nao_existir("documentos_pacientes", "status_documental_motivo TEXT")
_adicionar_coluna_documento_se_nao_existir("documentos_pacientes", "status_documental_atualizado_por VARCHAR")
_adicionar_coluna_documento_se_nao_existir("documentos_pacientes", "status_documental_atualizado_em TIMESTAMP")

router = APIRouter(prefix="/consultorio", tags=["Documentos"])

TIPOS_DOCUMENTO = [
    "RECEITA",
    "LAUDO",
    "EXAME",
    "DOCUMENTO_PESSOAL",
    "TERMO",
    "OUTRO",
]

STATUS_DOCUMENTO = ["ATIVO", "VENCIDO", "SUBSTITUIDO", "CANCELADO"]
STATUS_DOCUMENTAL = ["PENDENTE", "RECEBIDO", "VALIDADO", "REJEITADO", "SUBSTITUIDO"]
ORIGENS_DOCUMENTO = ["UPLOAD_MANUAL", "SISTEMA", "WHATSAPP", "IMPORTACAO"]

BASE_UPLOAD_DIR = Path(__file__).resolve().parents[1] / "uploads" / "documentos"
BASE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class StatusDocumentalUpdate(BaseModel):
    status_documental: str
    motivo: str
    observacao: Optional[str] = None


def _normalizar_status_documental(valor: str) -> str:
    status = (valor or "").strip().upper()
    if status not in STATUS_DOCUMENTAL:
        raise HTTPException(status_code=400, detail=f"Status documental inválido. Use: {', '.join(STATUS_DOCUMENTAL)}")
    return status


def _registrar_historico_status_documental(
    db: Session,
    doc: DocumentoPaciente,
    status_anterior: Optional[str],
    status_novo: str,
    motivo: str,
    observacao: Optional[str],
    usuario: Optional[str],
    origem: str = "MANUAL",
) -> HistoricoStatusDocumento:
    historico = HistoricoStatusDocumento(
        documento_id=doc.id,
        paciente_id=doc.paciente_id,
        processo_documental_id=getattr(doc, "processo_documental_id", None),
        status_anterior=status_anterior,
        status_novo=status_novo,
        motivo=motivo,
        observacao=observacao,
        usuario=usuario,
        origem=origem,
        criado_em=datetime.utcnow(),
    )
    db.add(historico)
    return historico


def _serializar_documento(doc: DocumentoPaciente):
    return {
        "id": doc.id,
        "paciente_id": doc.paciente_id,
        "processo_documental_id": getattr(doc, "processo_documental_id", None),
        "tipo_documento": doc.tipo_documento,
        "titulo": doc.titulo,
        "descricao": doc.descricao,
        "nome_arquivo_original": doc.nome_arquivo_original,
        "content_type": doc.content_type,
        "tamanho_bytes": doc.tamanho_bytes,
        "data_emissao": doc.data_emissao.isoformat() if doc.data_emissao else None,
        "data_validade": doc.data_validade.isoformat() if doc.data_validade else None,
        "dias_para_vencimento": _dias_para_vencimento(doc.data_validade),
        "status_validade": _status_validade(doc.data_validade),
        "status": doc.status,
        "status_documental": getattr(doc, "status_documental", None) or "RECEBIDO",
        "status_documental_motivo": getattr(doc, "status_documental_motivo", None),
        "status_documental_atualizado_por": getattr(doc, "status_documental_atualizado_por", None),
        "status_documental_atualizado_em": doc.status_documental_atualizado_em.isoformat() if getattr(doc, "status_documental_atualizado_em", None) else None,
        "origem": doc.origem,
        "operacao_vigencia": getattr(doc, "operacao_vigencia", None),
        "vigencia_inicio": doc.vigencia_inicio.isoformat() if getattr(doc, "vigencia_inicio", None) else None,
        "vigencia_fim": doc.vigencia_fim.isoformat() if getattr(doc, "vigencia_fim", None) else None,
        "vigencia_status": getattr(doc, "vigencia_status", None),
        "vigencia_origem_calculo": getattr(doc, "vigencia_origem_calculo", None),
        "vigencia_editada_manualmente": bool(getattr(doc, "vigencia_editada_manualmente", False)),
        "motivo_alteracao_vigencia": getattr(doc, "motivo_alteracao_vigencia", None),
        "ativo": doc.ativo,
        "criado_por": doc.criado_por,
        "criado_em": doc.criado_em.isoformat() if doc.criado_em else None,
        "atualizado_em": doc.atualizado_em.isoformat() if doc.atualizado_em else None,
    }


def _parse_date(value: Optional[str]):
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Data invalida: {value}. Use AAAA-MM-DD.")


DIAS_ATENDIMENTO_FARMACIA = {0, 1, 2, 3}  # segunda a quinta; sexta/sábado/domingo fechados


def _proximo_dia_util_farmacia(data_base: date) -> date:
    """Retorna o próximo dia de atendimento da Farmácia Escola a partir de data_base."""
    data = data_base
    for _ in range(10):
        if data.weekday() in DIAS_ATENDIMENTO_FARMACIA:
            return data
        data += timedelta(days=1)
    return data


def _status_validade(data_validade: Optional[date], hoje: Optional[date] = None) -> str:
    hoje = hoje or date.today()
    if not data_validade:
        return "SEM_VALIDADE"
    primeiro_dia_util_apos = _proximo_dia_util_farmacia(data_validade + timedelta(days=1))
    if hoje >= primeiro_dia_util_apos:
        return "VENCIDO_URGENTE"
    if data_validade < hoje:
        return "VENCIDO"
    dias = (data_validade - hoje).days
    if dias <= 30:
        return "VENCE_EM_30_DIAS"
    if dias <= 60:
        return "VENCE_EM_60_DIAS"
    return "VALIDO"


def _dias_para_vencimento(data_validade: Optional[date], hoje: Optional[date] = None):
    if not data_validade:
        return None
    hoje = hoje or date.today()
    return (data_validade - hoje).days


def _normalizar_tipo(tipo: str):
    tipo_norm = (tipo or "").strip().upper()
    if tipo_norm not in TIPOS_DOCUMENTO:
        raise HTTPException(status_code=400, detail=f"Tipo de documento invalido. Use: {', '.join(TIPOS_DOCUMENTO)}")
    return tipo_norm


@router.get("/documentos/opcoes")
def opcoes_documentos(current=Depends(get_current_user_consultorio)):
    return {
        "tipos_documento": TIPOS_DOCUMENTO,
        "status": STATUS_DOCUMENTO,
        "status_documental": STATUS_DOCUMENTAL,
        "origens": ORIGENS_DOCUMENTO,
        "operacoes_vigencia": OPERACOES_VIGENCIA,
        "status_vigencia": STATUS_VIGENCIA,
    }


@router.post("/paciente-clinico/{paciente_id}/documentos")
async def upload_documento_paciente(
    paciente_id: int,
    arquivo: UploadFile = File(...),
    tipo_documento: str = Form(...),
    titulo: Optional[str] = Form(None),
    descricao: Optional[str] = Form(None),
    data_emissao: Optional[str] = Form(None),
    data_validade: Optional[str] = Form(None),
    operacao_vigencia: Optional[str] = Form(None),
    processo_documental_id: Optional[int] = Form(None),
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    exigir_farmaceutico_ou_admin(current)

    paciente = db.query(PacienteClinico).filter(PacienteClinico.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente clinico nao encontrado")

    processo_documental = None
    if processo_documental_id:
        processo_documental = db.query(ProcessoDocumental).filter(ProcessoDocumental.id == processo_documental_id).first()
        if not processo_documental:
            raise HTTPException(status_code=404, detail="Processo documental não encontrado")
        if processo_documental.paciente_id != paciente_id:
            raise HTTPException(status_code=400, detail="Processo documental pertence a outro paciente")

    tipo = _normalizar_tipo(tipo_documento)
    conteudo = await arquivo.read()
    if not conteudo:
        raise HTTPException(status_code=400, detail="Arquivo vazio")

    nome_original = arquivo.filename or "documento"
    sufixo = Path(nome_original).suffix.lower()[:20]
    nome_salvo = f"paciente_{paciente_id}_{uuid4().hex}{sufixo}"
    destino = BASE_UPLOAD_DIR / nome_salvo
    destino.write_bytes(conteudo)

    usuario = getattr(current, "email", None) or getattr(current, "nome", None)
    doc = DocumentoPaciente(
        paciente_id=paciente_id,
        processo_documental_id=processo_documental_id,
        tipo_documento=tipo,
        titulo=titulo or nome_original,
        descricao=descricao,
        nome_arquivo_original=nome_original,
        nome_arquivo_salvo=nome_salvo,
        caminho_arquivo=str(destino),
        content_type=arquivo.content_type,
        tamanho_bytes=len(conteudo),
        data_emissao=_parse_date(data_emissao),
        data_validade=_parse_date(data_validade),
        operacao_vigencia=(operacao_vigencia.upper() if operacao_vigencia else None),
        status="ATIVO",
        status_documental="RECEBIDO",
        status_documental_motivo="Documento recebido por upload.",
        status_documental_atualizado_por=usuario,
        status_documental_atualizado_em=datetime.utcnow(),
        origem="UPLOAD_MANUAL",
        ativo=True,
        criado_por=usuario,
    )
    db.add(doc)
    db.flush()
    if doc.tipo_documento in {"LAUDO", "RECEITA"}:
        aplicar_vigencia_calculada(db, doc, operacao_vigencia=(operacao_vigencia.upper() if operacao_vigencia else None), usuario=usuario)
        criar_evento_notificacao_whatsapp_documento(db, doc, usuario=usuario)
    if processo_documental:
        if processo_documental.vigencia_inicio and processo_documental.vigencia_fim and doc.tipo_documento in {"LAUDO", "RECEITA"}:
            doc.vigencia_inicio = processo_documental.vigencia_inicio
            doc.vigencia_fim = processo_documental.vigencia_fim
            doc.vigencia_status = status_vigencia(doc.vigencia_inicio, doc.vigencia_fim)
            doc.vigencia_origem_calculo = "PROCESSO_DOCUMENTAL"
        elif doc.tipo_documento == "LAUDO" and doc.vigencia_inicio and doc.vigencia_fim and not processo_documental.vigencia_inicio:
            processo_documental.vigencia_inicio = doc.vigencia_inicio
            processo_documental.vigencia_fim = doc.vigencia_fim
            processo_documental.vigencia_status = doc.vigencia_status
            processo_documental.atualizado_em = datetime.utcnow()
    db.commit()
    db.refresh(doc)
    return {"mensagem": "Documento enviado com sucesso", "documento": _serializar_documento(doc)}


@router.get("/paciente-clinico/{paciente_id}/documentos")
def listar_documentos_paciente(
    paciente_id: int,
    tipo_documento: Optional[str] = None,
    processo_documental_id: Optional[int] = None,
    ativo: Optional[bool] = True,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    paciente = db.query(PacienteClinico).filter(PacienteClinico.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente clinico nao encontrado")

    query = db.query(DocumentoPaciente).filter(DocumentoPaciente.paciente_id == paciente_id)
    if tipo_documento:
        query = query.filter(DocumentoPaciente.tipo_documento == tipo_documento.upper())
    if processo_documental_id is not None:
        query = query.filter(DocumentoPaciente.processo_documental_id == processo_documental_id)
    if ativo is not None:
        query = query.filter(DocumentoPaciente.ativo == ativo)

    documentos = query.order_by(DocumentoPaciente.criado_em.desc()).all()
    return {"total": len(documentos), "documentos": [_serializar_documento(d) for d in documentos]}




@router.get("/documentos/validade-dashboard")
def dashboard_validade_documental(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    hoje = date.today()
    primeiro_dia_60 = hoje + timedelta(days=60)
    primeiro_dia_30 = hoje + timedelta(days=30)

    ativos = db.query(DocumentoPaciente).filter(DocumentoPaciente.ativo == True)  # noqa: E712
    total = ativos.count()
    com_validade = ativos.filter(DocumentoPaciente.data_validade.isnot(None)).count()
    sem_validade = total - com_validade

    vencidos_urgentes = 0
    vencidos = 0
    vence_30 = 0
    vence_60 = 0

    documentos_com_validade = ativos.filter(DocumentoPaciente.data_validade.isnot(None)).all()
    for doc in documentos_com_validade:
        status_validade = _status_validade(doc.data_validade, hoje)
        if status_validade == "VENCIDO_URGENTE":
            vencidos_urgentes += 1
        elif status_validade == "VENCIDO":
            vencidos += 1
        elif status_validade == "VENCE_EM_30_DIAS":
            vence_30 += 1
        elif status_validade == "VENCE_EM_60_DIAS":
            vence_60 += 1

    laudos_ativos = ativos.filter(DocumentoPaciente.tipo_documento == "LAUDO").count()
    receitas_ativas = ativos.filter(DocumentoPaciente.tipo_documento == "RECEITA").count()

    return {
        "total_documentos_ativos": total,
        "com_validade": com_validade,
        "sem_validade": sem_validade,
        "vencidos_urgentes": vencidos_urgentes,
        "vencidos": vencidos,
        "vence_em_30_dias": vence_30,
        "vence_em_60_dias": vence_60,
        "laudos_ativos": laudos_ativos,
        "receitas_ativas": receitas_ativas,
        "data_referencia": hoje.isoformat(),
        "janela_30_dias": primeiro_dia_30.isoformat(),
        "janela_60_dias": primeiro_dia_60.isoformat(),
    }


@router.get("/documentos/vencimentos")
def listar_documentos_por_vencimento(
    dias: int = 60,
    tipo_documento: Optional[str] = None,
    processo_documental_id: Optional[int] = None,
    incluir_sem_validade: bool = False,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    hoje = date.today()
    limite = hoje + timedelta(days=max(1, min(dias, 365)))

    query = db.query(DocumentoPaciente).filter(DocumentoPaciente.ativo == True)  # noqa: E712
    if tipo_documento:
        query = query.filter(DocumentoPaciente.tipo_documento == tipo_documento.upper())
    if processo_documental_id is not None:
        query = query.filter(DocumentoPaciente.processo_documental_id == processo_documental_id)

    if incluir_sem_validade:
        documentos = query.filter(
            (DocumentoPaciente.data_validade <= limite) | (DocumentoPaciente.data_validade.is_(None))
        ).order_by(DocumentoPaciente.data_validade.asc().nullslast()).all()
    else:
        documentos = query.filter(
            DocumentoPaciente.data_validade.isnot(None),
            DocumentoPaciente.data_validade <= limite,
        ).order_by(DocumentoPaciente.data_validade.asc()).all()

    return {"total": len(documentos), "documentos": [_serializar_documento(d) for d in documentos]}


@router.post("/documentos/gerar-notificacoes-validade")
def gerar_notificacoes_validade_documental(
    dias_alerta: int = 60,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    exigir_farmaceutico_ou_admin(current)
    hoje = date.today()
    limite = hoje + timedelta(days=max(1, min(dias_alerta, 180)))
    tipos_monitorados = ["LAUDO", "RECEITA"]

    documentos = db.query(DocumentoPaciente).filter(
        DocumentoPaciente.ativo == True,  # noqa: E712
        DocumentoPaciente.tipo_documento.in_(tipos_monitorados),
        DocumentoPaciente.data_validade.isnot(None),
        DocumentoPaciente.data_validade <= limite,
    ).all()

    criadas = 0
    ignoradas = 0

    for doc in documentos:
        status_validade = _status_validade(doc.data_validade, hoje)
        if status_validade == "VALIDO":
            ignoradas += 1
            continue

        if status_validade == "VENCIDO_URGENTE":
            prioridade = "URGENTE"
            titulo = f"{doc.tipo_documento.title()} vencido sem renovação"
            mensagem = (
                f"{doc.tipo_documento.title()} do paciente ID {doc.paciente_id} venceu em "
                f"{doc.data_validade.strftime('%d/%m/%Y')}. Ação imediata recomendada."
            )
        elif status_validade in {"VENCE_EM_30_DIAS", "VENCE_EM_60_DIAS", "VENCIDO"}:
            prioridade = "IMPORTANTE"
            titulo = f"{doc.tipo_documento.title()} a vencer ou pendente"
            mensagem = (
                f"{doc.tipo_documento.title()} do paciente ID {doc.paciente_id} possui validade em "
                f"{doc.data_validade.strftime('%d/%m/%Y')}. Acompanhar renovação."
            )
        else:
            ignoradas += 1
            continue

        existente = db.query(NotificacaoInterna).filter(
            NotificacaoInterna.paciente_id == doc.paciente_id,
            NotificacaoInterna.tipo == doc.tipo_documento,
            NotificacaoInterna.prioridade == prioridade,
            NotificacaoInterna.lida == False,  # noqa: E712
            NotificacaoInterna.titulo == titulo,
        ).first()
        if existente:
            ignoradas += 1
            continue

        notificacao = NotificacaoInterna(
            paciente_id=doc.paciente_id,
            tipo=doc.tipo_documento,
            prioridade=prioridade,
            origem="DOCUMENTO_AUTOMATICA",
            titulo=titulo,
            mensagem=mensagem,
            lida=False,
            necessita_acao=True,
        )
        db.add(notificacao)
        criadas += 1

    db.commit()
    return {"criadas": criadas, "ignoradas": ignoradas, "documentos_avaliados": len(documentos)}


@router.get("/documentos/status-opcoes")
def opcoes_status_documental(current=Depends(get_current_user_consultorio)):
    return {
        "status_documental": STATUS_DOCUMENTAL,
        "regra_completude": "Somente documentos com status_documental VALIDADO contam para a completude do pacote documental.",
        "whatsapp_documental": "Pendências documentais não geram WhatsApp automático; envio somente manual pelo operador.",
    }


@router.get("/documentos/status-dashboard")
def dashboard_status_documental(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    documentos = db.query(DocumentoPaciente).filter(DocumentoPaciente.ativo == True).all()  # noqa: E712
    por_status = {status: 0 for status in STATUS_DOCUMENTAL}
    for doc in documentos:
        status_doc = (getattr(doc, "status_documental", None) or "RECEBIDO").upper()
        por_status[status_doc] = por_status.get(status_doc, 0) + 1
    return {
        "total_documentos_ativos": len(documentos),
        "por_status_documental": por_status,
        "validados": por_status.get("VALIDADO", 0),
        "rejeitados": por_status.get("REJEITADO", 0),
        "recebidos_pendentes_de_validacao": por_status.get("RECEBIDO", 0),
    }


@router.put("/documentos/{documento_id}/status-documental")
def atualizar_status_documental_documento(
    documento_id: int,
    dados: StatusDocumentalUpdate,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    exigir_farmaceutico_ou_admin(current)
    doc = db.query(DocumentoPaciente).filter(DocumentoPaciente.id == documento_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento não encontrado")

    status_novo = _normalizar_status_documental(dados.status_documental)
    motivo = (dados.motivo or "").strip()
    if len(motivo) < 5:
        raise HTTPException(status_code=400, detail="Motivo obrigatório para alteração de status documental")

    usuario = getattr(current, "email", None) or getattr(current, "nome", None)
    status_anterior = getattr(doc, "status_documental", None) or "RECEBIDO"

    doc.status_documental = status_novo
    doc.status_documental_motivo = motivo
    doc.status_documental_atualizado_por = usuario
    doc.status_documental_atualizado_em = datetime.utcnow()
    doc.atualizado_em = datetime.utcnow()

    _registrar_historico_status_documental(
        db, doc, status_anterior, status_novo, motivo, dados.observacao, usuario, origem="MANUAL"
    )

    if status_novo == "REJEITADO":
        notificacao = NotificacaoInterna(
            paciente_id=doc.paciente_id,
            tipo="PENDENCIA_DOCUMENTAL",
            prioridade="IMPORTANTE",
            origem="STATUS_DOCUMENTAL",
            titulo="Documento rejeitado",
            mensagem=f"Documento {doc.titulo or doc.nome_arquivo_original} foi rejeitado. Motivo: {motivo}",
            lida=False,
            necessita_acao=True,
        )
        db.add(notificacao)

    db.commit()
    db.refresh(doc)
    return {
        "mensagem": "Status documental atualizado",
        "documento": _serializar_documento(doc),
        "whatsapp_automatico": False,
    }


@router.get("/documentos/{documento_id}/status-historico")
def historico_status_documental(
    documento_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    doc = db.query(DocumentoPaciente).filter(DocumentoPaciente.id == documento_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    historico = db.query(HistoricoStatusDocumento).filter(
        HistoricoStatusDocumento.documento_id == documento_id
    ).order_by(HistoricoStatusDocumento.criado_em.desc()).all()
    return {
        "documento": _serializar_documento(doc),
        "total": len(historico),
        "historico": [
            {
                "id": h.id,
                "documento_id": h.documento_id,
                "paciente_id": h.paciente_id,
                "processo_documental_id": h.processo_documental_id,
                "status_anterior": h.status_anterior,
                "status_novo": h.status_novo,
                "motivo": h.motivo,
                "observacao": h.observacao,
                "usuario": h.usuario,
                "origem": h.origem,
                "criado_em": h.criado_em.isoformat() if h.criado_em else None,
            }
            for h in historico
        ],
    }


@router.get("/documentos/{documento_id}/download")
def download_documento(
    documento_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    doc = db.query(DocumentoPaciente).filter(DocumentoPaciente.id == documento_id, DocumentoPaciente.ativo == True).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento nao encontrado")
    caminho = Path(doc.caminho_arquivo)
    if not caminho.exists():
        raise HTTPException(status_code=404, detail="Arquivo fisico nao encontrado")
    return FileResponse(path=str(caminho), filename=doc.nome_arquivo_original, media_type=doc.content_type or "application/octet-stream")


@router.put("/documentos/{documento_id}/metadados")
def atualizar_metadados_documento(
    documento_id: int,
    dados: DocumentoPacienteUpdate,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    exigir_farmaceutico_ou_admin(current)
    doc = db.query(DocumentoPaciente).filter(DocumentoPaciente.id == documento_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento nao encontrado")

    payload = dados.model_dump(exclude_unset=True)
    if "tipo_documento" in payload and payload["tipo_documento"] is not None:
        payload["tipo_documento"] = _normalizar_tipo(payload["tipo_documento"])
    if "status" in payload and payload["status"] is not None:
        status = payload["status"].upper()
        if status not in STATUS_DOCUMENTO:
            raise HTTPException(status_code=400, detail=f"Status invalido. Use: {', '.join(STATUS_DOCUMENTO)}")
        payload["status"] = status

    for campo, valor in payload.items():
        setattr(doc, campo, valor)
    processo_documental = None
    if getattr(doc, "processo_documental_id", None):
        processo_documental = db.query(ProcessoDocumental).filter(ProcessoDocumental.id == doc.processo_documental_id).first()

    if doc.tipo_documento in {"LAUDO", "RECEITA"}:
        usuario = getattr(current, "email", None) or getattr(current, "nome", None)
        aplicar_vigencia_calculada(db, doc, operacao_vigencia=getattr(doc, "operacao_vigencia", None), usuario=usuario, motivo="Recalculo após atualização de metadados")
        criar_evento_notificacao_whatsapp_documento(db, doc, usuario=usuario)
    if processo_documental:
        if processo_documental.vigencia_inicio and processo_documental.vigencia_fim and doc.tipo_documento in {"LAUDO", "RECEITA"}:
            doc.vigencia_inicio = processo_documental.vigencia_inicio
            doc.vigencia_fim = processo_documental.vigencia_fim
            doc.vigencia_status = status_vigencia(doc.vigencia_inicio, doc.vigencia_fim)
            doc.vigencia_origem_calculo = "PROCESSO_DOCUMENTAL"
        elif doc.tipo_documento == "LAUDO" and doc.vigencia_inicio and doc.vigencia_fim and not processo_documental.vigencia_inicio:
            processo_documental.vigencia_inicio = doc.vigencia_inicio
            processo_documental.vigencia_fim = doc.vigencia_fim
            processo_documental.vigencia_status = doc.vigencia_status
            processo_documental.atualizado_em = datetime.utcnow()
    doc.atualizado_em = datetime.utcnow()
    db.commit()
    db.refresh(doc)
    return {"mensagem": "Documento atualizado", "documento": _serializar_documento(doc)}


@router.delete("/documentos/{documento_id}")
def inativar_documento(
    documento_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    exigir_farmaceutico_ou_admin(current)
    doc = db.query(DocumentoPaciente).filter(DocumentoPaciente.id == documento_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento nao encontrado")
    doc.ativo = False
    doc.status = "CANCELADO"
    doc.atualizado_em = datetime.utcnow()
    db.commit()
    db.refresh(doc)
    return {"mensagem": "Documento inativado", "documento": _serializar_documento(doc)}


@router.get("/documentos/{documento_id}/vigencia-historico")
def historico_vigencia_documento(
    documento_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    doc = db.query(DocumentoPaciente).filter(DocumentoPaciente.id == documento_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento nao encontrado")
    historico = db.query(HistoricoVigenciaDocumento).filter(
        HistoricoVigenciaDocumento.documento_id == documento_id
    ).order_by(HistoricoVigenciaDocumento.criado_em.desc()).all()
    return {
        "documento": _serializar_documento(doc),
        "total": len(historico),
        "historico": [
            {
                "id": h.id,
                "documento_id": h.documento_id,
                "paciente_id": h.paciente_id,
                "vigencia_inicio_anterior": h.vigencia_inicio_anterior.isoformat() if h.vigencia_inicio_anterior else None,
                "vigencia_fim_anterior": h.vigencia_fim_anterior.isoformat() if h.vigencia_fim_anterior else None,
                "vigencia_status_anterior": h.vigencia_status_anterior,
                "vigencia_inicio_nova": h.vigencia_inicio_nova.isoformat() if h.vigencia_inicio_nova else None,
                "vigencia_fim_nova": h.vigencia_fim_nova.isoformat() if h.vigencia_fim_nova else None,
                "vigencia_status_nova": h.vigencia_status_nova,
                "motivo": h.motivo,
                "observacao": h.observacao,
                "usuario": h.usuario,
                "origem": h.origem,
                "criado_em": h.criado_em.isoformat() if h.criado_em else None,
            }
            for h in historico
        ],
    }


@router.put("/documentos/{documento_id}/vigencia")
def editar_vigencia_documento(
    documento_id: int,
    dados: VigenciaDocumentoUpdate,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    exigir_farmaceutico_ou_admin(current)
    doc = db.query(DocumentoPaciente).filter(DocumentoPaciente.id == documento_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento nao encontrado")
    if dados.vigencia_fim < dados.vigencia_inicio:
        raise HTTPException(status_code=400, detail="Fim da vigencia nao pode ser anterior ao inicio")
    motivo = (dados.motivo or "").strip()
    if len(motivo) < 5:
        raise HTTPException(status_code=400, detail="Motivo da alteracao da vigencia é obrigatório")

    usuario = getattr(current, "email", None) or getattr(current, "nome", None)
    anterior = {"inicio": doc.vigencia_inicio, "fim": doc.vigencia_fim, "status": doc.vigencia_status}
    novo_status = status_vigencia(dados.vigencia_inicio, dados.vigencia_fim)
    novo = {"inicio": dados.vigencia_inicio, "fim": dados.vigencia_fim, "status": novo_status}

    doc.vigencia_inicio = dados.vigencia_inicio
    doc.vigencia_fim = dados.vigencia_fim
    doc.vigencia_status = novo_status
    doc.vigencia_editada_manualmente = True
    doc.motivo_alteracao_vigencia = motivo
    doc.vigencia_origem_calculo = "EDICAO_MANUAL"
    doc.atualizado_em = datetime.utcnow()

    registrar_historico_vigencia(
        db, doc, anterior, novo, motivo=motivo, observacao=dados.observacao, usuario=usuario, origem="MANUAL"
    )
    resultado_fluxo = recalcular_fluxo_documento(db, doc, usuario=usuario)
    db.commit()
    db.refresh(doc)
    return {
        "mensagem": "Vigencia atualizada e fluxo operacional recalculado",
        "documento": _serializar_documento(doc),
        "fluxo": resultado_fluxo,
    }


@router.post("/documentos/{documento_id}/reprocessar-fluxo")
def reprocessar_fluxo_documento(
    documento_id: int,
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio),
):
    exigir_farmaceutico_ou_admin(current)
    doc = db.query(DocumentoPaciente).filter(DocumentoPaciente.id == documento_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento nao encontrado")
    usuario = getattr(current, "email", None) or getattr(current, "nome", None)
    resultado = recalcular_fluxo_documento(db, doc, usuario=usuario)
    db.commit()
    return resultado
