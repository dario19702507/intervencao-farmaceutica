"""Router planejado para o módulo Agenda Integrada.

Pacote de Reorganização 2
-------------------------
Este arquivo é criado como ponto de destino para a próxima etapa da refatoração.
As rotas ainda permanecem em routers/consultorio.py para evitar quebra ou duplicidade.

Rotas que serão migradas no Pacote 3:
- GET/POST /consultorio/agenda
- PUT /consultorio/agenda/{agenda_id}
- POST /consultorio/agenda/{agenda_id}/status
- rotas de capacidade
- rotas de alertas e notificações da agenda

A migração será feita mantendo o mesmo prefixo /consultorio para não alterar o frontend.
"""

from fastapi import APIRouter

router = APIRouter(
    prefix="/consultorio",
    tags=["Agenda Integrada"]
)

# As rotas serão movidas gradualmente no próximo pacote.
