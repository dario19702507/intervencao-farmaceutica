import csv
import io
import os
from datetime import datetime, date
from typing import List, Optional
from types import SimpleNamespace
from uuid import uuid4

from fastapi import FastAPI, Depends, HTTPException, Request, status, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy import func
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from routers.consultorio import router as consultorio_router
from routers.pacientes_consultorio import router as pacientes_consultorio_router
from routers.conversao_clinica import router as conversao_clinica_router
from routers.notificacoes import router as notificacoes_router
from routers.notificacoes_internas import router as notificacoes_internas_router
from routers.whatsapp import router as whatsapp_router
from routers.documentos import router as documentos_router
from routers.processos_documentais import router as processos_documentais_router
from routers.ocr_documentos import router as ocr_documentos_router
from routers.migracao_intervencoes import router as migracao_intervencoes_router
from routers.painel_operacional import router as painel_operacional_router
from routers.relatorios_gerenciais import router as relatorios_gerenciais_router
from routers.cuidado_farmaceutico import router as cuidado_farmaceutico_router
from routers.metas_terapeuticas import router as metas_terapeuticas_router
from routers.atencao_farmaceutica import router as atencao_farmaceutica_router
from routers.intervencoes_padronizadas import router as intervencoes_padronizadas_router
from routers.preenchimento_assistido import router as preenchimento_assistido_router
from routers.pacientes import router as pacientes_router
from routers.agenda import router as agenda_router
from routers.atendimento_rapido import router as atendimento_rapido_router
from routers.servicos_rapidos import router as servicos_rapidos_router
from routers.evolucoes_desfechos import router as evolucoes_desfechos_router
from routers.timeline_consultorio import router as timeline_consultorio_router
from routers.prontuario_consultorio import router as prontuario_consultorio_router
from routers.auditoria import router as auditoria_router
from routers.indicadores_consultorio import router as indicadores_consultorio_router
from routers.dashboard_notificacoes import router as dashboard_notificacoes_router
from routers.farmacoterapia import router as farmacoterapia_router
from routers.indicadores_cientificos import router as indicadores_cientificos_router
from routers.ceaf import router as ceaf_router
from routers.medicamentos import router as medicamentos_router
from database import SessionLocal, get_db
from auth import ALGORITHM, SECRET_KEY, create_access_token, hash_password, oauth2_scheme, verify_password
from permissions import exigir_admin as perm_exigir_admin, exigir_pode_escrever, usuario_eh_leitura_restrita, validar_perfil_usuario, obter_perfil
from models.core import User, Intervencao
from models.consultorio_models import AuditoriaSistema
from schemas.core import (
    Token, UserOut, PasswordReset, ChangeOwnPassword, InativarPayload,
    IntervencaoCreate, IntervencaoOut, Indicadores, UserCreate,
)
from migrations import aplicar_migracoes_simples


aplicar_migracoes_simples()

app = FastAPI(title="Sistema de Intervenção Farmacêutica", version="1.0.0")

app.include_router(conversao_clinica_router)
app.include_router(pacientes_consultorio_router)
app.include_router(notificacoes_router)
app.include_router(notificacoes_internas_router)
app.include_router(whatsapp_router)
app.include_router(documentos_router)
app.include_router(processos_documentais_router)
app.include_router(ocr_documentos_router)
app.include_router(migracao_intervencoes_router)
app.include_router(painel_operacional_router)
app.include_router(relatorios_gerenciais_router)
app.include_router(cuidado_farmaceutico_router)
app.include_router(metas_terapeuticas_router)
app.include_router(atencao_farmaceutica_router)
app.include_router(intervencoes_padronizadas_router)
app.include_router(preenchimento_assistido_router)
app.include_router(pacientes_router)
app.include_router(agenda_router)
app.include_router(atendimento_rapido_router)
app.include_router(servicos_rapidos_router)
app.include_router(evolucoes_desfechos_router)
app.include_router(timeline_consultorio_router)
app.include_router(prontuario_consultorio_router)
app.include_router(auditoria_router)
app.include_router(indicadores_consultorio_router)
app.include_router(dashboard_notificacoes_router)
app.include_router(farmacoterapia_router)
app.include_router(indicadores_cientificos_router)
app.include_router(ceaf_router)
app.include_router(medicamentos_router)
app.include_router(consultorio_router)


def _split_env_list(value: str):
    return [item.strip() for item in (value or "").split(",") if item.strip()]


def _cors_origins():
    """Origens liberadas para o frontend.

    Em produção, configure ALLOWED_ORIGINS no Render com o domínio real do
    frontend, por exemplo: https://seu-projeto.vercel.app.
    FRONTEND_ORIGIN foi mantida por compatibilidade com versões anteriores.
    """
    origins = _split_env_list(os.getenv("ALLOWED_ORIGINS", ""))
    legacy_frontend = os.getenv("FRONTEND_ORIGIN", "").strip()
    if legacy_frontend:
        origins.append(legacy_frontend)

    defaults = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://0.0.0.0:5173",
    ]
    origins.extend(defaults)

    return list(dict.fromkeys(origins))


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_origin_regex=os.getenv("ALLOWED_ORIGIN_REGEX", r"^http://192\.168\.\d{1,3}\.\d{1,3}:5173$"),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


PUBLIC_PATHS = {
    "/",
    "/auth/login",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/opcoes",
    "/health",
}
READ_ONLY_BLOCKED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
READ_ONLY_ALLOWED_PREFIXES = ("/me",)
AUDITABLE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _is_public_path(path: str) -> bool:
    return path in PUBLIC_PATHS or path.startswith("/docs/") or path.startswith("/redoc/")


def _unauthorized(message: str, status_code: int = 401):
    return JSONResponse(status_code=status_code, content={"detail": message})


def _registrar_mutacao_global(user: User, request: Request, status_code: int, request_id: str):
    """Registro simples de auditoria para ações de escrita no piloto.

    A auditoria não bloqueia a operação principal. Se a tabela ainda não
    existir ou se houver falha transitória, o erro é ignorado para não gerar
    indisponibilidade durante a homologação.
    """
    if request.method not in AUDITABLE_METHODS:
        return

    db = SessionLocal()
    try:
        usuario = getattr(user, "nome", None) or getattr(user, "email", None) or "usuario"
        evento = AuditoriaSistema(
            usuario=usuario,
            modulo="http",
            acao=f"{request.method} {request.url.path}",
            registro_id=None,
            descricao=f"status={status_code}; request_id={request_id}",
            criado_em=datetime.utcnow(),
        )
        db.add(evento)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


@app.middleware("http")
async def exigir_login_global(request: Request, call_next):
    """Barreira mínima de pré-homologação multiusuário.

    Garante que endpoints assistenciais, administrativos e documentais não
    fiquem expostos caso algum router tenha sido criado sem dependência de
    autenticação. Também impede alteração por perfis de leitura/pesquisa.
    """
    request_id = request.headers.get("X-Request-ID") or str(uuid4())

    if request.method == "OPTIONS" or _is_public_path(request.url.path):
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        response = _unauthorized("Login obrigatório para acessar este recurso")
        response.headers["X-Request-ID"] = request_id
        return response

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            response = _unauthorized("Token inválido")
            response.headers["X-Request-ID"] = request_id
            return response
    except JWTError:
        response = _unauthorized("Token inválido")
        response.headers["X-Request-ID"] = request_id
        return response

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            response = _unauthorized("Usuário não encontrado")
            response.headers["X-Request-ID"] = request_id
            return response

        if (
            request.method in READ_ONLY_BLOCKED_METHODS
            and usuario_eh_leitura_restrita(user)
            and not request.url.path.startswith(READ_ONLY_ALLOWED_PREFIXES)
        ):
            response = _unauthorized("Perfil sem permissão para alterar registros", status_code=403)
            response.headers["X-Request-ID"] = request_id
            return response

        user_snapshot = SimpleNamespace(
            id=user.id,
            email=user.email,
            nome=getattr(user, "nome", None),
            perfil=getattr(user, "perfil", None),
        )
    finally:
        db.close()

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    _registrar_mutacao_global(user_snapshot, request, response.status_code, request_id)
    return response

MOTIVOS = ["Documentação (inclusão/renovação/adequação)", "Dúvidas de paciente"]
COMORBIDADES = ["Esclerose múltipla", "Esclerose Sistêmica", "Esclerose Lateral Amiotrófica", "Asma/DPOC", "Outro"]
TIPOS_INTERVENCAO = ["Posologia", "Acondicionamento", "Técnica de uso", "Reação Adversa a Medicamentos (RAM)", "Erro de prescrição", "Orientação documental", "Encaminhamentos", "Educação em Saúde", "Orientação ao profissional da saúde", "Parâmetros clínicos"]
RESULTADOS = ["Aceitação", "Acompanhamento do paciente", "Outro"]

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Token inválido")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    return user

def ensure_admin(user: User):
    perm_exigir_admin(user)

def ensure_not_reader(user: User):
    exigir_pode_escrever(user)

def ensure_can_edit(user: User, item: Intervencao):
    if user.perfil == "admin":
        return
    if user.categoria_profissional == "Estagiário" and item.profissional_id != user.id:
        raise HTTPException(status_code=403, detail="Estagiário só pode editar os próprios registros")
def mascarar_nome(nome: str):
    partes = nome.split()
    mascarado = []

    for parte in partes:
        if len(parte) <= 2:
            mascarado.append(parte[0] + "*")
        else:
            mascarado.append(parte[0] + "***")

    return " ".join(mascarado)

@app.on_event("startup")
def seed_admin():
    """Cria usuário inicial somente quando explicitamente habilitado.

    Em produção/homologação, não use senha padrão. Para desenvolvimento local,
    defina SEED_ADMIN=true no .env. A senha pode ser ajustada por
    SEED_ADMIN_PASSWORD.
    """
    if os.getenv("SEED_ADMIN", "false").lower() not in {"1", "true", "yes", "sim"}:
        return

    admin_email = os.getenv("SEED_ADMIN_EMAIL", "admin@farmacia.local")
    admin_password = os.getenv("SEED_ADMIN_PASSWORD", "")
    if not admin_password:
        raise RuntimeError("SEED_ADMIN_PASSWORD deve ser configurada quando SEED_ADMIN=true")

    db = SessionLocal()
    try:
        if not db.query(User).filter(User.email == admin_email).first():
            db.add(User(
                nome=os.getenv("SEED_ADMIN_NAME", "Administrador"),
                email=admin_email,
                hashed_password=hash_password(admin_password),
                perfil="admin",
            ))
            db.commit()
    finally:
        db.close()

@app.post("/auth/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-mail ou senha inválidos")
    return {"access_token": create_access_token({"sub": user.email}), "token_type": "bearer"}

@app.post("/users", response_model=UserOut)
def create_user(payload: UserCreate, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    ensure_admin(current)
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")
    perfil_validado = validar_perfil_usuario(payload.perfil)
    user = User(
        nome=payload.nome,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        perfil=perfil_validado,
        categoria_profissional=payload.categoria_profissional
    )
    db.add(user); db.commit(); db.refresh(user)
    return user

@app.get("/users", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    ensure_admin(current)
    return db.query(User).order_by(User.nome.asc()).all()

@app.get("/profissionais", response_model=List[UserOut])
def listar_profissionais(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    return db.query(User).order_by(User.nome.asc()).all()

@app.get("/supervisores", response_model=List[UserOut])
def listar_supervisores(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    return db.query(User).filter(
        User.categoria_profissional.in_(["Farmacêutico", "Técnico", "Docente"])
    ).order_by(User.nome.asc()).all()

@app.put("/users/{user_id}/password", response_model=UserOut)
def reset_user_password(
    user_id: int,
    payload: PasswordReset,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user)
):
    ensure_admin(current)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    user.hashed_password = hash_password(payload.password)
    db.commit()
    db.refresh(user)

    return user

@app.get("/me", response_model=UserOut)
def me(current: User = Depends(get_current_user)):
    return current

@app.put("/me/password")
def change_own_password(
    payload: ChangeOwnPassword,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user)
):
    user = db.query(User).filter(User.id == current.id).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if not verify_password(payload.senha_atual, user.hashed_password):
        raise HTTPException(status_code=400, detail="Senha atual incorreta")

    user.hashed_password = hash_password(payload.nova_senha)
    db.commit()

    return {"ok": True}

@app.get("/opcoes")
def opcoes():
    return {"motivos": MOTIVOS, "comorbidades": COMORBIDADES, "tipos_intervencao": TIPOS_INTERVENCAO, "resultados": RESULTADOS, "tipos_atendimento": ["Presencial", "Remoto"]}

@app.post("/intervencoes", response_model=IntervencaoOut)
def criar_intervencao(
    payload: IntervencaoCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user)
):
    ensure_not_reader(current)

    if current.categoria_profissional == "Estagiário" and not payload.supervisor_id:
        raise HTTPException(status_code=400, detail="Supervisor obrigatório para estagiário")
    item = Intervencao(
        data_atendimento=payload.data_atendimento,
        paciente_nome=payload.paciente_nome.upper().strip(),
        data_nascimento=payload.data_nascimento,
        tipo_atendimento=payload.tipo_atendimento,
        motivo_atendimento=payload.motivo_atendimento,
        comorbidade=payload.comorbidade,
        tipos_intervencao=";".join(payload.tipos_intervencao),
        resultado=payload.resultado,
        observacoes=payload.observacoes,
        profissional_id=current.id,
        created_by=current.id,
        updated_by=current.id,
        supervisor_id=payload.supervisor_id,
    )
    db.add(item); db.commit(); db.refresh(item)
    return IntervencaoOut(**payload.model_dump(), id=item.id, profissional=current.nome, created_at=item.created_at)
@app.put("/intervencoes/{intervencao_id}", response_model=IntervencaoOut)
def atualizar_intervencao(
        intervencao_id: int,
        payload: IntervencaoCreate,
        db: Session = Depends(get_db),
        current: User = Depends(get_current_user)
    ):
    ensure_not_reader(current)

    item = db.query(Intervencao).filter(Intervencao.id == intervencao_id).first()

    if not item:
        raise HTTPException(status_code=404, detail="Intervenção não encontrada")

    ensure_can_edit(current, item)

    if current.categoria_profissional == "Estagiário" and not payload.supervisor_id:
        raise HTTPException(status_code=400, detail="Supervisor obrigatório para estagiário")

    item.data_atendimento = payload.data_atendimento
    item.paciente_nome = payload.paciente_nome.upper().strip()
    item.data_nascimento = payload.data_nascimento
    item.tipo_atendimento = payload.tipo_atendimento
    item.motivo_atendimento = payload.motivo_atendimento
    item.comorbidade = payload.comorbidade
    item.tipos_intervencao = ";".join(payload.tipos_intervencao)
    item.resultado = payload.resultado
    item.observacoes = payload.observacoes
    item.updated_at = datetime.utcnow()
    item.updated_by = current.id
    item.supervisor_id = payload.supervisor_id

    db.commit()
    db.refresh(item)

    profissional = db.query(User).filter(User.id == item.profissional_id).first()

    return IntervencaoOut(
        id=item.id,
        data_atendimento=item.data_atendimento,
        paciente_nome=item.paciente_nome,
        data_nascimento=item.data_nascimento,
        tipo_atendimento=item.tipo_atendimento,
        motivo_atendimento=item.motivo_atendimento,
        comorbidade=item.comorbidade,
        tipos_intervencao=item.tipos_intervencao.split(";"),
        resultado=item.resultado,
        observacoes=item.observacoes,
        profissional=profissional.nome if profissional else "",
        created_at=item.created_at
    )
@app.put("/intervencoes/{item_id}/inativar")
def inativar_intervencao(
    item_id: int,
    payload: InativarPayload,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user)
):
    ensure_not_reader(current)

    item = db.get(Intervencao, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Registro não encontrado")

    ensure_can_edit(current, item)

    item.ativo = False
    item.motivo_inativacao = payload.motivo
    item.updated_by = current.id
    item.updated_at = datetime.utcnow()

    db.commit()
    return {"ok": True}
@app.put("/intervencoes/{item_id}/reativar")
def reativar_intervencao(
    item_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user)
):
    ensure_admin(current)

    item = db.get(Intervencao, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Registro não encontrado")

    item.ativo = True
    item.motivo_inativacao = None
    item.updated_by = current.id
    item.updated_at = datetime.utcnow()

    db.commit()
    return {"ok": True}
@app.get("/intervencoes/exportar/csv")
def exportar_intervencoes_csv(
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user)
):
    q = db.query(Intervencao, User.nome).join(User, User.id == Intervencao.profissional_id)
    q = q.filter(Intervencao.ativo == True)

    if data_inicio:
        q = q.filter(Intervencao.data_atendimento >= data_inicio)

    if data_fim:
        q = q.filter(Intervencao.data_atendimento <= data_fim)

    rows = q.order_by(Intervencao.data_atendimento.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')

    writer.writerow([
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
        "profissional",
        "created_at"
    ])

    for i, nome in rows:
        writer.writerow([
            i.id,
            i.data_atendimento,
            mascarar_nome(i.paciente_nome) if usuario_eh_leitura_restrita(current) else i.paciente_nome,
            "" if usuario_eh_leitura_restrita(current) else i.data_nascimento,
            i.tipo_atendimento,
            i.motivo_atendimento,
            i.comorbidade,
            i.tipos_intervencao,
            i.resultado,
            "" if usuario_eh_leitura_restrita(current) else (i.observacoes or ""),
            nome,
            i.created_at
        ])

    csv_content = output.getvalue()

    return Response(
        content=csv_content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": "attachment; filename=intervencoes_farmaceuticas.csv"
        }
    )
@app.get("/intervencoes/inativadas", response_model=List[IntervencaoOut])
def listar_intervencoes_inativadas(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user)
):
    ensure_admin(current)

    q = db.query(Intervencao, User.nome, User.categoria_profissional).join(
        User, User.id == Intervencao.profissional_id
    )

    q = q.filter(Intervencao.ativo == False)

    rows = q.order_by(Intervencao.updated_at.desc()).limit(500).all()

    return [
        IntervencaoOut(
            id=i.id,
            data_atendimento=i.data_atendimento,
            paciente_nome=mascarar_nome(i.paciente_nome) if usuario_eh_leitura_restrita(current) else i.paciente_nome,
            data_nascimento=None if usuario_eh_leitura_restrita(current) else i.data_nascimento,
            tipo_atendimento=i.tipo_atendimento,
            motivo_atendimento=i.motivo_atendimento,
            comorbidade=i.comorbidade,
            tipos_intervencao=i.tipos_intervencao.split(";"),
            resultado=i.resultado,
            observacoes=None if usuario_eh_leitura_restrita(current) else i.observacoes,
            supervisor_id=i.supervisor_id,
            profissional=nome,
            created_at=i.created_at,
            updated_at=i.updated_at,
            criado_por=i.criador.nome if i.criador else nome,
            atualizado_por=i.atualizador.nome if i.atualizador else nome,
            supervisor_nome=i.supervisor.nome if i.supervisor else None,
            motivo_inativacao=i.motivo_inativacao,
            )
            for i, nome, _ in rows
        ]

@app.get("/intervencoes", response_model=List[IntervencaoOut])
def listar_intervencoes(
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    profissional_id: Optional[int] = None,
    categoria_profissional: Optional[str] = None,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user)
):
    q = db.query(Intervencao, User.nome, User.categoria_profissional).join(User, User.id == Intervencao.profissional_id)
    if data_inicio:
        q = q.filter(Intervencao.data_atendimento >= data_inicio)

    if data_fim:
        q = q.filter(Intervencao.data_atendimento <= data_fim)

    if profissional_id:
        q = q.filter(Intervencao.profissional_id == profissional_id)

    if categoria_profissional:
        q = q.filter(User.categoria_profissional == categoria_profissional)

    rows = q.order_by(Intervencao.data_atendimento.desc()).limit(500).all()

    return [
        IntervencaoOut(
            id=i.id,
            data_atendimento=i.data_atendimento,
            paciente_nome=i.paciente_nome,
            data_nascimento=None if usuario_eh_leitura_restrita(current) else i.data_nascimento,
            tipo_atendimento=i.tipo_atendimento,
            motivo_atendimento=i.motivo_atendimento,
            comorbidade=i.comorbidade,
            tipos_intervencao=i.tipos_intervencao.split(";"),
            resultado=i.resultado,
            observacoes=i.observacoes,
            profissional=nome,
            created_at=i.created_at,
            updated_at=i.updated_at,
            criado_por=i.criador.nome if i.criador else nome,
            atualizado_por=i.atualizador.nome if i.atualizador else nome,
            motivo_inativacao=i.motivo_inativacao,
            )
            for i, nome, _ in rows
        ]

def count_by(db, column, data_inicio=None, data_fim=None, profissional_id=None, categoria_profissional=None):
    q = db.query(column, func.count(Intervencao.id)).join(User, User.id == Intervencao.profissional_id).group_by(column)
    if data_inicio: 
        q = q.filter(Intervencao.data_atendimento >= data_inicio)
    if data_fim: 
        q = q.filter(Intervencao.data_atendimento <= data_fim)
    if profissional_id: 
        q = q.filter(Intervencao.profissional_id == profissional_id)
    if categoria_profissional: 
        q = q.filter(User.categoria_profissional == categoria_profissional)
    return {str(k): v for k, v in q.all()}

def calcular_faixa_etaria(data_nascimento: Optional[date]):
    if not data_nascimento:
        return "Sem informação"
    hoje = date.today()
    idade = hoje.year - data_nascimento.year - (
        (hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day)
    )

    if idade < 12:
        return "0 a 11 anos"
    if idade < 18:
        return "12 a 17 anos"
    if idade < 30:
        return "18 a 29 anos"
    if idade < 45:
        return "30 a 44 anos"
    if idade < 60:
        return "45 a 59 anos"
    return "60 anos ou mais"

@app.get("/indicadores", response_model=Indicadores)
def indicadores(
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    profissional_id: Optional[int] = None,
    categoria_profissional: Optional[str] = None,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user)
):
    q = db.query(Intervencao).join(User, User.id == Intervencao.profissional_id)
    q = q.filter(Intervencao.ativo == True)
    if data_inicio:
        q = q.filter(Intervencao.data_atendimento >= data_inicio)
    if data_fim: 
        q = q.filter(Intervencao.data_atendimento <= data_fim)
    if profissional_id:
        q = q.filter(Intervencao.profissional_id == profissional_id)
    if categoria_profissional:
        q = q.filter(User.categoria_profissional == categoria_profissional)
    registros = q.all()
    tipos = {}
    meses = {}
    faixas_etarias = {}
    for r in registros:
        for t in r.tipos_intervencao.split(";"):
            tipos[t] = tipos.get(t, 0) + 1

        chave_mes = r.data_atendimento.strftime("%Y-%m")
        meses[chave_mes] = meses.get(chave_mes, 0) + 1

        faixa = calcular_faixa_etaria(r.data_nascimento)
        faixas_etarias[faixa] = faixas_etarias.get(faixa, 0) + 1
    total = len(registros)

    aceitos = sum(1 for r in registros if r.resultado == "Aceitação")
    acompanhamentos = sum(1 for r in registros if r.resultado == "Acompanhamento do paciente")
    encaminhamentos = sum(
        1 for r in registros
        if "Encaminhamentos" in (r.tipos_intervencao or "")
    )

    taxa_aceitacao = round((aceitos / total) * 100, 2) if total else 0
    taxa_acompanhamento = round((acompanhamentos / total) * 100, 2) if total else 0
    taxa_encaminhamento = round((encaminhamentos / total) * 100, 2) if total else 0

    por_profissional = {
        nome: qtd
        for nome, qtd in db.query(User.nome, func.count(Intervencao.id))
            .join(Intervencao, Intervencao.profissional_id == User.id)
            .group_by(User.nome)
            .all()
    }

    por_categoria_profissional = {
        categoria or "Não informado": qtd
        for categoria, qtd in db.query(User.categoria_profissional, func.count(Intervencao.id))
            .join(Intervencao, Intervencao.profissional_id == User.id)
            .group_by(User.categoria_profissional)
            .all()
    }
    tendencia_mensal = {}

    for r in registros:
        mes = r.data_atendimento.strftime("%Y-%m")

        if mes not in tendencia_mensal:
            tendencia_mensal[mes] = {
                "intervencoes": 0,
                "aceitacao": 0,
                "acompanhamento": 0,
                "encaminhamento": 0,
            }

        tendencia_mensal[mes]["intervencoes"] += 1

        if r.resultado == "Aceitação":
            tendencia_mensal[mes]["aceitacao"] += 1

        if r.resultado == "Acompanhamento do paciente":
            tendencia_mensal[mes]["acompanhamento"] += 1

        if "Encaminhamentos" in (r.tipos_intervencao or ""):
            tendencia_mensal[mes]["encaminhamento"] += 1

    for mes, dados in tendencia_mensal.items():
        total_mes = dados["intervencoes"]

        dados["taxa_aceitacao"] = round((dados["aceitacao"] / total_mes) * 100, 2) if total_mes else 0
        dados["taxa_acompanhamento"] = round((dados["acompanhamento"] / total_mes) * 100, 2) if total_mes else 0
        dados["taxa_encaminhamento"] = round((dados["encaminhamento"] / total_mes) * 100, 2) if total_mes else 0
    return Indicadores(
        total_intervencoes=len(registros),
        total_pacientes=len(set(r.paciente_nome for r in registros)),
        por_tipo_atendimento=count_by(db, Intervencao.tipo_atendimento, data_inicio, data_fim, profissional_id, categoria_profissional),
        por_motivo=count_by(db, Intervencao.motivo_atendimento, data_inicio, data_fim, profissional_id, categoria_profissional),
        por_comorbidade=count_by(db, Intervencao.comorbidade, data_inicio, data_fim, profissional_id, categoria_profissional),
        por_resultado=count_by(db, Intervencao.resultado, data_inicio, data_fim, profissional_id, categoria_profissional),
        por_tipo_intervencao=tipos,
        por_mes=meses,
        taxa_aceitacao=taxa_aceitacao,
        taxa_acompanhamento=taxa_acompanhamento,
        taxa_encaminhamento=taxa_encaminhamento,
        por_profissional=por_profissional,
        por_categoria_profissional=por_categoria_profissional,
        tendencia_mensal=tendencia_mensal,
        por_faixa_etaria=faixas_etarias,
    )
@app.get("/relatorios/mensal/pdf")
def relatorio_mensal_pdf(
    ano: int,
    mes: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user)
):
    inicio = date(ano, mes, 1)

    if mes == 12:
        fim = date(ano + 1, 1, 1)
    else:
        fim = date(ano, mes + 1, 1)

    registros = (
        db.query(Intervencao)
        .filter(Intervencao.ativo == True)
        .filter(Intervencao.data_atendimento >= inicio)
        .filter(Intervencao.data_atendimento < fim)
        .all()
    )

    total = len(registros)
    pacientes = len(set(r.paciente_nome for r in registros))

    aceitos = sum(1 for r in registros if r.resultado == "Aceitação")
    acompanhamentos = sum(1 for r in registros if r.resultado == "Acompanhamento do paciente")
    encaminhamentos = sum(1 for r in registros if "Encaminhamentos" in (r.tipos_intervencao or ""))

    taxa_aceitacao = round((aceitos / total) * 100, 2) if total else 0
    taxa_acompanhamento = round((acompanhamentos / total) * 100, 2) if total else 0
    taxa_encaminhamento = round((encaminhamentos / total) * 100, 2) if total else 0

    def contar(campo):
        dados = {}
        for r in registros:
            valor = getattr(r, campo) or "Não informado"
            dados[valor] = dados.get(valor, 0) + 1
        return dados

    def contar_tipos():
        dados = {}
        for r in registros:
            for t in (r.tipos_intervencao or "").split(";"):
                if t:
                    dados[t] = dados.get(t, 0) + 1
        return dados

    por_resultado = contar("resultado")
    por_comorbidade = contar("comorbidade")
    por_tipo = contar_tipos()

    por_profissional = {}
    for r in registros:
        user = db.query(User).filter(User.id == r.profissional_id).first()
        nome = user.nome if user else "Não informado"
        por_profissional[nome] = por_profissional.get(nome, 0) + 1

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    largura, altura = A4

    y = altura - 2 * cm

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(2 * cm, y, "Sistema de Intervenção Farmacêutica")
    y -= 0.7 * cm

    pdf.setFont("Helvetica", 11)
    pdf.drawString(2 * cm, y, f"Relatório mensal - {mes:02d}/{ano}")
    y -= 0.6 * cm
    pdf.drawString(2 * cm, y, "Farmácia Escola - Universidade Federal de Mato Grosso do Sul")
    y -= 1.0 * cm

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(2 * cm, y, "Resumo do período")
    y -= 0.6 * cm

    pdf.setFont("Helvetica", 10)
    resumo = [
        f"Total de intervenções: {total}",
        f"Total de pacientes: {pacientes}",
        f"Taxa de aceitação: {taxa_aceitacao}%",
        f"Taxa de acompanhamento: {taxa_acompanhamento}%",
        f"Taxa de encaminhamento: {taxa_encaminhamento}%",
    ]

    for linha in resumo:
        pdf.drawString(2 * cm, y, linha)
        y -= 0.45 * cm

    def escrever_secao(titulo, dados):
        nonlocal y

        if y < 4 * cm:
            pdf.showPage()
            y = altura - 2 * cm

        y -= 0.4 * cm
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(2 * cm, y, titulo)
        y -= 0.5 * cm

        pdf.setFont("Helvetica", 10)

        if not dados:
            pdf.drawString(2 * cm, y, "Sem registros no período.")
            y -= 0.45 * cm
            return

        for chave, valor in sorted(dados.items(), key=lambda x: str(x[0])):
            if y < 2.5 * cm:
                pdf.showPage()
                y = altura - 2 * cm
                pdf.setFont("Helvetica", 10)

            texto = f"{chave}: {valor}"
            pdf.drawString(2 * cm, y, texto[:110])
            y -= 0.42 * cm

    escrever_secao("Distribuição por resultado", por_resultado)
    escrever_secao("Distribuição por comorbidade", por_comorbidade)
    escrever_secao("Distribuição por tipo de intervenção", por_tipo)
    escrever_secao("Produção por profissional", por_profissional)

    pdf.setFont("Helvetica-Oblique", 8)
    pdf.drawString(2 * cm, 1.5 * cm, f"Gerado por {current.nome} em {datetime.utcnow().strftime('%d/%m/%Y %H:%M')} UTC")

    pdf.save()
    buffer.seek(0)

    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=relatorio_mensal_{ano}_{mes:02d}.pdf"
        }
    )
@app.get("/teste-geral")
def teste_geral():
    return {"ok": True}
