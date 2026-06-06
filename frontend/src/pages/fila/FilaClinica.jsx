import { useEffect, useMemo, useRef, useState } from "react";
import { api } from "../../api/api";

export default function FilaClinica({ setActivePage }) {
  const [fila, setFila] = useState([]);
  const [alertas, setAlertas] = useState([]);
  const [resolucoes, setResolucoes] = useState([]);
  const [resumoAlertas, setResumoAlertas] = useState(null);
  const [carregando, setCarregando] = useState(false);
  const [abaAtiva, setAbaAtiva] = useState("alertas");
  const [modoAlertas, setModoAlertas] = useState("ativos");
  const [filtroPrioridade, setFiltroPrioridade] = useState("todos");
  const [busca, setBusca] = useState("");

  const [mostrarResolverAlerta, setMostrarResolverAlerta] = useState(false);
  const [alertaSelecionado, setAlertaSelecionado] = useState(null);
  const [dadosResolucao, setDadosResolucao] = useState({
    desfecho: "",
    observacoes: "",
  });

  const resolverModalRef = useRef(null);
  const [riscoPopulacional, setRiscoPopulacional] = useState([]);
  const [evolucaoRisco, setEvolucaoRisco] = useState([]);

  useEffect(() => {
    carregarFilaClinica();
    carregarRiscoPopulacional();
    carregarEvolucaoRisco();
  }, []);

  async function carregarFilaClinica() {
    try {
      setCarregando(true);

      const [filaResponse, alertasResponse, resolucoesResponse] = await Promise.all([
        api.get("/consultorio/fila-clinica"),
        api.get("/consultorio/alertas-clinicos-consolidados"),
        api.get("/consultorio/alertas-clinicos/resolucoes"),
      ]);

      setFila(filaResponse.data || []);
      setResumoAlertas(alertasResponse.data?.resumo || null);
      setAlertas(alertasResponse.data?.alertas || []);
      setResolucoes(resolucoesResponse.data?.resolucoes || []);
    } catch (error) {
      console.error("Erro ao carregar fila clínica:", error);
      setFila([]);
      setAlertas([]);
      setResolucoes([]);
      setResumoAlertas(null);
    } finally {
      setCarregando(false);
    }
  }

  function normalizarTexto(valor) {
    return String(valor || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function normalizarPrioridade(prioridade) {
    const texto = normalizarTexto(prioridade);

    if (texto.includes("maxima") || texto.includes("muito_alta") || texto.includes("muito alta")) {
      return "muito_alta";
    }

    if (texto.includes("alta")) return "alta";
    if (texto.includes("moderada")) return "moderada";
    if (texto.includes("baixa") || texto.includes("rotina")) return "baixa";

    return "baixa";
  }

  function corPrioridade(prioridade) {
    const nivel = normalizarPrioridade(prioridade);

    if (nivel === "muito_alta") return "#991b1b";
    if (nivel === "alta") return "#dc2626";
    if (nivel === "moderada") return "#f59e0b";

    return "#16a34a";
  }

  function rotuloPrioridade(prioridade) {
    const nivel = normalizarPrioridade(prioridade);

    if (nivel === "muito_alta") return "PRIORIDADE MÁXIMA";
    if (nivel === "alta") return "PRIORIDADE ALTA";
    if (nivel === "moderada") return "PRIORIDADE MODERADA";

    return "ROTINA / BAIXA";
  }

  function obterReferenciaAlerta(alerta) {
    return (
      alerta?.referencia?.atendimento_id ||
      alerta?.referencia?.evolucao_id ||
      alerta?.referencia?.bioimpedancia_id ||
      alerta?.referencia?.prontuario_id ||
      alerta?.referencia?.desfecho_id ||
      alerta?.atendimento_id ||
      alerta?.evolucao_id ||
      alerta?.bioimpedancia_id ||
      alerta?.data ||
      "sem-referencia"
    );
  }

  function criarChaveAlerta(alerta) {
    const origem = alerta?.origem || "origem";
    const tipo = alerta?.tipo || alerta?.tipo_alerta || "tipo";
    const pacienteId =
      alerta?.paciente_id ||
      alerta?.paciente_simplificado_id ||
      alerta?.referencia?.paciente_id ||
      alerta?.referencia?.paciente_simplificado_id ||
      "sem-paciente";
    const referencia = obterReferenciaAlerta(alerta);

    return `${origem}-${tipo}-${pacienteId}-${referencia}`;
  }

  function obterPacienteSimplificadoDoAlerta(alerta) {
    if (alerta?.referencia?.paciente_simplificado_id) return alerta.referencia.paciente_simplificado_id;
    if (alerta?.paciente_simplificado_id) return alerta.paciente_simplificado_id;

    if (["triagem_risco", "bioimpedancia", "alertas_pendentes"].includes(alerta?.origem)) {
      return alerta.paciente_id;
    }

    return null;
  }

  function obterPacienteClinicoDoAlerta(alerta) {
    if (alerta?.referencia?.paciente_clinico_id) return alerta.referencia.paciente_clinico_id;
    if (alerta?.paciente_clinico_id) return alerta.paciente_clinico_id;

    if (["evolucao_clinica", "desfecho", "consultorio_farmaceutico"].includes(alerta?.origem)) {
      return alerta.paciente_id;
    }

    return null;
  }

  const chavesResolvidas = useMemo(() => {
    return new Set((resolucoes || []).map((r) => r.alerta_chave));
  }, [resolucoes]);

  const alertasAtivos = useMemo(() => {
    return (alertas || []).filter((alerta) => !chavesResolvidas.has(criarChaveAlerta(alerta)));
  }, [alertas, chavesResolvidas]);

  const alertasResolvidos = useMemo(() => {
    return (resolucoes || []).map((r) => ({
      origem: r.alerta_origem || "resolucao",
      tipo: r.alerta_tipo || "alerta_resolvido",
      alerta_chave: r.alerta_chave,
      prioridade: r.prioridade,
      mensagem: r.mensagem_alerta,
      paciente_id: r.paciente_id,
      paciente_nome: r.paciente_nome,
      data: r.resolvido_em,
      resolvido: true,
      desfecho: r.desfecho,
      observacoes: r.observacoes,
      resolvido_por: r.resolvido_por,
      resolvido_em: r.resolvido_em,
    }));
  }, [resolucoes]);

  const alertasBase = modoAlertas === "ativos" ? alertasAtivos : alertasResolvidos;

  const alertasFiltrados = useMemo(() => {
    const termo = normalizarTexto(busca);

    return alertasBase.filter((alerta) => {
      const prioridadeOk = filtroPrioridade === "todos" || normalizarPrioridade(alerta.prioridade) === filtroPrioridade;

      const textoBusca = normalizarTexto([
        alerta.paciente_nome,
        alerta.mensagem,
        alerta.origem,
        alerta.tipo,
        alerta.prioridade,
        alerta.telefone,
      ].join(" "));

      return prioridadeOk && (!termo || textoBusca.includes(termo));
    });
  }, [alertasBase, filtroPrioridade, busca]);

  const filaFiltrada = useMemo(() => {
    const termo = normalizarTexto(busca);

    return fila.filter((item) => {
      const prioridadeOk = filtroPrioridade === "todos" || normalizarPrioridade(item.prioridade) === filtroPrioridade;

      const textoBusca = normalizarTexto([item.nome, item.resultado, item.prioridade, item.telefone].join(" "));

      return prioridadeOk && (!termo || textoBusca.includes(termo));
    });
  }, [fila, filtroPrioridade, busca]);

  function abrirConsultorio() {
    if (typeof setActivePage === "function") {
      setActivePage("consultorio");
    }
  }

  async function converterPacienteParaClinico(pacienteSimplificadoId) {
    if (!pacienteSimplificadoId) {
      alert("Paciente simplificado não identificado para conversão.");
      return;
    }

    try {
      await api.post(`/consultorio/converter-para-clinico/${pacienteSimplificadoId}`, {
        aceite_verbal: true,
        motivo_conversao: "Conversão indicada a partir da Fila Clínica Inteligente.",
        observacoes_prontuario: "Paciente convertido para acompanhamento clínico pelo painel de alertas.",
      });

      alert("Paciente convertido para acompanhamento clínico.");
      await carregarFilaClinica();
    } catch (error) {
      console.error("Erro ao converter paciente:", error);
      alert("Erro ao converter paciente para consultório.");
    }
  }

  function abrirModalResolucao(alerta) {
    setAlertaSelecionado(alerta);
    setDadosResolucao({ desfecho: "", observacoes: "" });
    setMostrarResolverAlerta(true);

    setTimeout(() => {
      resolverModalRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 100);
  }

  async function resolverAlertaClinico() {
    if (!alertaSelecionado) return;

    if (!dadosResolucao.desfecho) {
      alert("Selecione um desfecho para resolver o alerta.");
      return;
    }

    try {
      await api.post("/consultorio/alertas-clinicos/resolver", {
        alerta_origem: alertaSelecionado.origem,
        alerta_tipo: alertaSelecionado.tipo,
        alerta_chave: criarChaveAlerta(alertaSelecionado),
        paciente_id:
          alertaSelecionado.paciente_id ||
          alertaSelecionado.paciente_simplificado_id ||
          alertaSelecionado.referencia?.paciente_id ||
          alertaSelecionado.referencia?.paciente_simplificado_id ||
          null,
        paciente_nome: alertaSelecionado.paciente_nome,
        prioridade: alertaSelecionado.prioridade,
        mensagem_alerta: alertaSelecionado.mensagem,
        desfecho: dadosResolucao.desfecho,
        observacoes: dadosResolucao.observacoes,
      });

      alert("Alerta resolvido com sucesso.");
      setMostrarResolverAlerta(false);
      setAlertaSelecionado(null);
      setDadosResolucao({ desfecho: "", observacoes: "" });
      await carregarFilaClinica();
    } catch (error) {
      console.error("Erro ao resolver alerta:", error);
      alert("Erro ao resolver alerta clínico.");
    }
  }

  async function carregarRiscoPopulacional() {
  try {
    const response = await api.get(
      "/consultorio/classificacao-risco-populacional"
    );

    setRiscoPopulacional(response.data.pacientes || []);
  } catch (error) {
    console.error("Erro ao carregar risco populacional:", error);
    setRiscoPopulacional([]);
  }
}

  function renderAcoesAlerta(alerta) {
    const pacienteSimplificadoId = obterPacienteSimplificadoDoAlerta(alerta);
    const pacienteClinicoId = obterPacienteClinicoDoAlerta(alerta);
    const resolvido = chavesResolvidas.has(criarChaveAlerta(alerta));

    return (
      <div className="clinical-alert-actions">
        <button className="mini-action-button" onClick={abrirConsultorio}>
          Abrir consultório
        </button>

        {pacienteClinicoId && (
          <button className="mini-action-button" onClick={abrirConsultorio}>
            Ver prontuário
          </button>
        )}

        {pacienteSimplificadoId && (
          <button className="mini-action-button warning" onClick={() => converterPacienteParaClinico(pacienteSimplificadoId)}>
            Converter para consultório
          </button>
        )}

        {!resolvido && (
          <button className="mini-action-button success" onClick={() => abrirModalResolucao(alerta)}>
            Resolver alerta
          </button>
        )}
      </div>
    );
  }

  function obterRiscoPaciente(pacienteId) {
    return riscoPopulacional.find(
      (item) => Number(item.paciente_id) === Number(pacienteId)
    );
  }

  const resumoPrioridades = useMemo(() => {
  const base = abaAtiva === "fila" ? filaFiltrada : alertasFiltrados;

  const resumo = {
    total: base.length,
    muito_alta: 0,
    alta: 0,
    moderada: 0,
    baixa: 0,
  };

    base.forEach((item) => {
      const prioridade = normalizarPrioridade(item.prioridade);
      resumo[prioridade] += 1;
    });

    return resumo;
  }, [abaAtiva, filaFiltrada, alertasFiltrados]);

  async function carregarEvolucaoRisco() {
    try {
      const response = await api.get(
        "/consultorio/evolucao-risco-populacional"
      );

      setEvolucaoRisco(response.data.pacientes || []);
    } catch (error) {
      console.error("Erro ao carregar evolução do risco:", error);
      setEvolucaoRisco([]);
    }
  }

  function obterEvolucaoRiscoPaciente(pacienteId) {
  return evolucaoRisco.find(
    (item) => Number(item.paciente_id) === Number(pacienteId)
  );
}

  return (
    <div>
      <div className="section-header-row">
        <div>
          <h2>Fila Clínica Inteligente</h2>
          <p className="muted">
            Central de priorização clínica, alertas automáticos e encaminhamento para o Consultório Farmacêutico.
          </p>
        </div>

        <button className="secondary-button" onClick={carregarFilaClinica}>
          Atualizar fila
        </button>
      </div>

      <div className="filters-row">
        <input
          className="input"
          placeholder="Buscar por paciente, alerta, telefone ou resultado"
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
        />

        <select className="input" value={filtroPrioridade} onChange={(e) => setFiltroPrioridade(e.target.value)}>
          <option value="todos">Todas as prioridades</option>
          <option value="muito_alta">Prioridade máxima</option>
          <option value="alta">Alta</option>
          <option value="moderada">Moderada</option>
          <option value="baixa">Baixa / rotina</option>
        </select>
      </div>

      <div className="cards-grid four">
        <div className="metric-card">
          <span>{abaAtiva === "fila" ? "Pacientes na fila" : "Alertas exibidos"}</span>
          <strong>{resumoPrioridades.total}</strong>
        </div>

        <div className="metric-card danger">
          <span>Máxima/Alta</span>
          <strong>{resumoPrioridades.muito_alta + resumoPrioridades.alta}</strong>
        </div>

        <div className="metric-card warning">
          <span>Moderada</span>
          <strong>{resumoPrioridades.moderada}</strong>
        </div>

        <div className="metric-card success">
          <span>{abaAtiva === "alertas" ? "Resolvidos" : "Baixa/Rotina"}</span>
          <strong>
            {abaAtiva === "alertas"
              ? alertasResolvidos.length
              : resumoPrioridades.baixa}
          </strong>
        </div>
      </div>
      <div className="tab-buttons">
        <button className={abaAtiva === "alertas" ? "active" : ""} onClick={() => setAbaAtiva("alertas")}>
          Alertas clínicos
        </button>
        <button className={abaAtiva === "fila" ? "active" : ""} onClick={() => setAbaAtiva("fila")}>
          Fila por prioridade
        </button>
      </div>

      {abaAtiva === "alertas" && (
        <div className="form-card">
          <div className="section-header-row">
            <div>
              <h3>Alertas clínicos</h3>
              <p className="muted">Acompanhe os alertas ativos e resolvidos.</p>
            </div>
          </div>

          <div className="tab-buttons">
            <button className={modoAlertas === "ativos" ? "active" : ""} onClick={() => setModoAlertas("ativos")}>
              Ativos ({alertasAtivos.length})
            </button>
            <button className={modoAlertas === "resolvidos" ? "active" : ""} onClick={() => setModoAlertas("resolvidos")}>
              Resolvidos ({alertasResolvidos.length})
            </button>
          </div>

          {carregando ? (
            <p className="muted">Carregando alertas...</p>
          ) : alertasFiltrados.length === 0 ? (
            <p className="muted">Nenhum alerta {modoAlertas === "ativos" ? "ativo" : "resolvido"} encontrado.</p>
          ) : (
            <div className="clinical-alert-list">
              {alertasFiltrados.map((alerta, index) => {
                const cor = corPrioridade(alerta.prioridade);
                const resolvido = chavesResolvidas.has(criarChaveAlerta(alerta));

                return (
                  <div
                    key={`${criarChaveAlerta(alerta)}-${index}`}
                    className={`clinical-alert-item ${normalizarPrioridade(alerta.prioridade)} ${resolvido ? "resolvido" : ""}`}
                    style={{ borderLeftColor: cor }}
                  >
                    <div className="clinical-alert-main">
                      <div>
                        <strong>{alerta.paciente_nome || "Paciente não informado"}</strong>
                        <p>{alerta.mensagem}</p>

                        <span className="timeline-tag">{alerta.origem || "origem não informada"}</span>
                        {alerta.tipo && <span className="timeline-tag warning">{alerta.tipo}</span>}
                        {resolvido && <span className="timeline-tag">Resolvido</span>}
                        {obterRiscoPaciente(alerta.paciente_id) && (
                        <span
                          className={`clinical-badge ${obterRiscoPaciente(alerta.paciente_id).risco}`}
                        >
                          Risco {obterRiscoPaciente(alerta.paciente_id).risco} · Score{" "}
                          {obterRiscoPaciente(alerta.paciente_id).score}
                        </span>
)}
                      </div>

                      <div className="clinical-alert-side">
                        <span className="risk-badge" style={{ background: cor }}>
                          {rotuloPrioridade(alerta.prioridade)}
                        </span>
                        <small>{alerta.data ? new Date(alerta.data).toLocaleDateString("pt-BR") : "Sem data"}</small>
                      </div>
                      {obterEvolucaoRiscoPaciente(alerta.paciente_id) && (
                        <span
                          className={`timeline-tag ${
                            obterEvolucaoRiscoPaciente(alerta.paciente_id).tendencia
                          }`}
                        >
                          {obterEvolucaoRiscoPaciente(alerta.paciente_id).tendencia === "melhora"
                            ? "↓ Melhora"
                            : obterEvolucaoRiscoPaciente(alerta.paciente_id).tendencia === "piora"
                            ? "↑ Piora"
                            : "→ Estável"}{" "}
                          (
                          {obterEvolucaoRiscoPaciente(alerta.paciente_id).diferenca_score > 0
                            ? "+"
                            : ""}
                          {obterEvolucaoRiscoPaciente(alerta.paciente_id).diferenca_score})
                        </span>
                      )}
                    </div>

                    {renderAcoesAlerta(alerta)}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {abaAtiva === "fila" && (
        <div className="form-card">
          <h3>Fila por prioridade</h3>

          {carregando ? (
            <p className="muted">Carregando fila clínica...</p>
          ) : filaFiltrada.length === 0 ? (
            <p className="muted">Nenhum paciente encontrado na fila.</p>
          ) : (
            <div className="fila-grid">
              {filaFiltrada.map((item, index) => {
                const cor = corPrioridade(item.prioridade);

                return (
                  <div
                    key={`${item.paciente_id || "paciente"}-${index}`}
                    className="fila-card"
                    style={{ borderLeft: `8px solid ${cor}` }}
                  >
                    <div className="fila-top">
                      <h3>{item.nome}</h3>
                      <span className="risk-badge" style={{ background: cor }}>
                        {item.prioridade}
                      </span>
                    </div>

                    <p><strong>Último atendimento:</strong> {item.ultimo_atendimento || "—"}</p>
                    <p><strong>Resultado:</strong> {item.resultado || "—"}</p>
                    {item.telefone && <p><strong>Telefone:</strong> {item.telefone}</p>}

                    <div className="clinical-alert-actions">
                      <button className="primary-button" onClick={abrirConsultorio}>
                        Abrir no consultório
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {mostrarResolverAlerta && (
        <div className="modal-overlay">
          <div className="modal-content" ref={resolverModalRef}>
            <h3>Resolver alerta clínico</h3>

            <p><strong>{alertaSelecionado?.paciente_nome || "Paciente não informado"}</strong></p>
            <p>{alertaSelecionado?.mensagem}</p>

            <select
              className="input"
              value={dadosResolucao.desfecho}
              onChange={(e) => setDadosResolucao({ ...dadosResolucao, desfecho: e.target.value })}
            >
              <option value="">Selecione o desfecho</option>
              <option value="resolvido">Resolvido</option>
              <option value="encaminhado_para_consultorio">Encaminhado para consultório</option>
              <option value="monitoramento">Mantido em monitoramento</option>
              <option value="sem_adesao">Sem adesão</option>
              <option value="encaminhado_urgencia">Encaminhado para urgência</option>
              <option value="outro">Outro</option>
            </select>

            <textarea
              className="textarea"
              placeholder="Observações"
              value={dadosResolucao.observacoes}
              onChange={(e) => setDadosResolucao({ ...dadosResolucao, observacoes: e.target.value })}
            />

            <div className="modal-actions">
              <button
                className="secondary-button"
                onClick={() => {
                  setMostrarResolverAlerta(false);
                  setAlertaSelecionado(null);
                }}
              >
                Cancelar
              </button>

              <button className="primary-button" onClick={resolverAlertaClinico}>
                Salvar resolução
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
