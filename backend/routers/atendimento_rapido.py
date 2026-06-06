"""
Router atendimento_rapido.py.

Arquivo estrutural criado no Pacote de Reorganizacao 1.
As rotas ainda continuam em routers/consultorio.py.
"""

from fastapi import APIRouter

router = APIRouter(
    prefix="/consultorio",
    tags=["Atendimento Rapido"]
)
