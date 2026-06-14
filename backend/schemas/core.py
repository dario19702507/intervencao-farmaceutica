from datetime import date, datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserOut(BaseModel):
    id: int
    nome: str
    email: str
    perfil: str
    categoria_profissional: Optional[str] = None
    permissoes: Optional[Dict[str, Dict[str, bool]]] = None

    class Config:
        from_attributes = True

class PasswordReset(BaseModel):
    password: str = Field(min_length=6)

class ChangeOwnPassword(BaseModel):
    senha_atual: str
    nova_senha: str = Field(min_length=6)

class InativarPayload(BaseModel):
    motivo: str = Field(min_length=3)

class IntervencaoCreate(BaseModel):
    data_atendimento: date
    paciente_nome: str
    data_nascimento: Optional[date] = None
    tipo_atendimento: str
    motivo_atendimento: str
    comorbidade: str
    tipos_intervencao: List[str]
    resultado: str
    observacoes: Optional[str] = None
    supervisor_id: Optional[int] = None

class IntervencaoOut(IntervencaoCreate):
    data_nascimento: Optional[date] = None
    id: int
    profissional: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    criado_por: Optional[str] = None
    atualizado_por: Optional[str] = None
    supervisor_nome: Optional[str] = None
    motivo_inativacao: Optional[str] = None

class Indicadores(BaseModel):
    total_intervencoes: int
    total_pacientes: int
    por_tipo_atendimento: dict
    por_motivo: dict
    por_comorbidade: dict
    por_resultado: dict
    por_tipo_intervencao: dict
    por_mes: dict
    taxa_aceitacao: float
    taxa_acompanhamento: float
    taxa_encaminhamento: float
    por_profissional: dict
    por_categoria_profissional: dict
    tendencia_mensal: dict
    por_faixa_etaria: dict


class UserCreate(BaseModel):
    nome: str
    email: str
    password: str = Field(min_length=6)
    perfil: str = "farmaceutico"
    categoria_profissional: str = "Farmacêutico"


class UserUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[str] = None
    perfil: Optional[str] = None
    categoria_profissional: Optional[str] = None
