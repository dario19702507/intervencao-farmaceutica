import { useEffect, useMemo, useState } from "react";
import { api } from "../../api/api";
import "./DocumentosPaciente.css";

const estadoInicialUpload = {
  paciente_id: "",
  tipo_documento: "LAUDO",
  operacao_vigencia: "RENOVACAO",
  titulo: "",
  descricao: "",
  data_emissao: "",
  data_validade: "",
  arquivo: null,
};

const estadoInicialEdicaoVigencia = {
  documento_id: null,
  titulo: "",
  vigencia_inicio: "",
  vigencia_fim: "",
  motivo: "",
  observacao: "",
};

function normalizarPacientes(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.pacientes)) return payload.pacientes;
  if (Array.isArray(payload?.items)) return payload.items;
  return [];
}

function normalizarDocumentos(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.documentos)) return payload.documentos;
  if (Array.isArray(payload?.items)) return payload.items;
  return [];
}

function normalizarHistorico(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.historico)) return payload.historico;
  return [];
}

function formatarData(data) {
  if (!data) return "-";
  const d = new Date(`${data}T00:00:00`);
  if (Number.isNaN(d.getTime())) return data;
  return d.toLocaleDateString("pt-BR");
}

function formatarDataHora(valor) {
  if (!valor) return "-";
  const d = new Date(valor);
  if (Number.isNaN(d.getTime())) return valor;
  return d.toLocaleString("pt-BR");
}

function documentoTipo(doc) {
  return doc.tipo_documento || doc.tipo || "-";
}

function documentoTitulo(doc) {
  return doc.titulo || doc.nome_arquivo_original || doc.filename || `Documento ${doc.id}`;
}

function statusValidadeClasse(doc) {
  const status = (doc.status_validade || doc.status || "").toString().toUpperCase();
  if (status.includes("VENC")) return "danger";
  if (status.includes("PROX") || status.includes("A_VENCER")) return "warning";
  return "ok";
}

function statusVigenciaClasse(doc) {
  const status = (doc.vigencia_status || "").toString().toUpperCase();
  if (status.includes("VENC") || status.includes("ENCERR")) return "danger";
  if (status.includes("AGUARD") || status.includes("FUTUR")) return "warning";
  if (status.includes("ATIVA")) return "ok";
  if (status.includes("SUBSTIT")) return "neutral";
  return "neutral";
}

function preencherDataInput(valor) {
  if (!valor) return "";
  return String(valor).slice(0, 10);
}

export default function DocumentosPaciente() {
  const [pacientes, setPacientes] = useState([]);
  const [pacienteSelecionado, setPacienteSelecionado] = useState("");
  const [buscaPaciente, setBuscaPaciente] = useState("");
  const [buscandoPacientes, setBuscandoPacientes] = useState(false);
  const [documentos, setDocumentos] = useState([]);
  const [dashboard, setDashboard] = useState(null);
  const [vencimentos, setVencimentos] = useState([]);
  const [opcoes, setOpcoes] = useState({
    tipos_documento: ["RECEITA", "LAUDO", "EXAME", "DOCUMENTO_PESSOAL", "TERMO", "OUTRO"],
    operacoes_vigencia: ["INCLUSAO", "RENOVACAO", "ADEQUACAO"],
    status_vigencia: ["AGUARDANDO_INICIO", "ATIVA", "ENCERRADA", "SUBSTITUIDA", "VENCIDA"],
  });
  const [form, setForm] = useState(estadoInicialUpload);
  const [loading, setLoading] = useState(false);
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState("");
  const [sucesso, setSucesso] = useState("");
  const [filtroVencimento, setFiltroVencimento] = useState("todos");
  const [edicaoVigencia, setEdicaoVigencia] = useState(estadoInicialEdicaoVigencia);
  const [historicoVigencia, setHistoricoVigencia] = useState([]);
  const [documentoHistorico, setDocumentoHistorico] = useState(null);
  const [carregandoHistorico, setCarregandoHistorico] = useState(false);

  const pacienteAtual = useMemo(
    () => pacientes.find((p) => String(p.id) === String(pacienteSelecionado)),
    [pacientes, pacienteSelecionado]
  );

  async function carregarBase() {
    setLoading(true);
    setErro("");
    try {
  const [opcoesResp, dashboardResp, vencimentosResp] = await Promise.all([
    api.get("/consultorio/documentos/opcoes"),
    api.get("/consultorio/documentos/validade-dashboard"),
    api.get("/consultorio/documentos/vencimentos"),
  ]);

  setOpcoes(opcoesResp.data || opcoes);
  setPacientes([]);
  setDashboard(dashboardResp.data || null);
  setVencimentos(normalizarDocumentos(vencimentosResp.data));
    } catch (e) {
      console.error(e);
      setErro("Não foi possível carregar a gestão documental. Verifique se o backend está ativo.");
    } finally {
      setLoading(false);
    }
  }

    async function buscarPacientesClinicos(termo) {
      const busca = (termo || "").trim();

      setBuscaPaciente(termo);

      if (busca.length < 3) {
        setPacientes([]);
        return;
      }

      try {
        setBuscandoPacientes(true);

      const response = await api.get("/consultorio/pacientes-clinicos/buscar", {
        params: {
          termo: busca,
          limit: 30,
        },
      });

      setPacientes(normalizarPacientes(response.data));
    } catch (error) {
      console.warn("Erro ao buscar pacientes clínicos.", error.response?.data || error);
      setPacientes([]);
    } finally {
      setBuscandoPacientes(false);
    }
  }

  async function carregarDocumentosDoPaciente(id = pacienteSelecionado) {
    if (!id) {
      setDocumentos([]);
      return;
    }
    try {
      const resp = await api.get(`/consultorio/paciente-clinico/${id}/documentos`);
      setDocumentos(normalizarDocumentos(resp.data));
    } catch (e) {
      console.error(e);
      setErro("Não foi possível carregar os documentos do paciente selecionado.");
    }
  }

  useEffect(() => {
    carregarBase();
  }, []);

  useEffect(() => {
    carregarDocumentosDoPaciente(pacienteSelecionado);
    setForm((atual) => ({ ...atual, paciente_id: pacienteSelecionado }));
  }, [pacienteSelecionado]);

  function alterarForm(campo, valor) {
    setForm((atual) => ({ ...atual, [campo]: valor }));
  }

  function selecionarPaciente(id) {
    setPacienteSelecionado(id);
    setForm((atual) => ({ ...atual, paciente_id: id }));
  }

  async function enviarDocumento(e) {
    e.preventDefault();
    setErro("");
    setSucesso("");

    if (!form.paciente_id) {
      setErro("Selecione um paciente clínico.");
      return;
    }
    if (!form.arquivo) {
      setErro("Selecione um arquivo para upload.");
      return;
    }

    const dados = new FormData();
    dados.append("arquivo", form.arquivo);
    dados.append("tipo_documento", form.tipo_documento);
    dados.append("titulo", form.titulo || form.arquivo.name);
    dados.append("descricao", form.descricao || "");
    if (form.data_emissao) dados.append("data_emissao", form.data_emissao);
    if (form.data_validade) dados.append("data_validade", form.data_validade);
    if (["LAUDO", "RECEITA"].includes(form.tipo_documento) && form.operacao_vigencia) {
      dados.append("operacao_vigencia", form.operacao_vigencia);
    }

    setSalvando(true);
    try {
      await api.post(`/consultorio/paciente-clinico/${form.paciente_id}/documentos`, dados, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setSucesso("Documento enviado com sucesso. A vigência e o fluxo operacional foram calculados quando aplicável.");
      setForm({ ...estadoInicialUpload, paciente_id: form.paciente_id, tipo_documento: form.tipo_documento, operacao_vigencia: form.operacao_vigencia });
      await Promise.all([carregarDocumentosDoPaciente(form.paciente_id), carregarBase()]);
    } catch (e) {
      console.error(e);
      setErro(e.response?.data?.detail || "Não foi possível enviar o documento.");
    } finally {
      setSalvando(false);
    }
  }

  async function inativarDocumento(id) {
    if (!window.confirm("Deseja inativar este documento?")) return;
    try {
      await api.delete(`/consultorio/documentos/${id}`);
      await Promise.all([carregarDocumentosDoPaciente(), carregarBase()]);
      setSucesso("Documento inativado.");
    } catch (e) {
      console.error(e);
      setErro("Não foi possível inativar o documento.");
    }
  }

  function baixarDocumento(id) {
    const baseURL = api.defaults.baseURL || "http://127.0.0.1:8000";
    window.open(`${baseURL}/consultorio/documentos/${id}/download`, "_blank", "noopener,noreferrer");
  }

  async function gerarNotificacoes() {
    setErro("");
    setSucesso("");
    try {
      await api.post("/consultorio/documentos/gerar-notificacoes-validade");
      setSucesso("Notificações documentais geradas/atualizadas.");
      await carregarBase();
    } catch (e) {
      console.error(e);
      setErro(e.response?.data?.detail || "Não foi possível gerar notificações documentais.");
    }
  }

  function abrirEdicaoVigencia(doc) {
    setErro("");
    setSucesso("");
    setEdicaoVigencia({
      documento_id: doc.id,
      titulo: documentoTitulo(doc),
      vigencia_inicio: preencherDataInput(doc.vigencia_inicio),
      vigencia_fim: preencherDataInput(doc.vigencia_fim || doc.data_validade),
      motivo: "",
      observacao: "",
    });
  }

  function fecharEdicaoVigencia() {
    setEdicaoVigencia(estadoInicialEdicaoVigencia);
  }

  async function salvarVigencia(e) {
    e.preventDefault();
    setErro("");
    setSucesso("");
    if (!edicaoVigencia.documento_id) return;
    if (!edicaoVigencia.vigencia_inicio || !edicaoVigencia.vigencia_fim) {
      setErro("Informe início e fim da vigência.");
      return;
    }
    if (!edicaoVigencia.motivo || edicaoVigencia.motivo.trim().length < 5) {
      setErro("Informe o motivo da alteração da vigência com pelo menos 5 caracteres.");
      return;
    }
    try {
      await api.put(`/consultorio/documentos/${edicaoVigencia.documento_id}/vigencia`, {
        vigencia_inicio: edicaoVigencia.vigencia_inicio,
        vigencia_fim: edicaoVigencia.vigencia_fim,
        motivo: edicaoVigencia.motivo,
        observacao: edicaoVigencia.observacao || null,
      });
      setSucesso("Vigência atualizada. Agenda, notificações e fila WhatsApp foram recalculadas.");
      fecharEdicaoVigencia();
      await Promise.all([carregarDocumentosDoPaciente(), carregarBase()]);
    } catch (e) {
      console.error(e);
      setErro(e.response?.data?.detail || "Não foi possível atualizar a vigência.");
    }
  }

  async function carregarHistorico(doc) {
    setErro("");
    setCarregandoHistorico(true);
    setDocumentoHistorico(doc);
    setHistoricoVigencia([]);
    try {
      const resp = await api.get(`/consultorio/documentos/${doc.id}/vigencia-historico`);
      setHistoricoVigencia(normalizarHistorico(resp.data));
    } catch (e) {
      console.error(e);
      setErro("Não foi possível carregar o histórico de vigência.");
    } finally {
      setCarregandoHistorico(false);
    }
  }

  function fecharHistorico() {
    setDocumentoHistorico(null);
    setHistoricoVigencia([]);
  }

  async function reprocessarFluxo(doc) {
    if (!window.confirm("Reprocessar Agenda, Notificações e WhatsApp para este documento?")) return;
    setErro("");
    setSucesso("");
    try {
      await api.post(`/consultorio/documentos/${doc.id}/reprocessar-fluxo`);
      setSucesso("Fluxo operacional reprocessado para o documento.");
      await Promise.all([carregarDocumentosDoPaciente(), carregarBase()]);
    } catch (e) {
      console.error(e);
      setErro(e.response?.data?.detail || "Não foi possível reprocessar o fluxo do documento.");
    }
  }

  const vencimentosFiltrados = vencimentos.filter((doc) => {
    if (filtroVencimento === "todos") return true;
    const status = (doc.status_validade || doc.status || "").toString().toUpperCase();
    if (filtroVencimento === "vencidos") return status.includes("VENC");
    if (filtroVencimento === "a_vencer") return status.includes("PROX") || status.includes("A_VENCER");
    return true;
  });

  return (
    <div className="documentos-page">
      <div className="documentos-header">
        <div>
          <p className="eyebrow">Gestão documental</p>
          <h1>Documentos, vigências e fluxo operacional</h1>
          <p>Upload, validade, vigência editável, histórico e integração com Agenda, Notificações e WhatsApp.</p>
        </div>
        <button className="primary" onClick={gerarNotificacoes}>Gerar notificações de validade</button>
      </div>

      <section className="regra-box">
        <strong>Regras automáticas ativas</strong>
        <span>Inclusão: +30 dias; início após dia 23 vai para 01 do mês seguinte.</span>
        <span>Renovação vencida até 3 meses: +8 dias; após dia 23 vai para 01 do mês seguinte.</span>
        <span>Laudo não renovado: urgente no primeiro dia de atendimento após o vencimento.</span>
      </section>

      {erro && <div className="alert danger">{erro}</div>}
      {sucesso && <div className="alert success">{sucesso}</div>}
      {loading && <div className="alert info">Carregando informações documentais...</div>}

      <section className="cards-grid">
        <div className="metric-card"><span>Total</span><strong>{dashboard?.total_documentos_ativos ?? dashboard?.total_documentos ?? dashboard?.total ?? 0}</strong></div>
        <div className="metric-card warning"><span>A vencer</span><strong>{dashboard?.vence_em_30_dias ?? dashboard?.a_vencer ?? dashboard?.documentos_a_vencer ?? 0}</strong></div>
        <div className="metric-card danger"><span>Vencidos urgentes</span><strong>{dashboard?.vencidos_urgentes ?? 0}</strong></div>
        <div className="metric-card"><span>Laudos/Receitas</span><strong>{(dashboard?.laudos_ativos ?? 0) + (dashboard?.receitas_ativas ?? 0) || dashboard?.laudos_receitas || dashboard?.documentos_monitorados || 0}</strong></div>
      </section>

      <section className="documentos-panel">
        <div className="panel-title">
          <h2>Novo documento</h2>
          <span>Vinculado ao paciente clínico, com cálculo automático de vigência quando aplicável</span>
        </div>

        <form className="upload-form" onSubmit={enviarDocumento}>
          <label>
            Paciente
            <select value={form.paciente_id} onChange={(e) => selecionarPaciente(e.target.value)}>
              <option value="">Selecione</option>
              {pacientes.map((p) => <option key={p.id} value={p.id}>{p.nome || p.nome_completo || `Paciente ${p.id}`}</option>)}
            </select>
          </label>

          <label>
            Tipo
            <select value={form.tipo_documento} onChange={(e) => alterarForm("tipo_documento", e.target.value)}>
              {(opcoes.tipos_documento || opcoes.tipos || []).map((tipo) => <option key={tipo} value={tipo}>{tipo}</option>)}
            </select>
          </label>

          <label>
            Operação de vigência
            <select value={form.operacao_vigencia} onChange={(e) => alterarForm("operacao_vigencia", e.target.value)} disabled={!['LAUDO', 'RECEITA'].includes(form.tipo_documento)}>
              {(opcoes.operacoes_vigencia || ["INCLUSAO", "RENOVACAO", "ADEQUACAO"]).map((op) => <option key={op} value={op}>{op}</option>)}
            </select>
          </label>

          <label>
            Título
            <input value={form.titulo} onChange={(e) => alterarForm("titulo", e.target.value)} placeholder="Ex.: Laudo de asma grave" />
          </label>

          <label>
            Data de emissão
            <input type="date" value={form.data_emissao} onChange={(e) => alterarForm("data_emissao", e.target.value)} />
          </label>

          <label>
            Data de validade
            <input type="date" value={form.data_validade} onChange={(e) => alterarForm("data_validade", e.target.value)} />
          </label>

          <label className="wide">
            Descrição/observações
            <textarea value={form.descricao} onChange={(e) => alterarForm("descricao", e.target.value)} placeholder="Observações sobre o documento" />
          </label>

          <label className="wide file-input">
            Arquivo
            <input type="file" onChange={(e) => alterarForm("arquivo", e.target.files?.[0] || null)} />
          </label>

          <button className="primary" disabled={salvando}>{salvando ? "Enviando..." : "Enviar documento"}</button>
        </form>
      </section>

      <section className="documentos-panel">
        <div className="panel-title">
          <div>
            <h2>Documentos do paciente</h2>
            <span>{pacienteAtual ? (pacienteAtual.nome || pacienteAtual.nome_completo) : "Selecione um paciente para visualizar"}</span>
          </div>
            <input
              className="input"
              placeholder="Buscar paciente por nome, CPF ou CNS"
              value={buscaPaciente}
              onChange={(e) => buscarPacientesClinicos(e.target.value)}
            />
            {buscandoPacientes && <p className="muted">Buscando pacientes...</p>}
          <select value={pacienteSelecionado} onChange={(e) => selecionarPaciente(e.target.value)}>
            <option value="">Selecionar paciente</option>
            {pacientes.map((p) => <option key={p.id} value={p.id}>{p.nome || p.nome_completo || `Paciente ${p.id}`}</option>)}
          </select>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Tipo</th>
                <th>Título</th>
                <th>Validade</th>
                <th>Vigência</th>
                <th>Status</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {documentos.length === 0 && <tr><td colSpan="6" className="empty">Nenhum documento encontrado.</td></tr>}
              {documentos.map((doc) => (
                <tr key={doc.id}>
                  <td>{documentoTipo(doc)}</td>
                  <td>
                    <strong>{documentoTitulo(doc)}</strong>
                    <small className="subinfo">{doc.operacao_vigencia ? `Operação: ${doc.operacao_vigencia}` : "Sem operação de vigência"}</small>
                  </td>
                  <td>{formatarData(doc.data_validade)}</td>
                  <td>
                    <div className="vigencia-cell">
                      <span>{formatarData(doc.vigencia_inicio)} → {formatarData(doc.vigencia_fim)}</span>
                      <span className={`pill ${statusVigenciaClasse(doc)}`}>{doc.vigencia_status || "SEM_VIGENCIA"}</span>
                      {doc.vigencia_editada_manualmente && <small className="manual-flag">Editada manualmente</small>}
                    </div>
                  </td>
                  <td><span className={`pill ${statusValidadeClasse(doc)}`}>{doc.status_validade || doc.status || "ATIVO"}</span></td>
                  <td className="actions actions-stack">
                    <button onClick={() => baixarDocumento(doc.id)}>Baixar</button>
                    <button onClick={() => abrirEdicaoVigencia(doc)}>Editar vigência</button>
                    <button onClick={() => carregarHistorico(doc)}>Histórico</button>
                    <button onClick={() => reprocessarFluxo(doc)}>Reprocessar</button>
                    <button className="danger-outline" onClick={() => inativarDocumento(doc.id)}>Inativar</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="documentos-panel">
        <div className="panel-title">
          <div>
            <h2>Vencimentos documentais</h2>
            <span>Laudos, receitas e documentos monitorados</span>
          </div>
          <select value={filtroVencimento} onChange={(e) => setFiltroVencimento(e.target.value)}>
            <option value="todos">Todos</option>
            <option value="a_vencer">A vencer</option>
            <option value="vencidos">Vencidos</option>
          </select>
        </div>

        <div className="vencimentos-list">
          {vencimentosFiltrados.length === 0 && <div className="empty-card">Nenhum vencimento encontrado.</div>}
          {vencimentosFiltrados.map((doc) => (
            <div className="vencimento-card" key={doc.id}>
              <div>
                <strong>{documentoTitulo(doc)}</strong>
                <span>{doc.paciente_nome || doc.nome_paciente || `Paciente ${doc.paciente_id || "não informado"}`}</span>
              </div>
              <div><small>Tipo</small><b>{documentoTipo(doc)}</b></div>
              <div><small>Validade</small><b>{formatarData(doc.data_validade)}</b></div>
              <div><small>Vigência</small><b>{formatarData(doc.vigencia_inicio)} → {formatarData(doc.vigencia_fim)}</b></div>
              <span className={`pill ${statusValidadeClasse(doc)}`}>{doc.status_validade || doc.status || "MONITORADO"}</span>
            </div>
          ))}
        </div>
      </section>

      {edicaoVigencia.documento_id && (
        <div className="modal-backdrop">
          <form className="modal-card" onSubmit={salvarVigencia}>
            <div className="modal-header">
              <div>
                <h2>Editar vigência</h2>
                <span>{edicaoVigencia.titulo}</span>
              </div>
              <button type="button" onClick={fecharEdicaoVigencia}>×</button>
            </div>
            <label>
              Início da vigência
              <input type="date" value={edicaoVigencia.vigencia_inicio} onChange={(e) => setEdicaoVigencia((a) => ({ ...a, vigencia_inicio: e.target.value }))} required />
            </label>
            <label>
              Fim da vigência
              <input type="date" value={edicaoVigencia.vigencia_fim} onChange={(e) => setEdicaoVigencia((a) => ({ ...a, vigencia_fim: e.target.value }))} required />
            </label>
            <label>
              Motivo da alteração
              <input value={edicaoVigencia.motivo} onChange={(e) => setEdicaoVigencia((a) => ({ ...a, motivo: e.target.value }))} placeholder="Ex.: Correção administrativa" required />
            </label>
            <label>
              Observação
              <textarea value={edicaoVigencia.observacao} onChange={(e) => setEdicaoVigencia((a) => ({ ...a, observacao: e.target.value }))} placeholder="Detalhe adicional da alteração" />
            </label>
            <div className="modal-actions">
              <button type="button" onClick={fecharEdicaoVigencia}>Cancelar</button>
              <button className="primary" type="submit">Salvar vigência</button>
            </div>
          </form>
        </div>
      )}

      {documentoHistorico && (
        <div className="modal-backdrop">
          <div className="modal-card history-modal">
            <div className="modal-header">
              <div>
                <h2>Histórico de vigência</h2>
                <span>{documentoTitulo(documentoHistorico)}</span>
              </div>
              <button type="button" onClick={fecharHistorico}>×</button>
            </div>
            {carregandoHistorico && <div className="alert info">Carregando histórico...</div>}
            {!carregandoHistorico && historicoVigencia.length === 0 && <div className="empty-card">Nenhuma alteração de vigência registrada.</div>}
            <div className="history-list">
              {historicoVigencia.map((h) => (
                <div className="history-item" key={h.id}>
                  <div>
                    <strong>{h.origem || "ALTERAÇÃO"}</strong>
                    <span>{formatarDataHora(h.criado_em)} · {h.usuario || "Usuário não informado"}</span>
                  </div>
                  <p><b>Anterior:</b> {formatarData(h.vigencia_inicio_anterior)} → {formatarData(h.vigencia_fim_anterior)} ({h.vigencia_status_anterior || "-"})</p>
                  <p><b>Novo:</b> {formatarData(h.vigencia_inicio_nova)} → {formatarData(h.vigencia_fim_nova)} ({h.vigencia_status_nova || "-"})</p>
                  <p><b>Motivo:</b> {h.motivo || "-"}</p>
                  {h.observacao && <p><b>Observação:</b> {h.observacao}</p>}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
