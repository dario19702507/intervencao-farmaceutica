
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return path.read_text(encoding='utf-8')

def write(path, text):
    path.write_text(text, encoding='utf-8')
    print(f"OK: {path}")

def replace_once(text, old, new, label):
    if new.strip() in text:
        print(f"OK: {label} já aplicado")
        return text
    if old not in text:
        print(f"AVISO: padrão não encontrado para {label}")
        return text
    return text.replace(old, new, 1)

def insert_after(text, marker, insert, label):
    if insert.strip() in text:
        print(f"OK: {label} já aplicado")
        return text
    if marker not in text:
        print(f"AVISO: marcador não encontrado para {label}")
        return text
    return text.replace(marker, marker + insert, 1)

# 1) Models
models = ROOT / 'backend' / 'models' / 'consultorio_models.py'
text = read(models)
marker = '    observacoes = Column(Text, nullable=True)\n\n    ativo = Column(Boolean, default=True)\n'
insert = '''    observacoes = Column(Text, nullable=True)\n\n    # Passo 14E.2C.5B.1 — ciclo de vida da farmacoterapia\n    status_farmacoterapia = Column(String, default="EM_USO")\n    data_status = Column(DateTime, nullable=True)\n    motivo_status = Column(String, nullable=True)\n    tipo_suspensao = Column(String, nullable=True)\n    observacao_status = Column(Text, nullable=True)\n    substituido_por_medicamento_id = Column(Integer, nullable=True)\n    prm_relacionado_id = Column(Integer, nullable=True)\n    intervencao_relacionada_id = Column(Integer, nullable=True)\n\n    ativo = Column(Boolean, default=True)\n'''
text = replace_once(text, marker, insert, 'campos de ciclo de vida em MedicamentoUso')
write(models, text)

# 2) Schemas
schemas = ROOT / 'backend' / 'schemas' / 'consultorio_schemas.py'
text = read(schemas)
insert = '''\n\nclass MedicamentoTrocaCreate(BaseModel):\n    novo_medicamento: MedicamentoUsoCreate\n    data_troca: Optional[date] = None\n    motivo_troca: str\n    prm_relacionado_id: Optional[int] = None\n    intervencao_relacionada_id: Optional[int] = None\n    observacao: Optional[str] = None\n\n\nclass MedicamentoSuspensaoCreate(BaseModel):\n    data_suspensao: Optional[date] = None\n    motivo_suspensao: str\n    tipo_suspensao: str = "DEFINITIVA"\n    prm_relacionado_id: Optional[int] = None\n    intervencao_relacionada_id: Optional[int] = None\n    observacao: Optional[str] = None\n\n\nclass MedicamentoEncerramentoCreate(BaseModel):\n    data_encerramento: Optional[date] = None\n    motivo_encerramento: str = "FIM_DO_TRATAMENTO"\n    prm_relacionado_id: Optional[int] = None\n    intervencao_relacionada_id: Optional[int] = None\n    observacao: Optional[str] = None\n'''
marker = 'class IntervencaoFarmacoterapiaCreate(BaseModel):\n'
text = insert_after(text, '\n\nclass IntervencaoFarmacoterapiaCreate(BaseModel):\n', insert + '\n', 'schemas de troca/suspensão/encerramento')
write(schemas, text)

# 3) Migrations
mig = ROOT / 'backend' / 'migrations.py'
text = read(mig)
marker = '        _adicionar_coluna_se_nao_existir(conn, "medicamentos_uso", "uso_se_necessario BOOLEAN DEFAULT FALSE")\n'
insert = '''\n        # Passo 14E.2C.5B.1 — ciclo de vida da farmacoterapia\n        _adicionar_coluna_se_nao_existir(conn, "medicamentos_uso", "status_farmacoterapia VARCHAR DEFAULT 'EM_USO'")\n        _adicionar_coluna_se_nao_existir(conn, "medicamentos_uso", "data_status DATETIME")\n        _adicionar_coluna_se_nao_existir(conn, "medicamentos_uso", "motivo_status VARCHAR")\n        _adicionar_coluna_se_nao_existir(conn, "medicamentos_uso", "tipo_suspensao VARCHAR")\n        _adicionar_coluna_se_nao_existir(conn, "medicamentos_uso", "observacao_status TEXT")\n        _adicionar_coluna_se_nao_existir(conn, "medicamentos_uso", "substituido_por_medicamento_id INTEGER")\n        _adicionar_coluna_se_nao_existir(conn, "medicamentos_uso", "prm_relacionado_id INTEGER")\n        _adicionar_coluna_se_nao_existir(conn, "medicamentos_uso", "intervencao_relacionada_id INTEGER")\n'''
text = insert_after(text, marker, insert, 'migrações de ciclo de vida')
write(mig, text)

# 4) Router farmacoterapia
router = ROOT / 'backend' / 'routers' / 'farmacoterapia.py'
text = read(router)
text = replace_once(text, 'from fastapi import APIRouter, Depends, HTTPException\n', 'from fastapi import APIRouter, Depends, HTTPException\nfrom datetime import datetime, time\n', 'import datetime')
text = replace_once(text, '    MedicamentoUsoCreate,\n    IntervencaoFarmacoterapiaCreate,\n', '    MedicamentoUsoCreate,\n    MedicamentoTrocaCreate,\n    MedicamentoSuspensaoCreate,\n    MedicamentoEncerramentoCreate,\n    IntervencaoFarmacoterapiaCreate,\n', 'imports schemas ciclo de vida')
marker = '_adicionar_coluna_farmacoterapia_se_nao_existir("medicamentos_uso", "uso_se_necessario BOOLEAN DEFAULT FALSE")\n'
insert = '''_adicionar_coluna_farmacoterapia_se_nao_existir("medicamentos_uso", "status_farmacoterapia VARCHAR DEFAULT 'EM_USO'")\n_adicionar_coluna_farmacoterapia_se_nao_existir("medicamentos_uso", "data_status DATETIME")\n_adicionar_coluna_farmacoterapia_se_nao_existir("medicamentos_uso", "motivo_status VARCHAR")\n_adicionar_coluna_farmacoterapia_se_nao_existir("medicamentos_uso", "tipo_suspensao VARCHAR")\n_adicionar_coluna_farmacoterapia_se_nao_existir("medicamentos_uso", "observacao_status TEXT")\n_adicionar_coluna_farmacoterapia_se_nao_existir("medicamentos_uso", "substituido_por_medicamento_id INTEGER")\n_adicionar_coluna_farmacoterapia_se_nao_existir("medicamentos_uso", "prm_relacionado_id INTEGER")\n_adicionar_coluna_farmacoterapia_se_nao_existir("medicamentos_uso", "intervencao_relacionada_id INTEGER")\n'''
text = insert_after(text, marker, insert, 'ALTER TABLE ciclo de vida no router')
const_marker = 'FREQUENCIAS_USO = [\n    "1x ao dia", "2x ao dia", "3x ao dia", "4x ao dia", "a cada 6 horas",\n    "a cada 8 horas", "a cada 12 horas", "semanal", "quinzenal", "mensal",\n    "antes das refeições", "após refeições", "se necessário"\n]\n'
const_insert = '''\n\nSTATUS_FARMACOTERAPIA = ["EM_USO", "TROCADO", "SUSPENSO", "ENCERRADO"]\nMOTIVOS_TROCA = [\n    "INEFETIVIDADE", "REACAO_ADVERSA", "INTERACAO_MEDICAMENTOSA",\n    "DESABASTECIMENTO", "AJUSTE_TERAPEUTICO", "SIMPLIFICACAO_ESQUEMA", "OUTRO"\n]\nMOTIVOS_SUSPENSAO = [\n    "EVENTO_ADVERSO", "CONTRAINDICACAO", "FIM_DO_TRATAMENTO",\n    "NAO_ADESAO", "DECISAO_MEDICA", "DECISAO_PACIENTE", "OUTRO"\n]\nMOTIVOS_ENCERRAMENTO = [\n    "FIM_DO_TRATAMENTO", "TRATAMENTO_CONCLUIDO", "CURSO_CURTO_FINALIZADO", "OUTRO"\n]\nTIPOS_SUSPENSAO = ["TEMPORARIA", "DEFINITIVA"]\n\n\ndef _data_para_datetime(valor):\n    if not valor:\n        return datetime.utcnow()\n    return datetime.combine(valor, time.min)\n'''
text = insert_after(text, const_marker, const_insert, 'constantes ciclo de vida')
# opcoes add keys
old = '        "orientacao_catalogo": "Use catalogo_medicamento_id quando houver correspondência; mantenha nome_medicamento para registro manual quando necessário.",\n    }\n'
new = '        "orientacao_catalogo": "Use catalogo_medicamento_id quando houver correspondência; mantenha nome_medicamento para registro manual quando necessário.",\n        "status_farmacoterapia": STATUS_FARMACOTERAPIA,\n        "motivos_troca": MOTIVOS_TROCA,\n        "motivos_suspensao": MOTIVOS_SUSPENSAO,\n        "motivos_encerramento": MOTIVOS_ENCERRAMENTO,\n        "tipos_suspensao": TIPOS_SUSPENSAO,\n    }\n'
text = replace_once(text, old, new, 'opções de ciclo de vida')
# add endpoints after listar_medicamentos_uso return medicamentos block
marker = '''    return medicamentos\n\n\n@router.get("/paciente-clinico/{paciente_id}/avaliacao-polifarmacia")\n'''
insert = r'''
    return medicamentos


@router.post("/medicamentos/{medicamento_id}/trocar")
def trocar_medicamento_uso(
    medicamento_id: int,
    dados: MedicamentoTrocaCreate,
    db: Session = Depends(get_db_consultorio),
    current: UserConsultorio = Depends(get_current_user_consultorio)
):
    exigir_farmaceutico_ou_admin(current)

    medicamento = db.query(MedicamentoUso).filter(MedicamentoUso.id == medicamento_id).first()
    if not medicamento:
        raise HTTPException(status_code=404, detail="Medicamento não encontrado")

    payload_novo = _normalizar_payload_medicamento(dados.novo_medicamento, db)
    novo = MedicamentoUso(
        paciente_clinico_id=medicamento.paciente_clinico_id,
        **payload_novo,
    )
    novo.status_farmacoterapia = "EM_USO"

    db.add(novo)
    db.flush()

    medicamento.status_farmacoterapia = "TROCADO"
    medicamento.data_status = _data_para_datetime(dados.data_troca)
    medicamento.motivo_status = dados.motivo_troca
    medicamento.observacao_status = dados.observacao
    medicamento.substituido_por_medicamento_id = novo.id
    medicamento.prm_relacionado_id = dados.prm_relacionado_id
    medicamento.intervencao_relacionada_id = dados.intervencao_relacionada_id

    db.commit()
    db.refresh(medicamento)
    db.refresh(novo)

    return {
        "mensagem": "Troca de medicamento registrada com sucesso.",
        "medicamento_anterior": medicamento,
        "medicamento_novo": novo,
    }


@router.post("/medicamentos/{medicamento_id}/suspender")
def suspender_medicamento_uso(
    medicamento_id: int,
    dados: MedicamentoSuspensaoCreate,
    db: Session = Depends(get_db_consultorio),
    current: UserConsultorio = Depends(get_current_user_consultorio)
):
    exigir_farmaceutico_ou_admin(current)

    medicamento = db.query(MedicamentoUso).filter(MedicamentoUso.id == medicamento_id).first()
    if not medicamento:
        raise HTTPException(status_code=404, detail="Medicamento não encontrado")

    medicamento.status_farmacoterapia = "SUSPENSO"
    medicamento.data_status = _data_para_datetime(dados.data_suspensao)
    medicamento.motivo_status = dados.motivo_suspensao
    medicamento.tipo_suspensao = dados.tipo_suspensao
    medicamento.observacao_status = dados.observacao
    medicamento.prm_relacionado_id = dados.prm_relacionado_id
    medicamento.intervencao_relacionada_id = dados.intervencao_relacionada_id

    db.commit()
    db.refresh(medicamento)

    return {"mensagem": "Suspensão de medicamento registrada com sucesso.", "medicamento": medicamento}


@router.post("/medicamentos/{medicamento_id}/encerrar")
def encerrar_medicamento_uso(
    medicamento_id: int,
    dados: MedicamentoEncerramentoCreate,
    db: Session = Depends(get_db_consultorio),
    current: UserConsultorio = Depends(get_current_user_consultorio)
):
    exigir_farmaceutico_ou_admin(current)

    medicamento = db.query(MedicamentoUso).filter(MedicamentoUso.id == medicamento_id).first()
    if not medicamento:
        raise HTTPException(status_code=404, detail="Medicamento não encontrado")

    medicamento.status_farmacoterapia = "ENCERRADO"
    medicamento.data_status = _data_para_datetime(dados.data_encerramento)
    medicamento.motivo_status = dados.motivo_encerramento
    medicamento.observacao_status = dados.observacao
    medicamento.prm_relacionado_id = dados.prm_relacionado_id
    medicamento.intervencao_relacionada_id = dados.intervencao_relacionada_id

    db.commit()
    db.refresh(medicamento)

    return {"mensagem": "Encerramento de medicamento registrado com sucesso.", "medicamento": medicamento}


@router.get("/paciente-clinico/{paciente_id}/avaliacao-polifarmacia")
'''
text = replace_once(text, marker, insert, 'endpoints troca/suspensão/encerramento')
write(router, text)

# 5) Service cuidado_farmaceutico serialization/timeline
service = ROOT / 'backend' / 'services' / 'cuidado_farmaceutico.py'
text = read(service)
old = '''        "observacoes": m.observacoes,\n        "ativo": bool(m.ativo),\n        "criado_em": _dt(m.criado_em),\n    }\n'''
new = '''        "observacoes": m.observacoes,\n        "status_farmacoterapia": getattr(m, "status_farmacoterapia", None) or "EM_USO",\n        "data_status": _dt(getattr(m, "data_status", None)),\n        "motivo_status": getattr(m, "motivo_status", None),\n        "tipo_suspensao": getattr(m, "tipo_suspensao", None),\n        "observacao_status": getattr(m, "observacao_status", None),\n        "substituido_por_medicamento_id": getattr(m, "substituido_por_medicamento_id", None),\n        "prm_relacionado_id": getattr(m, "prm_relacionado_id", None),\n        "intervencao_relacionada_id": getattr(m, "intervencao_relacionada_id", None),\n        "ativo": bool(m.ativo),\n        "criado_em": _dt(m.criado_em),\n    }\n'''
text = replace_once(text, old, new, 'serialização ciclo de vida medicamento')
old = '''            status="ATIVO" if med.ativo else "INATIVO",\n            origem="medicamentos_uso",\n            referencia_tipo="medicamento_uso",\n            referencia_id=med.id,\n            detalhes={"indicacao": med.indicacao, "uso_continuo": med.uso_continuo, "adesao": med.adesao_referida},\n        ))\n'''
new = '''            status=getattr(med, "status_farmacoterapia", None) or ("ATIVO" if med.ativo else "INATIVO"),\n            origem="medicamentos_uso",\n            referencia_tipo="medicamento_uso",\n            referencia_id=med.id,\n            detalhes={\n                "indicacao": med.indicacao,\n                "uso_continuo": med.uso_continuo,\n                "adesao": med.adesao_referida,\n                "motivo_status": getattr(med, "motivo_status", None),\n                "tipo_suspensao": getattr(med, "tipo_suspensao", None),\n                "substituido_por_medicamento_id": getattr(med, "substituido_por_medicamento_id", None),\n                "prm_relacionado_id": getattr(med, "prm_relacionado_id", None),\n                "intervencao_relacionada_id": getattr(med, "intervencao_relacionada_id", None),\n            },\n        ))\n        if getattr(med, "data_status", None) and (getattr(med, "status_farmacoterapia", None) or "EM_USO") in ("TROCADO", "SUSPENSO", "ENCERRADO"):\n            _adicionar_evento(eventos, _timeline_evento(\n                data=med.data_status,\n                categoria="FARMACOTERAPIA",\n                tipo=f"MEDICAMENTO_{med.status_farmacoterapia}",\n                titulo=med.nome_medicamento,\n                descricao=(getattr(med, "observacao_status", None) or getattr(med, "motivo_status", None)),\n                status=med.status_farmacoterapia,\n                origem="medicamentos_uso",\n                referencia_tipo="medicamento_uso",\n                referencia_id=med.id,\n                detalhes={\n                    "motivo_status": getattr(med, "motivo_status", None),\n                    "tipo_suspensao": getattr(med, "tipo_suspensao", None),\n                    "substituido_por_medicamento_id": getattr(med, "substituido_por_medicamento_id", None),\n                    "prm_relacionado_id": getattr(med, "prm_relacionado_id", None),\n                    "intervencao_relacionada_id": getattr(med, "intervencao_relacionada_id", None),\n                },\n            ))\n'''
text = replace_once(text, old, new, 'timeline do ciclo de vida do medicamento')
write(service, text)

# 6) Frontend Consultorio.jsx
front = ROOT / 'frontend' / 'src' / 'pages' / 'consultorio' / 'Consultorio.jsx'
text = read(front)
# add states after novoMedicamento state block
marker = '''  const [novoMedicamento, setNovoMedicamento] = useState({\n    catalogo_medicamento_id: "",\n    nome_medicamento: "",\n    dose: "",\n    via: "",\n    frequencia: "",\n    frequencia_uso: "",\n    horarios_uso: "",\n    uso_se_necessario: false,\n    indicacao: "",\n    uso_continuo: true,\n    adesao_referida: "",\n    observacoes: "",\n  });\n'''
insert = '''\n\n  const [opcoesCicloVidaMedicamento, setOpcoesCicloVidaMedicamento] = useState({\n    status_farmacoterapia: ["EM_USO", "TROCADO", "SUSPENSO", "ENCERRADO"],\n    motivos_troca: [],\n    motivos_suspensao: [],\n    motivos_encerramento: [],\n    tipos_suspensao: ["TEMPORARIA", "DEFINITIVA"],\n  });\n  const [medicamentoCicloVida, setMedicamentoCicloVida] = useState(null);\n  const [acaoCicloVidaMedicamento, setAcaoCicloVidaMedicamento] = useState(null);\n  const [salvandoCicloVidaMedicamento, setSalvandoCicloVidaMedicamento] = useState(false);\n  const [medicamentoSubstituto, setMedicamentoSubstituto] = useState({\n    catalogo_medicamento_id: "",\n    nome_medicamento: "",\n    dose: "",\n    via: "",\n    frequencia: "",\n    frequencia_uso: "",\n    horarios_uso: "",\n    uso_se_necessario: false,\n    indicacao: "",\n    uso_continuo: true,\n    adesao_referida: "",\n    observacoes: "",\n  });\n  const [formCicloVidaMedicamento, setFormCicloVidaMedicamento] = useState({\n    data_evento: "",\n    motivo: "",\n    tipo_suspensao: "DEFINITIVA",\n    prm_relacionado_id: "",\n    intervencao_relacionada_id: "",\n    observacao: "",\n  });\n'''
text = insert_after(text, marker, insert, 'estados ciclo de vida frontend')
# useEffect call
text = replace_once(text, '    carregarOpcoesPlanoCuidado();\n  }, []);', '    carregarOpcoesPlanoCuidado();\n    carregarOpcoesCicloVidaMedicamento();\n  }, []);', 'carregar opções ciclo de vida no useEffect')
# Add functions after carregarOpcoesFarmacoterapia or before carregarCatalogo maybe find function end
marker = '''  async function carregarOpcoesFarmacoterapia() {\n    try {\n      const response = await api.get("/consultorio/farmacoterapia/opcoes");\n      setOpcoesFarmacoterapia(response.data || { vias_administracao: [], horarios_padrao: [], frequencias_uso: [] });\n    } catch (error) {\n      console.warn("Opções de farmacoterapia indisponíveis.", error.response?.data || error);\n    }\n  }\n'''
insert = r'''

  async function carregarOpcoesCicloVidaMedicamento() {
    try {
      const response = await api.get("/consultorio/farmacoterapia/opcoes");
      setOpcoesCicloVidaMedicamento((atual) => ({ ...atual, ...(response.data || {}) }));
    } catch (error) {
      console.warn("Opções do ciclo de vida da farmacoterapia indisponíveis.", error.response?.data || error);
    }
  }

  function abrirAcaoMedicamento(medicamento, acao) {
    setMedicamentoCicloVida(medicamento);
    setAcaoCicloVidaMedicamento(acao);
    setFormCicloVidaMedicamento({
      data_evento: new Date().toISOString().slice(0, 10),
      motivo: "",
      tipo_suspensao: "DEFINITIVA",
      prm_relacionado_id: "",
      intervencao_relacionada_id: "",
      observacao: "",
    });
    setMedicamentoSubstituto({
      catalogo_medicamento_id: "",
      nome_medicamento: "",
      dose: "",
      via: medicamento?.via || "",
      frequencia: "",
      frequencia_uso: "",
      horarios_uso: "",
      uso_se_necessario: false,
      indicacao: medicamento?.indicacao || "",
      uso_continuo: true,
      adesao_referida: "",
      observacoes: "",
    });
  }

  function fecharAcaoMedicamento() {
    setMedicamentoCicloVida(null);
    setAcaoCicloVidaMedicamento(null);
  }

  async function salvarCicloVidaMedicamento() {
    if (!medicamentoCicloVida?.id || !acaoCicloVidaMedicamento) return;
    if (!formCicloVidaMedicamento.motivo) {
      alert("Informe o motivo da alteração da farmacoterapia.");
      return;
    }

    try {
      setSalvandoCicloVidaMedicamento(true);
      const prmId = formCicloVidaMedicamento.prm_relacionado_id ? Number(formCicloVidaMedicamento.prm_relacionado_id) : null;
      const intervencaoId = formCicloVidaMedicamento.intervencao_relacionada_id ? Number(formCicloVidaMedicamento.intervencao_relacionada_id) : null;

      if (acaoCicloVidaMedicamento === "TROCAR") {
        if (!medicamentoSubstituto.catalogo_medicamento_id && !medicamentoSubstituto.nome_medicamento.trim()) {
          alert("Informe o medicamento substituto.");
          return;
        }
        await api.post(`/consultorio/medicamentos/${medicamentoCicloVida.id}/trocar`, {
          novo_medicamento: {
            ...medicamentoSubstituto,
            catalogo_medicamento_id: medicamentoSubstituto.catalogo_medicamento_id ? Number(medicamentoSubstituto.catalogo_medicamento_id) : null,
          },
          data_troca: formCicloVidaMedicamento.data_evento || null,
          motivo_troca: formCicloVidaMedicamento.motivo,
          prm_relacionado_id: prmId,
          intervencao_relacionada_id: intervencaoId,
          observacao: formCicloVidaMedicamento.observacao,
        });
      } else if (acaoCicloVidaMedicamento === "SUSPENDER") {
        await api.post(`/consultorio/medicamentos/${medicamentoCicloVida.id}/suspender`, {
          data_suspensao: formCicloVidaMedicamento.data_evento || null,
          motivo_suspensao: formCicloVidaMedicamento.motivo,
          tipo_suspensao: formCicloVidaMedicamento.tipo_suspensao,
          prm_relacionado_id: prmId,
          intervencao_relacionada_id: intervencaoId,
          observacao: formCicloVidaMedicamento.observacao,
        });
      } else if (acaoCicloVidaMedicamento === "ENCERRAR") {
        await api.post(`/consultorio/medicamentos/${medicamentoCicloVida.id}/encerrar`, {
          data_encerramento: formCicloVidaMedicamento.data_evento || null,
          motivo_encerramento: formCicloVidaMedicamento.motivo,
          prm_relacionado_id: prmId,
          intervencao_relacionada_id: intervencaoId,
          observacao: formCicloVidaMedicamento.observacao,
        });
      }

      fecharAcaoMedicamento();
      await atualizarProntuario(pacienteSelecionado.id);
      alert("Evolução da farmacoterapia registrada com sucesso.");
    } catch (error) {
      console.error("Erro ao registrar ciclo de vida do medicamento:", error.response?.data || error);
      alert("Erro ao registrar evolução da farmacoterapia.");
    } finally {
      setSalvandoCicloVidaMedicamento(false);
    }
  }
'''
text = insert_after(text, marker, insert, 'funções ciclo de vida frontend')
# Add status and buttons in med card after observacoes line
marker = '                      {m.observacoes && <p className="muted">Observações: {m.observacoes}</p>}\n                    </div>\n'
insert = '''                      <p className="muted">\n                        Situação: <strong>{m.status_farmacoterapia || (m.ativo ? "EM_USO" : "INATIVO")}</strong>\n                        {m.motivo_status ? ` · Motivo: ${m.motivo_status}` : ""}\n                      </p>\n                      {podeRegistrarClinico() && (m.status_farmacoterapia || "EM_USO") === "EM_USO" && (\n                        <div className="inline-actions">\n                          <button className="secondary-button" type="button" onClick={() => abrirAcaoMedicamento(m, "TROCAR")}>Trocar</button>\n                          <button className="secondary-button" type="button" onClick={() => abrirAcaoMedicamento(m, "SUSPENDER")}>Suspender</button>\n                          <button className="secondary-button" type="button" onClick={() => abrirAcaoMedicamento(m, "ENCERRAR")}>Encerrar</button>\n                        </div>\n                      )}\n                    </div>\n'''
text = replace_once(text, marker, insert, 'botões ciclo de vida no card medicamento')
# Add modal after med list before mostrarFormularioMedicamento
marker = '\n              {mostrarFormularioMedicamento && (\n'
insert = r'''

              {medicamentoCicloVida && acaoCicloVidaMedicamento && (
                <div className="nested-form">
                  <div className="section-header-row">
                    <div>
                      <h4>
                        {acaoCicloVidaMedicamento === "TROCAR" ? "Trocar medicamento" : acaoCicloVidaMedicamento === "SUSPENDER" ? "Suspender medicamento" : "Encerrar medicamento"}
                      </h4>
                      <p className="muted">{medicamentoCicloVida.nome_medicamento}</p>
                    </div>
                    <button className="secondary-button" type="button" onClick={fecharAcaoMedicamento}>Cancelar</button>
                  </div>

                  {acaoCicloVidaMedicamento === "TROCAR" && (
                    <>
                      <div className="form-grid">
                        <input className="input" placeholder="Medicamento substituto" value={medicamentoSubstituto.nome_medicamento} onChange={(e) => setMedicamentoSubstituto({ ...medicamentoSubstituto, nome_medicamento: e.target.value })} />
                        <input className="input" placeholder="Dose" value={medicamentoSubstituto.dose} onChange={(e) => setMedicamentoSubstituto({ ...medicamentoSubstituto, dose: e.target.value })} />
                        <select className="input" value={medicamentoSubstituto.via} onChange={(e) => setMedicamentoSubstituto({ ...medicamentoSubstituto, via: e.target.value })}>
                          <option value="">Via</option>
                          {(opcoesFarmacoterapia.vias_administracao || []).map((via) => <option key={via} value={via}>{via}</option>)}
                        </select>
                        <select className="input" value={medicamentoSubstituto.frequencia_uso} onChange={(e) => setMedicamentoSubstituto({ ...medicamentoSubstituto, frequencia_uso: e.target.value, frequencia: e.target.value })}>
                          <option value="">Frequência</option>
                          {(opcoesFarmacoterapia.frequencias_uso || []).map((freq) => <option key={freq} value={freq}>{freq}</option>)}
                        </select>
                      </div>
                      <input className="input" placeholder="Horários de uso" value={medicamentoSubstituto.horarios_uso} onChange={(e) => setMedicamentoSubstituto({ ...medicamentoSubstituto, horarios_uso: e.target.value })} />
                    </>
                  )}

                  <div className="form-grid">
                    <input className="input" type="date" value={formCicloVidaMedicamento.data_evento} onChange={(e) => setFormCicloVidaMedicamento({ ...formCicloVidaMedicamento, data_evento: e.target.value })} />
                    <select className="input" value={formCicloVidaMedicamento.motivo} onChange={(e) => setFormCicloVidaMedicamento({ ...formCicloVidaMedicamento, motivo: e.target.value })}>
                      <option value="">Motivo</option>
                      {((acaoCicloVidaMedicamento === "TROCAR" ? opcoesCicloVidaMedicamento.motivos_troca : acaoCicloVidaMedicamento === "SUSPENDER" ? opcoesCicloVidaMedicamento.motivos_suspensao : opcoesCicloVidaMedicamento.motivos_encerramento) || []).map((motivo) => (
                        <option key={motivo} value={motivo}>{motivo}</option>
                      ))}
                    </select>
                    {acaoCicloVidaMedicamento === "SUSPENDER" && (
                      <select className="input" value={formCicloVidaMedicamento.tipo_suspensao} onChange={(e) => setFormCicloVidaMedicamento({ ...formCicloVidaMedicamento, tipo_suspensao: e.target.value })}>
                        {(opcoesCicloVidaMedicamento.tipos_suspensao || []).map((tipo) => <option key={tipo} value={tipo}>{tipo}</option>)}
                      </select>
                    )}
                  </div>

                  <div className="form-grid">
                    <select className="input" value={formCicloVidaMedicamento.prm_relacionado_id} onChange={(e) => setFormCicloVidaMedicamento({ ...formCicloVidaMedicamento, prm_relacionado_id: e.target.value })}>
                      <option value="">Associar PRM (opcional)</option>
                      {problemasFarmacoterapeuticos.map((p) => <option key={p.id} value={p.id}>{p.categoria || "PRM"} · {p.subcategoria || p.tipo || p.descricao}</option>)}
                    </select>
                    <select className="input" value={formCicloVidaMedicamento.intervencao_relacionada_id} onChange={(e) => setFormCicloVidaMedicamento({ ...formCicloVidaMedicamento, intervencao_relacionada_id: e.target.value })}>
                      <option value="">Associar intervenção (opcional)</option>
                      {intervencoesFarmacoterapia.map((i) => <option key={i.id} value={i.id}>{i.tipo_intervencao || i.tipo_padronizado || "Intervenção"}</option>)}
                    </select>
                  </div>

                  <textarea className="textarea" placeholder="Observação clínica" value={formCicloVidaMedicamento.observacao} onChange={(e) => setFormCicloVidaMedicamento({ ...formCicloVidaMedicamento, observacao: e.target.value })} />

                  <button className="primary-button" type="button" onClick={salvarCicloVidaMedicamento} disabled={salvandoCicloVidaMedicamento}>
                    {salvandoCicloVidaMedicamento ? "Salvando..." : "Registrar alteração da farmacoterapia"}
                  </button>
                </div>
              )}
'''
text = insert_after(text, marker, insert, 'formulário ciclo de vida medicamento')
write(front, text)

print('\nPasso 14E.2C.5B.1 aplicado. Rode: pytest -q tests && python tests\\smoke_tests.py; depois cd frontend && npm run dev')
