import { useEffect, useMemo, useState } from "react";
import { api } from "../../api/api";
import BuscaPacienteClinico from "../../components/BuscaPacienteClinico";
import "./ProcessosDocumentais.css";

const processoInicial = {
  paciente_id: "",
  tipo_processo: "RENOVACAO",
  titulo: "",
  descricao: "",
  situacao: "EM_MONTAGEM",
  prioridade: "NORMAL",
  data_abertura: "",
  vigencia_inicio: "",
  vigencia_fim: "",
  pendencias_descricao: "",
};

function normalizarPacientes(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.pacientes)) return payload.pacientes;
  if (Array.isArray(payload?.items)) return payload.items;
  return [];
}

function normalizarProcessos(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.processos)) return payload.processos;
  if (Array.isArray(payload?.items)) return payload.items;
  return [];
}

function nomePaciente(paciente) {
  return paciente?.nome || paciente?.nome_completo || paciente?.paciente_nome || `Paciente #${paciente?.id}`;
}

function formatarData(data) {
  if (!data) return "-";
  const d = new Date(`${data}T00:00:00`);
  if (Number.isNaN(d.getTime())) return data;
  return d.toLocaleDateString("pt-BR");
}

function badgeClasse(valor) {
  const v = (valor || "").toString().toUpperCase();
  if (v.includes("URGENTE") || v.includes("VENC") || v.includes("INDEFERIDO")) return "danger";
  if (v.includes("IMPORTANTE") || v.includes("AGUARDANDO") || v.includes("MONTAGEM") || v.includes("INCOMPLETO") || v.includes("SEM_DOCUMENTOS")) return "warning";
  if (v.includes("DEFERIDO") || v.includes("PRONTO") || v.includes("COMPLETO")) return "success";
  return "neutral";
}

function arquivoParaItem(file, tipoPadrao = "LAUDO") {
  return {
    id_local: `${file.name}-${file.size}-${file.lastModified}`,
    file,
    tipo_documento: tipoPadrao,
    titulo: file.name,
    descricao: "",
    data_emissao: "",
    data_validade: "",
  };
}

export default function ProcessosDocumentais() {
  const [pacienteSelecionado, setPacienteSelecionado] = useState(null);
  const [opcoes, setOpcoes] = useState({
    tipos_processo: ["INCLUSAO", "RENOVACAO", "ADEQUACAO", "ENCERRAMENTO"],
    situacoes: ["EM_MONTAGEM", "AGUARDANDO_DOCUMENTOS", "PRONTO_PARA_ENVIO", "ENVIADO", "DEFERIDO", "INDEFERIDO", "ENCERRADO"],
    prioridades: ["NORMAL", "IMPORTANTE", "URGENTE"],
    documentos_recomendados: {},
  });
  const [opcoesDocumentos, setOpcoesDocumentos] = useState({ tipos_documento: ["LAUDO", "RECEITA", "EXAME", "DOCUMENTO_PESSOAL", "TERMO", "OUTRO"] });
  const [dashboard, setDashboard] = useState(null);
  const [completudeDashboard, setCompletudeDashboard] = useState(null);
  const [formProcesso, setFormProcesso] = useState(processoInicial);
  const [processos, setProcessos] = useState([]);
  const [processoSelecionadoId, setProcessoSelecionadoId] = useState("");
  const [processoDetalhe, setProcessoDetalhe] = useState(null);
  const [arquivos, setArquivos] = useState([]);
  const [pendencia, setPendencia] = useState({ titulo: "", mensagem: "", prioridade: "IMPORTANTE" });
  const [sugestoesPreenchimento, setSugestoesPreenchimento] = useState(null);
  const [camposSelecionados, setCamposSelecionados] = useState([]);
  const [loadingSugestoes, setLoadingSugestoes] = useState(false);
  const [loading, setLoading] = useState(false);
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState("");
  const [sucesso, setSucesso] = useState("");


  const processoSelecionado = processoDetalhe?.id ? processoDetalhe : processos.find((p) => String(p.id) === String(processoSelecionadoId));

  const recomendados = opcoes.documentos_recomendados?.[formProcesso.tipo_processo] || [];
  const recomendadosDetalhe = processoSelecionado?.documentos_recomendados || [];
  const pendentesDetalhe = processoSelecionado?.documentos_pendentes || [];

  async function carregarBase() {
    setLoading(true);
    setErro("");
    try {
      const [opcoesResp, docsOpcoesResp, dashboardResp, completudeResp] = await Promise.all([
        api.get("/consultorio/processos-documentais/opcoes"),
        api.get("/consultorio/documentos/opcoes"),
        api.get("/consultorio/processos-documentais/dashboard"),
        api.get("/consultorio/processos-documentais/completude-dashboard"),
      ]);
      setOpcoes(opcoesResp.data || opcoes);
      setOpcoesDocumentos(docsOpcoesResp.data || opcoesDocumentos);
      setDashboard(dashboardResp.data || null);
      setCompletudeDashboard(completudeResp.data || null);
    } catch (e) {
      console.error(e);
      setErro("Não foi possível carregar os processos documentais. Verifique se o backend está ativo.");
    } finally {
      setLoading(false);
    }
  }

  async function carregarProcessos(pacienteId = formProcesso.paciente_id) {
    if (!pacienteId) {
      setProcessos([]);
      setProcessoSelecionadoId("");
      setProcessoDetalhe(null);
      return;
    }
    try {
      const resp = await api.get(`/consultorio/paciente-clinico/${pacienteId}/processos-documentais`);
      const lista = normalizarProcessos(resp.data);
      setProcessos(lista);
      if (lista.length > 0 && !lista.some((p) => String(p.id) === String(processoSelecionadoId))) {
        setProcessoSelecionadoId(String(lista[0].id));
      }
      if (lista.length === 0) {
        setProcessoSelecionadoId("");
        setProcessoDetalhe(null);
      }
    } catch (e) {
      console.error(e);
      setErro("Não foi possível carregar os processos do paciente selecionado.");
    }
  }

  async function carregarDetalhe(processoId = processoSelecionadoId) {
    if (!processoId) {
      setProcessoDetalhe(null);
      return;
    }
    try {
      const resp = await api.get(`/consultorio/processos-documentais/${processoId}`);
      setProcessoDetalhe(resp.data?.processo || null);
    } catch (e) {
      console.error(e);
      setErro("Não foi possível carregar o processo documental selecionado.");
    }
  }

  useEffect(() => {
    carregarBase();
  }, []);

  useEffect(() => {
    carregarProcessos(formProcesso.paciente_id);
  }, [formProcesso.paciente_id]);

  useEffect(() => {
    carregarDetalhe(processoSelecionadoId);
    setSugestoesPreenchimento(null);
    setCamposSelecionados([]);
  }, [processoSelecionadoId]);

  function selecionarPaciente(paciente) {
    const id = paciente?.id ? String(paciente.id) : "";
    setPacienteSelecionado(paciente || null);
    setFormProcesso((atual) => ({ ...atual, paciente_id: id }));
    if (!id) {
      setProcessos([]);
      setProcessoSelecionadoId("");
      setProcessoDetalhe(null);
    }
  }

  function alterarProcesso(campo, valor) {
    setFormProcesso((atual) => ({ ...atual, [campo]: valor }));
  }

  function selecionarArquivos(e) {
    const selecionados = Array.from(e.target.files || []);
    if (selecionados.length === 0) return;
    setArquivos((atuais) => [...atuais, ...selecionados.map((file) => arquivoParaItem(file, recomendados[0] || "LAUDO"))]);
    e.target.value = "";
  }

  function alterarArquivo(idLocal, campo, valor) {
    setArquivos((atuais) => atuais.map((item) => (item.id_local === idLocal ? { ...item, [campo]: valor } : item)));
  }

  function removerArquivo(idLocal) {
    setArquivos((atuais) => atuais.filter((item) => item.id_local !== idLocal));
  }

  async function validarCompletude() {
    if (!processoSelecionado?.id) return;
    setErro("");
    setSucesso("");
    setSalvando(true);
    try {
      const resp = await api.post(`/consultorio/processos-documentais/${processoSelecionado.id}/validar-completude`);
      setSucesso(resp.data?.mensagem || "Completude documental validada.");
      await carregarDetalhe(processoSelecionado.id);
      await carregarProcessos(formProcesso.paciente_id);
      await carregarBase();
    } catch (e) {
      console.error(e);
      setErro(e.response?.data?.detail || "Não foi possível validar a completude documental.");
    } finally {
      setSalvando(false);
    }
  }

  async function criarProcesso(e) {
    e.preventDefault();
    setErro("");
    setSucesso("");
    if (!formProcesso.paciente_id) {
      setErro("Selecione um paciente clínico.");
      return;
    }
    setSalvando(true);
    try {
      const payload = {
        tipo_processo: formProcesso.tipo_processo,
        titulo: formProcesso.titulo || undefined,
        descricao: formProcesso.descricao || undefined,
        situacao: formProcesso.situacao || undefined,
        prioridade: formProcesso.prioridade || undefined,
        data_abertura: formProcesso.data_abertura || undefined,
        vigencia_inicio: formProcesso.vigencia_inicio || undefined,
        vigencia_fim: formProcesso.vigencia_fim || undefined,
        pendencias_descricao: formProcesso.pendencias_descricao || undefined,
      };
      const resp = await api.post(`/consultorio/paciente-clinico/${formProcesso.paciente_id}/processos-documentais`, payload);
      const novo = resp.data?.processo;
      setSucesso("Processo documental criado com sucesso.");
      await carregarProcessos(formProcesso.paciente_id);
      if (novo?.id) setProcessoSelecionadoId(String(novo.id));
      setFormProcesso((atual) => ({ ...processoInicial, paciente_id: atual.paciente_id, tipo_processo: atual.tipo_processo }));
    } catch (e) {
      console.error(e);
      setErro(e.response?.data?.detail || "Não foi possível criar o processo documental.");
    } finally {
      setSalvando(false);
    }
  }

  async function atualizarProcesso(campo, valor) {
    if (!processoSelecionado?.id) return;
    setErro("");
    setSucesso("");
    try {
      await api.put(`/consultorio/processos-documentais/${processoSelecionado.id}`, { [campo]: valor });
      setSucesso("Processo atualizado.");
      await carregarProcessos(formProcesso.paciente_id);
      await carregarDetalhe(processoSelecionado.id);
      await carregarBase();
    } catch (e) {
      console.error(e);
      setErro(e.response?.data?.detail || "Não foi possível atualizar o processo.");
    }
  }

  async function enviarArquivosMultiplos(e) {
    e.preventDefault();
    setErro("");
    setSucesso("");
    if (!processoSelecionado?.id) {
      setErro("Selecione ou crie um processo documental antes de enviar arquivos.");
      return;
    }
    if (arquivos.length === 0) {
      setErro("Selecione pelo menos um arquivo.");
      return;
    }
    setSalvando(true);
    let enviados = 0;
    const erros = [];
    try {
      for (const item of arquivos) {
        const formData = new FormData();
        formData.append("arquivo", item.file);
        formData.append("tipo_documento", item.tipo_documento);
        formData.append("titulo", item.titulo || item.file.name);
        if (item.descricao) formData.append("descricao", item.descricao);
        if (item.data_emissao) formData.append("data_emissao", item.data_emissao);
        if (item.data_validade) formData.append("data_validade", item.data_validade);
        formData.append("processo_documental_id", String(processoSelecionado.id));
        formData.append("operacao_vigencia", processoSelecionado.tipo_processo || formProcesso.tipo_processo);
        try {
          await api.post(`/consultorio/paciente-clinico/${processoSelecionado.paciente_id}/documentos`, formData, {
            headers: { "Content-Type": "multipart/form-data" },
          });
          enviados += 1;
        } catch (e) {
          console.error(e);
          erros.push(`${item.file.name}: ${e.response?.data?.detail || "falha no envio"}`);
        }
      }
      setArquivos([]);
      await carregarDetalhe(processoSelecionado.id);
      await carregarProcessos(formProcesso.paciente_id);
      await carregarBase();
      if (erros.length > 0) {
        setErro(`Arquivos enviados: ${enviados}. Falhas: ${erros.join(" | ")}`);
      } else {
        setSucesso(`${enviados} arquivo(s) vinculado(s) ao pacote documental.`);
      }
    } finally {
      setSalvando(false);
    }
  }

  async function notificarPendencia(e) {
    e.preventDefault();
    setErro("");
    setSucesso("");
    if (!processoSelecionado?.id) {
      setErro("Selecione um processo documental.");
      return;
    }
    if (!pendencia.mensagem.trim()) {
      setErro("Informe a mensagem da pendência documental.");
      return;
    }
    setSalvando(true);
    try {
      await api.post(`/consultorio/processos-documentais/${processoSelecionado.id}/notificar-pendencia`, {
        titulo: pendencia.titulo || undefined,
        mensagem: pendencia.mensagem,
        prioridade: pendencia.prioridade,
      });
      setPendencia({ titulo: "", mensagem: "", prioridade: "IMPORTANTE" });
      setSucesso("Pendência registrada como notificação interna. WhatsApp documental permanece manual.");
      await carregarDetalhe(processoSelecionado.id);
      await carregarProcessos(formProcesso.paciente_id);
    } catch (e) {
      console.error(e);
      setErro(e.response?.data?.detail || "Não foi possível registrar a pendência.");
    } finally {
      setSalvando(false);
    }
  }

  function baixarDocumento(documentoId) {
    const token = localStorage.getItem("token");
    const base = api.defaults.baseURL || "http://127.0.0.1:8000";
    const url = `${base}/consultorio/documentos/${documentoId}/download`;
    if (token) {
      window.open(`${url}?token=${encodeURIComponent(token)}`, "_blank", "noopener,noreferrer");
    } else {
      window.open(url, "_blank", "noopener,noreferrer");
    }
  }

  async function atualizarStatusDocumental(documento, status) {
    const motivo = window.prompt(`Informe o motivo para alterar o documento para ${status}:`);
    if (!motivo || motivo.trim().length < 5) {
      setErro("Motivo obrigatório com pelo menos 5 caracteres para alterar o status documental.");
      return;
    }
    setErro("");
    setSucesso("");
    setSalvando(true);
    try {
      await api.put(`/consultorio/documentos/${documento.id}/status-documental`, {
        status_documental: status,
        motivo: motivo.trim(),
      });
      setSucesso("Status documental atualizado. A completude considera apenas documentos VALIDADOS.");
      await carregarDetalhe(processoSelecionado.id);
      await carregarProcessos(formProcesso.paciente_id);
      await carregarBase();
    } catch (e) {
      console.error(e);
      setErro(e.response?.data?.detail || "Não foi possível alterar o status documental.");
    } finally {
      setSalvando(false);
    }
  }


  async function carregarSugestoesPreenchimento() {
    if (!processoSelecionado?.id) return;
    setErro("");
    setSucesso("");
    setLoadingSugestoes(true);
    try {
      const resp = await api.get(`/consultorio/processos-documentais/${processoSelecionado.id}/preenchimento-assistido`);
      setSugestoesPreenchimento(resp.data || null);
      const sugestoes = resp.data?.sugestoes || {};
      setCamposSelecionados(Object.keys(sugestoes).filter((campo) => campo !== "medicamento_catalogo"));
    } catch (e) {
      console.error(e);
      setErro(e.response?.data?.detail || "Não foi possível carregar as sugestões OCR do processo.");
    } finally {
      setLoadingSugestoes(false);
    }
  }

  function alternarCampoSugestao(campo) {
    setCamposSelecionados((atuais) => (
      atuais.includes(campo) ? atuais.filter((c) => c !== campo) : [...atuais, campo]
    ));
  }

  async function aplicarSugestoesSelecionadas() {
    if (!processoSelecionado?.id) return;
    if (camposSelecionados.length === 0) {
      setErro("Selecione pelo menos uma sugestão para aplicar ao processo.");
      return;
    }
    const observacao = window.prompt("Observação para registrar a aplicação assistida das sugestões:", "Conferido pelo operador");
    if (observacao === null) return;
    setErro("");
    setSucesso("");
    setSalvando(true);
    try {
      const resp = await api.post(`/consultorio/processos-documentais/${processoSelecionado.id}/preenchimento-assistido/aplicar`, {
        campos: camposSelecionados,
        observacao: observacao || "Conferido pelo operador",
      });
      setSucesso(resp.data?.mensagem || "Sugestões aplicadas ao processo documental.");
      await carregarDetalhe(processoSelecionado.id);
      await carregarProcessos(formProcesso.paciente_id);
    } catch (e) {
      console.error(e);
      setErro(e.response?.data?.detail || "Não foi possível aplicar as sugestões selecionadas.");
    } finally {
      setSalvando(false);
    }
  }

  return (
    <div className="processos-doc-page">
      <div className="processos-doc-header">
        <div>
          <p className="eyebrow">Gestão documental</p>
          <h1>Processos documentais</h1>
          <p>Monte pacotes documentais por ação operacional e vincule vários arquivos à mesma inclusão, renovação, adequação ou encerramento.</p>
        </div>
        <button className="btn-secondary" onClick={() => { carregarBase(); carregarProcessos(); carregarDetalhe(); }} disabled={loading}>
          Atualizar
        </button>
      </div>

      {erro && <div className="alert error">{erro}</div>}
      {sucesso && <div className="alert success">{sucesso}</div>}

      <section className="cards-grid">
        <div className="metric-card">
          <span>Total</span>
          <strong>{dashboard?.total ?? 0}</strong>
        </div>
        <div className="metric-card warning">
          <span>Aguardando documentos</span>
          <strong>{dashboard?.aguardando_documentos ?? 0}</strong>
        </div>
        <div className="metric-card">
          <span>Prontos para envio</span>
          <strong>{dashboard?.prontos_para_envio ?? 0}</strong>
        </div>
        <div className="metric-card danger">
          <span>Urgentes</span>
          <strong>{dashboard?.urgentes ?? 0}</strong>
        </div>
      </section>

      <section className="cards-grid completude-grid">
        <div className="metric-card success">
          <span>Pacotes completos</span>
          <strong>{completudeDashboard?.por_status?.COMPLETO ?? 0}</strong>
        </div>
        <div className="metric-card warning">
          <span>Pacotes incompletos</span>
          <strong>{completudeDashboard?.por_status?.INCOMPLETO ?? 0}</strong>
        </div>
        <div className="metric-card warning">
          <span>Sem documentos</span>
          <strong>{completudeDashboard?.por_status?.SEM_DOCUMENTOS ?? 0}</strong>
        </div>
        <div className="metric-card">
          <span>Total avaliados</span>
          <strong>{completudeDashboard?.total_processos ?? 0}</strong>
        </div>
      </section>

      <section className="processos-doc-layout">
        <div className="panel">
          <h2>Novo pacote documental</h2>
          <form onSubmit={criarProcesso} className="form-grid">
            <div className="span-2">
              <BuscaPacienteClinico
                label="Paciente clínico"
                value={formProcesso.paciente_id}
                selectedPaciente={pacienteSelecionado}
                onSelect={selecionarPaciente}
                required
              />
            </div>
            <label>
              Ação
              <select value={formProcesso.tipo_processo} onChange={(e) => alterarProcesso("tipo_processo", e.target.value)}>
                {(opcoes.tipos_processo || []).map((tipo) => <option key={tipo} value={tipo}>{tipo}</option>)}
              </select>
            </label>
            <label>
              Situação
              <select value={formProcesso.situacao} onChange={(e) => alterarProcesso("situacao", e.target.value)}>
                {(opcoes.situacoes || []).map((situacao) => <option key={situacao} value={situacao}>{situacao}</option>)}
              </select>
            </label>
            <label>
              Prioridade
              <select value={formProcesso.prioridade} onChange={(e) => alterarProcesso("prioridade", e.target.value)}>
                {(opcoes.prioridades || []).map((prioridade) => <option key={prioridade} value={prioridade}>{prioridade}</option>)}
              </select>
            </label>
            <label className="span-2">
              Título
              <input value={formProcesso.titulo} onChange={(e) => alterarProcesso("titulo", e.target.value)} placeholder="Ex.: Renovação 2026/2" />
            </label>
            <label>
              Início da vigência
              <input type="date" value={formProcesso.vigencia_inicio} onChange={(e) => alterarProcesso("vigencia_inicio", e.target.value)} />
            </label>
            <label>
              Fim da vigência
              <input type="date" value={formProcesso.vigencia_fim} onChange={(e) => alterarProcesso("vigencia_fim", e.target.value)} />
            </label>
            <label className="span-2">
              Descrição
              <textarea value={formProcesso.descricao} onChange={(e) => alterarProcesso("descricao", e.target.value)} placeholder="Observações sobre o pacote documental" />
            </label>
            <div className="recommended span-2">
              <strong>Documentos recomendados para {formProcesso.tipo_processo}:</strong>
              <div className="tag-list">
                {recomendados.map((doc) => <span key={doc}>{doc}</span>)}
              </div>
            </div>
            <button className="btn-primary span-2" disabled={salvando || !formProcesso.paciente_id}>Criar pacote</button>
          </form>
        </div>

        <div className="panel">
          <h2>Pacotes do paciente</h2>
          {pacienteSelecionado && <p className="muted">Paciente selecionado: <strong>{nomePaciente(pacienteSelecionado)}</strong></p>}
          <div className="process-list">
            {processos.length === 0 && <p className="empty">Nenhum processo documental encontrado para este paciente.</p>}
            {processos.map((processo) => (
              <button
                key={processo.id}
                className={`process-card ${String(processoSelecionadoId) === String(processo.id) ? "active" : ""}`}
                onClick={() => setProcessoSelecionadoId(String(processo.id))}
              >
                <div>
                  <strong>{processo.titulo || `${processo.tipo_processo} #${processo.id}`}</strong>
                  <span>{processo.tipo_processo} · {processo.total_documentos ?? 0} documento(s)</span>
                  <span>Completude: {processo.completude_status || processo.completude?.status || "EM_ANALISE"}</span>
                </div>
                <div className="process-badges">
                  <span className={`badge ${badgeClasse(processo.situacao)}`}>{processo.situacao}</span>
                  <span className={`badge ${badgeClasse(processo.completude_status || processo.completude?.status)}`}>{processo.completude_status || processo.completude?.status || "EM_ANALISE"}</span>
                </div>
              </button>
            ))}
          </div>
        </div>
      </section>

      {processoSelecionado && (
        <section className="panel detail-panel">
          <div className="detail-header">
            <div>
              <p className="eyebrow">Pacote selecionado</p>
              <h2>{processoSelecionado.titulo || `${processoSelecionado.tipo_processo} #${processoSelecionado.id}`}</h2>
              <p className="muted">Vigência: {formatarData(processoSelecionado.vigencia_inicio)} até {formatarData(processoSelecionado.vigencia_fim)}</p>
              <span className={`badge ${badgeClasse(processoSelecionado.completude_status || processoSelecionado.completude?.status)}`}>
                Completude: {processoSelecionado.completude_status || processoSelecionado.completude?.status || "EM_ANALISE"}
              </span>
            </div>
            <div className="status-controls">
              <select value={processoSelecionado.situacao || "EM_MONTAGEM"} onChange={(e) => atualizarProcesso("situacao", e.target.value)}>
                {(opcoes.situacoes || []).map((situacao) => <option key={situacao} value={situacao}>{situacao}</option>)}
              </select>
              <select value={processoSelecionado.prioridade || "NORMAL"} onChange={(e) => atualizarProcesso("prioridade", e.target.value)}>
                {(opcoes.prioridades || []).map((prioridade) => <option key={prioridade} value={prioridade}>{prioridade}</option>)}
              </select>
              <button type="button" className="btn-secondary" onClick={validarCompletude} disabled={salvando}>Validar completude</button>
            </div>
          </div>

          <div className="assist-panel">
            <div className="assist-header">
              <div>
                <h3>Pré-preenchimento assistido</h3>
                <p>Usa somente documentos VALIDADOS com OCR já extraído. Nenhum dado é aplicado sem confirmação do operador.</p>
              </div>
              <div className="assist-actions">
                <button type="button" className="btn-secondary" onClick={carregarSugestoesPreenchimento} disabled={loadingSugestoes || salvando}>
                  {loadingSugestoes ? "Carregando..." : "Gerar sugestões OCR"}
                </button>
                <button type="button" className="btn-primary" onClick={aplicarSugestoesSelecionadas} disabled={salvando || !sugestoesPreenchimento || camposSelecionados.length === 0}>
                  Aplicar selecionadas
                </button>
              </div>
            </div>

            {sugestoesPreenchimento && (
              <div className="assist-content">
                <div className="assist-summary">
                  <span className="badge neutral">Documentos validados com OCR: {sugestoesPreenchimento.total_documentos_validados_com_ocr ?? 0}</span>
                  <span className="badge warning">Atualização automática: não</span>
                </div>
                <div className="suggestions-grid">
                  {Object.keys(sugestoesPreenchimento.sugestoes || {}).length === 0 && (
                    <p className="empty">Nenhuma sugestão disponível. Verifique se há documentos VALIDADOS com OCR extraído.</p>
                  )}
                  {Object.entries(sugestoesPreenchimento.sugestoes || {}).map(([campo, dados]) => (
                    <label key={campo} className="suggestion-card">
                      <input
                        type="checkbox"
                        checked={camposSelecionados.includes(campo)}
                        onChange={() => alternarCampoSugestao(campo)}
                        disabled={campo === "medicamento_catalogo"}
                      />
                      <div>
                        <strong>{campo.replaceAll("_", " ")}</strong>
                        <span>{dados?.valor || "-"}</span>
                        <small>Confiança: {dados?.confianca ?? "-"} · Origem: {dados?.origem || "OCR"}</small>
                      </div>
                    </label>
                  ))}
                </div>
                {sugestoesPreenchimento.vigencia_sugerida && (
                  <p className="muted">Vigência sugerida: {sugestoesPreenchimento.vigencia_sugerida.inicio} até {sugestoesPreenchimento.vigencia_sugerida.fim}. Conferência humana obrigatória.</p>
                )}
              </div>
            )}
          </div>

          <div className="detail-grid">
            <div>
              <h3>Composição do pacote</h3>
              <div className="completude-summary">
                <span className={`badge ${badgeClasse(processoSelecionado.completude_status || processoSelecionado.completude?.status)}`}>
                  {processoSelecionado.completude_status || processoSelecionado.completude?.status || "EM_ANALISE"}
                </span>
                <span>{processoSelecionado.completude?.total_documentos ?? processoSelecionado.total_documentos ?? 0} documento(s) recebido(s)</span>
              </div>

              <h4>Documentos obrigatórios</h4>
              <div className="tag-list">
                {(processoSelecionado.completude?.documentos_obrigatorios || recomendadosDetalhe).map((doc) => {
                  const pendente = (processoSelecionado.completude?.documentos_pendentes || pendentesDetalhe).includes(doc);
                  return <span key={doc} className={pendente ? "pending" : "present"}>{doc}</span>;
                })}
              </div>

              <h4>Documentos presentes/classificados</h4>
              <div className="tag-list">
                {(processoSelecionado.completude?.documentos_presentes || processoSelecionado.documentos_presentes || []).length === 0 && <span className="pending">Nenhum documento classificado</span>}
                {(processoSelecionado.completude?.documentos_presentes || processoSelecionado.documentos_presentes || []).map((doc) => (
                  <span key={doc} className="present">{doc}</span>
                ))}
              </div>

              {(processoSelecionado.completude?.documentos_pendentes || pendentesDetalhe).length > 0 ? (
                <p className="warning-text">Pendentes: {(processoSelecionado.completude?.documentos_pendentes || pendentesDetalhe).join(", ")}</p>
              ) : (
                <p className="success-text">Pacote documental completo conforme documentos recomendados.</p>
              )}
              <p className="muted">Regra: pendência documental gera notificação interna. WhatsApp para documentos deve ser enviado manualmente pelo operador.</p>
            </div>

            <form onSubmit={notificarPendencia} className="pendency-box">
              <h3>Registrar pendência documental</h3>
              <input value={pendencia.titulo} onChange={(e) => setPendencia((a) => ({ ...a, titulo: e.target.value }))} placeholder="Título da pendência" />
              <select value={pendencia.prioridade} onChange={(e) => setPendencia((a) => ({ ...a, prioridade: e.target.value }))}>
                {(opcoes.prioridades || []).map((prioridade) => <option key={prioridade} value={prioridade}>{prioridade}</option>)}
              </select>
              <textarea value={pendencia.mensagem} onChange={(e) => setPendencia((a) => ({ ...a, mensagem: e.target.value }))} placeholder="Descreva a pendência de forma específica para avaliação interna" />
              <button className="btn-secondary" disabled={salvando}>Criar notificação interna</button>
            </form>
          </div>

          <form onSubmit={enviarArquivosMultiplos} className="upload-multiple">
            <div className="upload-header">
              <div>
                <h3>Upload múltiplo de documentos</h3>
                <p>Selecione vários arquivos e classifique cada um antes de enviar para o mesmo pacote documental.</p>
              </div>
              <label className="file-picker">
                Selecionar arquivos
                <input type="file" multiple onChange={selecionarArquivos} />
              </label>
            </div>

            {arquivos.length > 0 && (
              <div className="upload-table">
                {arquivos.map((item) => (
                  <div className="upload-row" key={item.id_local}>
                    <div className="file-name">
                      <strong>{item.file.name}</strong>
                      <span>{Math.ceil(item.file.size / 1024)} KB</span>
                    </div>
                    <select value={item.tipo_documento} onChange={(e) => alterarArquivo(item.id_local, "tipo_documento", e.target.value)}>
                      {(opcoesDocumentos.tipos_documento || []).map((tipo) => <option key={tipo} value={tipo}>{tipo}</option>)}
                    </select>
                    <input value={item.titulo} onChange={(e) => alterarArquivo(item.id_local, "titulo", e.target.value)} placeholder="Título" />
                    <input type="date" value={item.data_emissao} onChange={(e) => alterarArquivo(item.id_local, "data_emissao", e.target.value)} title="Data de emissão" />
                    <input type="date" value={item.data_validade} onChange={(e) => alterarArquivo(item.id_local, "data_validade", e.target.value)} title="Data de validade" />
                    <button type="button" className="btn-link danger" onClick={() => removerArquivo(item.id_local)}>Remover</button>
                  </div>
                ))}
              </div>
            )}

            <button className="btn-primary" disabled={salvando || arquivos.length === 0}>Enviar {arquivos.length || ""} arquivo(s)</button>
          </form>

          <div className="documents-section">
            <h3>Documentos vinculados</h3>
            <p className="muted">A completude do pacote considera somente documentos com status documental VALIDADO. Documentos RECEBIDOS, REJEITADOS ou SUBSTITUÍDOS não completam exigências.</p>
            <div className="documents-table">
              {(processoSelecionado.documentos || []).length === 0 && <p className="empty">Nenhum documento vinculado ainda.</p>}
              {(processoSelecionado.documentos || []).map((doc) => (
                <div className="doc-row" key={doc.id}>
                  <div>
                    <strong>{doc.titulo || doc.nome_arquivo_original}</strong>
                    <span>{doc.tipo_documento} · {doc.nome_arquivo_original}</span>
                  </div>
                  <div className="doc-status-stack">
                    <span className={`badge ${badgeClasse(doc.status_documental || "RECEBIDO")}`}>Documental: {doc.status_documental || "RECEBIDO"}</span>
                    <span className={`badge ${badgeClasse(doc.vigencia_status || doc.status)}`}>Vigência: {doc.vigencia_status || doc.status || "ATIVO"}</span>
                  </div>
                  <span>{formatarData(doc.vigencia_inicio)} — {formatarData(doc.vigencia_fim)}</span>
                  <div className="doc-actions">
                    <button className="btn-link" onClick={() => baixarDocumento(doc.id)}>Download</button>
                    <button className="btn-link success" onClick={() => atualizarStatusDocumental(doc, "VALIDADO")} disabled={salvando}>Validar</button>
                    <button className="btn-link danger" onClick={() => atualizarStatusDocumental(doc, "REJEITADO")} disabled={salvando}>Rejeitar</button>
                    <button className="btn-link" onClick={() => atualizarStatusDocumental(doc, "SUBSTITUIDO")} disabled={salvando}>Substituir</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
