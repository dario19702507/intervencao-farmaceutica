from datetime import datetime

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    perfil = Column(String, default="farmaceutico")  # admin, farmaceutico, leitor
    categoria_profissional = Column(String, default="Farmacêutico")
    crf = Column(String, nullable=True)
    assinatura_digital = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    intervencoes = relationship(
    "Intervencao",
    foreign_keys="Intervencao.profissional_id",
    back_populates="usuario"
)

class Intervencao(Base):
    __tablename__ = "intervencoes"
    id = Column(Integer, primary_key=True, index=True)
    data_atendimento = Column(Date, nullable=False, index=True)
    paciente_nome = Column(String, nullable=False, index=True)
    data_nascimento = Column(Date, nullable=True)
    tipo_atendimento = Column(String, nullable=False)  # Presencial/Remoto
    motivo_atendimento = Column(String, nullable=False)
    comorbidade = Column(String, nullable=False)
    tipos_intervencao = Column(Text, nullable=False)  # separados por ;
    resultado = Column(String, nullable=False)
    observacoes = Column(Text, nullable=True)
    profissional_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    supervisor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ativo = Column(Boolean, default=True)
    motivo_inativacao = Column(Text, nullable=True)
    usuario = relationship("User", foreign_keys=[profissional_id], back_populates="intervencoes")
    criador = relationship("User", foreign_keys=[created_by])
    atualizador = relationship("User", foreign_keys=[updated_by])
    supervisor = relationship("User", foreign_keys=[supervisor_id])
