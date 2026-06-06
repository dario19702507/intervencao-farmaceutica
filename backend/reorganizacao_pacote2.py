from pathlib import Path
from datetime import datetime

BACKEND = Path.cwd()
ROUTERS = BACKEND / 'routers'
MODELS = BACKEND / 'models'
SCHEMAS = BACKEND / 'schemas'

CONSULTORIO = ROUTERS / 'consultorio.py'
MAIN = BACKEND / 'main.py'
AGENDA = ROUTERS / 'agenda.py'
README = BACKEND / 'README_reorganizacao_pacote2_resultado.md'

backup_dir = BACKEND / 'backup_reorganizacao_pacote2'
backup_dir.mkdir(exist_ok=True)
stamp = datetime.now().strftime('%Y%m%d_%H%M%S')

for f in [CONSULTORIO, MAIN, AGENDA]:
    if f.exists():
        (backup_dir / f'{f.name}.{stamp}.bak').write_text(f.read_text(encoding='utf-8'), encoding='utf-8')

if not CONSULTORIO.exists():
    raise FileNotFoundError('routers/consultorio.py não encontrado. Execute este script dentro da pasta backend.')

text = CONSULTORIO.read_text(encoding='utf-8')

# Correção pontual da auditoria criada anteriormente na rota POST /agenda.
old = '''    registrar_auditoria(
        db=db,
        current=current,
        modulo="agenda",
        acao="criacao",
        registro_id=evento.id,
        descricao=f"Evento criado para {evento.paciente_nome}"
    )

    db.add(agenda)
    db.commit()
    db.refresh(agenda)
'''
new = '''    db.add(agenda)
    db.flush()
    db.refresh(agenda)

    registrar_auditoria(
        db=db,
        current=current,
        modulo="agenda",
        acao="criacao",
        registro_id=agenda.id,
        descricao=f"Evento criado para {agenda.paciente_nome}"
    )

    db.commit()
    db.refresh(agenda)
'''
if old in text:
    text = text.replace(old, new)

# Adicionar constantes padronizadas após criação do router.
marker = '''router = APIRouter(
    prefix="/consultorio",
    tags=["Consultório Farmacêutico"]
)
'''
constants = '''router = APIRouter(
    prefix="/consultorio",
    tags=["Consultório Farmacêutico"]
)

TIPOS_EVENTO_AGENDA = [
    "retirada_medicamento",
    "renovacao_laudo",
    "adequacao",
    "encerramento",
    "retorno_consultorio",
    "consulta_farmaceutica",
    "risco_interrupcao_tratamento",
]

STATUS_AGENDA = [
    "agendado",
    "notificado",
    "reagendado",
    "realizado",
    "cancelado",
    "renovacao_recomendada",
    "renovacao_urgente",
    "risco_interrupcao_tratamento",
]

SERVICOS_ORIGEM_AGENDA = [
    "dispensacao",
    "renovacao_laudo",
    "consultorio",
    "intervencao",
]
'''
if marker in text and 'TIPOS_EVENTO_AGENDA' not in text:
    text = text.replace(marker, constants)

# Modelo de configuração do sistema.
model_marker = '''class AuditoriaSistema(BaseConsultorio):
    __tablename__ = "auditoria_sistema"

    id = Column(Integer, primary_key=True, index=True)
    usuario = Column(String, nullable=True)
    modulo = Column(String, nullable=False)
    acao = Column(String, nullable=False)
    registro_id = Column(Integer, nullable=True)
    descricao = Column(Text, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
'''
model_with_config = '''class AuditoriaSistema(BaseConsultorio):
    __tablename__ = "auditoria_sistema"

    id = Column(Integer, primary_key=True, index=True)
    usuario = Column(String, nullable=True)
    modulo = Column(String, nullable=False)
    acao = Column(String, nullable=False)
    registro_id = Column(Integer, nullable=True)
    descricao = Column(Text, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

class ConfiguracaoSistema(BaseConsultorio):
    __tablename__ = "configuracoes_sistema"

    id = Column(Integer, primary_key=True, index=True)
    chave = Column(String, unique=True, index=True, nullable=False)
    valor = Column(String, nullable=True)
    descricao = Column(Text, nullable=True)
    atualizado_em = Column(DateTime, default=datetime.utcnow)
'''
if model_marker in text and 'class ConfiguracaoSistema' not in text:
    text = text.replace(model_marker, model_with_config)

# Funções auxiliares de configuração.
util_marker = '''def registrar_auditoria(
    db: Session,
    current,
    modulo: str,
    acao: str,
    registro_id: Optional[int] = None,
    descricao: Optional[str] = None
):
    usuario = (
        getattr(current, "nome", None)
        or getattr(current, "email", None)
        or "sistema"
    )

    auditoria = AuditoriaSistema(
        usuario=usuario,
        modulo=modulo,
        acao=acao,
        registro_id=registro_id,
        descricao=descricao,
        criado_em=datetime.utcnow()
    )

    db.add(auditoria)    
'''
util_with_config = '''def registrar_auditoria(
    db: Session,
    current,
    modulo: str,
    acao: str,
    registro_id: Optional[int] = None,
    descricao: Optional[str] = None
):
    usuario = (
        getattr(current, "nome", None)
        or getattr(current, "email", None)
        or "sistema"
    )

    auditoria = AuditoriaSistema(
        usuario=usuario,
        modulo=modulo,
        acao=acao,
        registro_id=registro_id,
        descricao=descricao,
        criado_em=datetime.utcnow()
    )

    db.add(auditoria)


def obter_configuracao(db: Session, chave: str, valor_padrao=None):
    config = db.query(ConfiguracaoSistema).filter(
        ConfiguracaoSistema.chave == chave
    ).first()

    if not config:
        return valor_padrao

    return config.valor


def obter_configuracao_int(db: Session, chave: str, valor_padrao: int):
    valor = obter_configuracao(db, chave, valor_padrao)

    try:
        return int(valor)
    except Exception:
        return valor_padrao


def criar_configuracoes_padrao(db: Session):
    configuracoes = [
        ("dias_alerta_renovacao", "60", "Dias antes do vencimento do laudo para alerta de renovação recomendada."),
        ("dias_alerta_urgente", "30", "Dias antes do vencimento do laudo para alerta urgente."),
        ("dias_alerta_disp_atrasada", "5", "Dias de atraso para reforço de alerta de dispensação."),
        ("whatsapp_habilitado", "false", "Habilita ou desabilita envio real via WhatsApp."),
    ]

    for chave, valor, descricao in configuracoes:
        existente = db.query(ConfiguracaoSistema).filter(
            ConfiguracaoSistema.chave == chave
        ).first()

        if not existente:
            db.add(ConfiguracaoSistema(
                chave=chave,
                valor=valor,
                descricao=descricao,
                atualizado_em=datetime.utcnow()
            ))
'''
if util_marker in text and 'def obter_configuracao(' not in text:
    text = text.replace(util_marker, util_with_config)

# Criar rota de configurações para conferência/uso futuro.
insert_before = '@router.get("/me")'
config_routes = '''@router.get("/configuracoes")
def listar_configuracoes_sistema(
    db: Session = Depends(get_db_consultorio),
    current=Depends(get_current_user_consultorio)
):
    criar_configuracoes_padrao(db)
    db.commit()

    configuracoes = db.query(ConfiguracaoSistema).order_by(
        ConfiguracaoSistema.chave.asc()
    ).all()

    return {
        "total": len(configuracoes),
        "configuracoes": configuracoes
    }

'''
if insert_before in text and '@router.get("/configuracoes")' not in text:
    text = text.replace(insert_before, config_routes + insert_before)

# Usar configurações nos alertas de renovação.
text = text.replace(
'''        if 31 <= dias_para_vencimento <= 60:
            novo_status = "renovacao_recomendada"

        elif 0 <= dias_para_vencimento <= 30:
            novo_status = "renovacao_urgente"
''',
'''        dias_alerta_renovacao = obter_configuracao_int(
            db,
            "dias_alerta_renovacao",
            60
        )

        dias_alerta_urgente = obter_configuracao_int(
            db,
            "dias_alerta_urgente",
            30
        )

        if dias_alerta_urgente < dias_para_vencimento <= dias_alerta_renovacao:
            novo_status = "renovacao_recomendada"

        elif 0 <= dias_para_vencimento <= dias_alerta_urgente:
            novo_status = "renovacao_urgente"
''')

# Auditoria no PUT /agenda/{agenda_id}, se ainda não existir.
put_commit = '''    db.commit()
    db.refresh(agenda)

    return {
        "mensagem": "Agendamento atualizado.",
'''
put_audit = '''    registrar_auditoria(
        db=db,
        current=current,
        modulo="agenda",
        acao="atualizacao",
        registro_id=agenda.id,
        descricao=f"Agendamento atualizado para {agenda.paciente_nome}"
    )

    db.commit()
    db.refresh(agenda)

    return {
        "mensagem": "Agendamento atualizado.",
'''
if put_commit in text and 'acao="atualizacao"' not in text[text.find('@router.put("/agenda/{agenda_id}")'):text.find('@router.post("/agenda/{agenda_id}/status")')]:
    text = text.replace(put_commit, put_audit, 1)

# Auditoria no status.
status_commit = '''    db.commit()
    db.refresh(agenda)

    return {
        "mensagem": "Status atualizado.",
'''
status_audit = '''    registrar_auditoria(
        db=db,
        current=current,
        modulo="agenda",
        acao="alteracao_status",
        registro_id=agenda.id,
        descricao=f"Status alterado para {agenda.status} - {agenda.paciente_nome}"
    )

    db.commit()
    db.refresh(agenda)

    return {
        "mensagem": "Status atualizado.",
'''
if status_commit in text and 'acao="alteracao_status"' not in text[text.find('@router.post("/agenda/{agenda_id}/status")'):text.find('@router.get("/agenda-retornos")')]:
    text = text.replace(status_commit, status_audit, 1)

# Corrigir retorno de obter_ou_criar_paciente_agenda caso esteja com return vazio.
text = text.replace('''    db.add(paciente)
    db.flush()
    db.refresh(paciente)

    return
''', '''    db.add(paciente)
    db.flush()
    db.refresh(paciente)

    return paciente
''')

CONSULTORIO.write_text(text, encoding='utf-8')

# Criar router agenda.py como documento técnico/stub seguro, sem registrar no main ainda para evitar rotas duplicadas.
AGENDA.write_text('''"""Router planejado para o módulo Agenda Integrada.

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
''', encoding='utf-8')

README.write_text(f'''# Reorganização Pacote 2 aplicada em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

Este pacote fez uma refatoração conservadora, sem remover rotas do `consultorio.py`.

## Alterações realizadas

1. Criou backup em `backup_reorganizacao_pacote2/`.
2. Criou `routers/agenda.py` como destino planejado das rotas da Agenda.
3. Corrigiu a auditoria da rota `POST /consultorio/agenda`:
   - antes usava `evento.id`, mas o objeto correto é `agenda`;
   - agora usa `db.flush()` antes de registrar auditoria.
4. Adicionou listas padronizadas:
   - `TIPOS_EVENTO_AGENDA`;
   - `STATUS_AGENDA`;
   - `SERVICOS_ORIGEM_AGENDA`.
5. Criou o modelo `ConfiguracaoSistema`.
6. Criou funções auxiliares:
   - `obter_configuracao()`;
   - `obter_configuracao_int()`;
   - `criar_configuracoes_padrao()`.
7. Criou rota:
   - `GET /consultorio/configuracoes`.
8. Ajustou alertas de renovação para usar configurações:
   - `dias_alerta_renovacao`;
   - `dias_alerta_urgente`.
9. Adicionou auditoria em:
   - atualização de agenda;
   - alteração de status da agenda.
10. Corrigiu `obter_ou_criar_paciente_agenda()` para retornar o paciente criado.

## Testes sugeridos

```bash
python -m py_compile routers/consultorio.py
uvicorn main:app --reload
```

Depois testar no Swagger ou frontend:

- `GET /consultorio/configuracoes`
- `POST /consultorio/agenda`
- `PUT /consultorio/agenda/{{agenda_id}}`
- `POST /consultorio/agenda/{{agenda_id}}/status`
- verificar auditoria:

```sql
SELECT * FROM auditoria_sistema ORDER BY id DESC LIMIT 20;
```

## Observação importante

Este pacote ainda não removeu as rotas de Agenda do `consultorio.py`. A extração real para `routers/agenda.py` deve ser feita no próximo pacote, após estes testes passarem.
''', encoding='utf-8')

print('Pacote 2 aplicado com sucesso.')
print('Backup criado em:', backup_dir)
print('Leia:', README)
