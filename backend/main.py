import csv
import io
import os
from datetime import datetime, timedelta, date
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, status, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./intervencoes.db")
SECRET_KEY = os.getenv("SECRET_KEY", "troque-esta-chave-em-producao")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    perfil = Column(String, default="farmaceutico")  # admin, farmaceutico, leitor
    created_at = Column(DateTime, default=datetime.utcnow)
    intervencoes = relationship("Intervencao", back_populates="usuario")

class Intervencao(Base):
    __tablename__ = "intervencoes"
    id = Column(Integer, primary_key=True, index=True)
    data_atendimento = Column(Date, nullable=False, index=True)
    paciente_nome = Column(String, nullable=False, index=True)
    data_nascimento = Column(Date, nullable=False)
    tipo_atendimento = Column(String, nullable=False)  # Presencial/Remoto
    motivo_atendimento = Column(String, nullable=False)
    comorbidade = Column(String, nullable=False)
    tipos_intervencao = Column(Text, nullable=False)  # separados por ;
    resultado = Column(String, nullable=False)
    observacoes = Column(Text, nullable=True)
    profissional_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    usuario = relationship("User", back_populates="intervencoes")

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sistema de Intervenção Farmacêutica", version="1.0.0")

allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserCreate(BaseModel):
    nome: str
    email: str
    password: str = Field(min_length=6)
    perfil: str = "farmaceutico"

class PasswordReset(BaseModel):
    password: str = Field(min_length=6)

class UserOut(BaseModel):
    id: int
    nome: str
    email: str
    perfil: str
    class Config:
        from_attributes = True

class IntervencaoCreate(BaseModel):
    data_atendimento: date
    paciente_nome: str
    data_nascimento: date
    tipo_atendimento: str
    motivo_atendimento: str
    comorbidade: str
    tipos_intervencao: List[str]
    resultado: str
    observacoes: Optional[str] = None

class IntervencaoOut(IntervencaoCreate):
    id: int
    profissional: str
    created_at: datetime

class Indicadores(BaseModel):
    total_intervencoes: int
    total_pacientes: int
    por_tipo_atendimento: dict
    por_motivo: dict
    por_comorbidade: dict
    por_resultado: dict
    por_tipo_intervencao: dict
    por_mes: dict

MOTIVOS = ["Documentação (inclusão/renovação/adequação)", "Dúvidas de paciente"]
COMORBIDADES = ["Esclerose múltipla", "Esclerose Sistêmica", "Esclerose Lateral Amiotrófica", "Asma/DPOC", "Outro"]
TIPOS_INTERVENCAO = ["Posologia", "Acondicionamento", "Técnica de uso", "Reação Adversa a Medicamentos (RAM)", "Erro de prescrição", "Orientação documental", "Encaminhamentos", "Educação em Saúde", "Orientação ao profissional da saúde", "Parâmetros clínicos"]
RESULTADOS = ["Aceitação", "Acompanhamento do paciente", "Outro"]

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def hash_password(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

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
    if user.perfil != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito ao administrador")

@app.on_event("startup")
def seed_admin():
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.email == "admin@farmacia.local").first():
            db.add(User(nome="Administrador", email="admin@farmacia.local", hashed_password=hash_password("admin123"), perfil="admin"))
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
    user = User(nome=payload.nome, email=payload.email, hashed_password=hash_password(payload.password), perfil=payload.perfil)
    db.add(user); db.commit(); db.refresh(user)
    return user

@app.get("/users", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    ensure_admin(current)
    return db.query(User).order_by(User.nome.asc()).all()


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

@app.get("/opcoes")
def opcoes():
    return {"motivos": MOTIVOS, "comorbidades": COMORBIDADES, "tipos_intervencao": TIPOS_INTERVENCAO, "resultados": RESULTADOS, "tipos_atendimento": ["Presencial", "Remoto"]}

@app.post("/intervencoes", response_model=IntervencaoOut)
def criar_intervencao(payload: IntervencaoCreate, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
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
    item = db.query(Intervencao).filter(Intervencao.id == intervencao_id).first()

    if not item:
        raise HTTPException(status_code=404, detail="Intervenção não encontrada")

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
@app.get("/intervencoes/exportar/csv")
def exportar_intervencoes_csv(
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user)
):
    q = db.query(Intervencao, User.nome).join(User, User.id == Intervencao.profissional_id)

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
            i.paciente_nome,
            i.data_nascimento,
            i.tipo_atendimento,
            i.motivo_atendimento,
            i.comorbidade,
            i.tipos_intervencao,
            i.resultado,
            i.observacoes or "",
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
@app.get("/intervencoes", response_model=List[IntervencaoOut])
def listar_intervencoes(
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    profissional_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user)
):
    q = db.query(Intervencao, User.nome).join(User, User.id == Intervencao.profissional_id)

    if data_inicio:
        q = q.filter(Intervencao.data_atendimento >= data_inicio)

    if data_fim:
        q = q.filter(Intervencao.data_atendimento <= data_fim)

    if profissional_id:
        q = q.filter(Intervencao.profissional_id == profissional_id)

    rows = q.order_by(Intervencao.data_atendimento.desc()).limit(500).all()

    return [
        IntervencaoOut(
            id=i.id,
            data_atendimento=i.data_atendimento,
            paciente_nome=i.paciente_nome,
            data_nascimento=i.data_nascimento,
            tipo_atendimento=i.tipo_atendimento,
            motivo_atendimento=i.motivo_atendimento,
            comorbidade=i.comorbidade,
            tipos_intervencao=i.tipos_intervencao.split(";"),
            resultado=i.resultado,
            observacoes=i.observacoes,
            profissional=nome,
            created_at=i.created_at
        )
        for i, nome in rows
    ]

def count_by(db, column, data_inicio=None, data_fim=None, profissional_id=None):
    q = db.query(column, func.count(Intervencao.id)).group_by(column)
    if data_inicio: q = q.filter(Intervencao.data_atendimento >= data_inicio)
    if data_fim: q = q.filter(Intervencao.data_atendimento <= data_fim)
    if profissional_id: q = q.filter(Intervencao.profissional_id == profissional_id)
    return {str(k): v for k, v in q.all()}

@app.get("/indicadores", response_model=Indicadores)
def indicadores(
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    profissional_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user)
):
    q = db.query(Intervencao)
    if data_inicio: q = q.filter(Intervencao.data_atendimento >= data_inicio)
    if data_fim: q = q.filter(Intervencao.data_atendimento <= data_fim)
    if profissional_id: q = q.filter(Intervencao.profissional_id == profissional_id)
    registros = q.all()
    tipos = {}
    meses = {}
    for r in registros:
        for t in r.tipos_intervencao.split(";"):
            tipos[t] = tipos.get(t, 0) + 1
        chave_mes = r.data_atendimento.strftime("%Y-%m")
        meses[chave_mes] = meses.get(chave_mes, 0) + 1
    return Indicadores(
        total_intervencoes=len(registros),
        total_pacientes=len(set(r.paciente_nome for r in registros)),
        por_tipo_atendimento=count_by(db, Intervencao.tipo_atendimento, data_inicio, data_fim, profissional_id),
        por_motivo=count_by(db, Intervencao.motivo_atendimento, data_inicio, data_fim, profissional_id),
        por_comorbidade=count_by(db, Intervencao.comorbidade, data_inicio, data_fim, profissional_id),
        por_resultado=count_by(db, Intervencao.resultado, data_inicio, data_fim, profissional_id),
        por_tipo_intervencao=tipos,
        por_mes=meses,
    )
