import { useEffect, useMemo, useState } from "react";
import { api } from "../../api/api";
import "./AgendaIntegrada.css";
import CentralNotificacoes from "./CentralNotificacoes";

export default function AgendaIntegrada() {
  const [eventos, setEventos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filtroServico, setFiltroServico] = useState("todos");
  const [filtroStatus, setFiltroStatus] = useState("ativos");
  const [mostrarFormulario, setMostrarFormulario] = useState(false);
  const [capacidadeDia, setCapacidadeDia] = useState(null);
  const [sugestoesDatas, setSugestoesDatas] = useState([]);
  const [periodoAgenda, setPeriodoAgenda] = useState("30");
  const [notificacoes, setNotificacoes] = useState(null);
  const [filtroAlerta, setFiltroAlerta] = useState("");
  const [mostrarNotificacoes, setMostrarNotificacoes] = useState(false);
  const [buscaPaciente, setBuscaPaciente] = useState("");
  const [pacientesEncontrados, setPacientesEncontrados] = useState([]);
  const [buscandoPaciente, setBuscandoPaciente] = useState(false);
  const [buscaCeaf, setBuscaCeaf] = useState("");
  const [pacientesCeafEncontrados, setPacientesCeafEncontrados] = useState([]);
  const [buscandoCeaf, setBuscandoCeaf] = useState(false);
  const [contextoCeaf, setContextoCeaf] = useState(null);
  const [reagendamento, setReagendamento] = useState(null);
  const [historicoAgenda, setHistoricoAgenda] = useState(null);

  const [novoEvento, setNovoEvento] = useState({
    paciente_id: null,
    paciente_ceaf_id: null,
    paciente_clinico_id: null,
    paciente_nome: "",
    telefone: "",
    servico_origem: "dispensacao",
    tipo_evento: "retirada_medicamento",
    medicamento: "",
    situacao_laudo: "",
    data_evento: "",
    data_inicio_vigencia: "",
    data_fim_vigencia: "",
    observacoes: "",
    notificar_whatsapp: true,
  });

  function gerarParametrosPeriodo(periodo) {
    if (periodo === "todos") {
      return {};
    }

    const hojeLocal = new Date();
    hojeLocal.setHours(0, 0, 0, 0);

    const dataFim = new Date(hojeLocal);
    dataFim.setDate(dataFim.getDate() + Number(periodo));

    return {
      data_inicio: hojeLocal.toISOString().split("T")[0],
      data_fim: dataFim.toISOString().split("T")[0],
    };
  }

  async function carregarAgenda() {
    try {
      setLoading(true);

      const response = await api.get("/consultorio/agenda", {
        params: gerarParametrosPeriodo(periodoAgenda),
      });

      setEventos(response.data.eventos || []);

      const notificacoesResponse = await api.get(
        "/consultorio/agenda/notificacoes"
      );

      setNotificacoes(notificacoesResponse.data || null);
    } catch (error) {
      console.error("Erro ao carregar agenda integrada:", error);
      alert("Erro ao carregar agenda integrada.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    carregarAgenda();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [periodoAgenda]);

  const hoje = new Date().toISOString().slice(0, 10);

  const statusEncerradosAgenda = ["cancelado", "reagendado", "realizado", "concluido"];
  const statusOperacionaisAgenda = [
    "agendado",
    "notificado",
    "retirada_prevista",
    "renovacao_recomendada",
    "renovacao_urgente",
    "risco_interrupcao_tratamento",
    "faltou",
  ];
  const tiposRetiradaAgenda = ["retirada_medicamento", "retirada", "retirada_prevista", "dispensacao"];
  const tiposRenovacaoAgenda = ["renovacao_lme", "renovacao_laudo", "pendencia_documental", "renovacao_lme_ceaf"];

  function normalizarTexto(valor) {
    return String(valor || "").trim().toLowerCase();
  }

  function ehRetirada(evento) {
    return tiposRetiradaAgenda.includes(normalizarTexto(evento.tipo_evento));
  }

  function ehRenovacao(evento) {
    return tiposRenovacaoAgenda.includes(normalizarTexto(evento.tipo_evento));
  }

  function ehAtivoOperacional(evento) {
    const status = normalizarTexto(evento.status);
    return !statusEncerradosAgenda.includes(status);
  }

  function categoriaOk(evento, filtro) {
    const origem = normalizarTexto(evento.servico_origem);
    if (filtro === "todos") return true;
    if (filtro === "consultorio") return origem === "consultorio";
    if (filtro === "intervencao") return origem === "intervencao";
    if (filtro === "dispensacao") return ehRetirada(evento);
    if (filtro === "renovacao_laudo") return ehRenovacao(evento);
    return true;
  }

  function laudoVencido(dataFimVigencia) {
    if (!dataFimVigencia) return false;
    const dataFim = new Date(`${dataFimVigencia}T00:00:00`);
    const hojeLocal = new Date();
    hojeLocal.setHours(0, 0, 0, 0);
    return dataFim < hojeLocal;
  }

  const retiradaComLaudoVencido =
    novoEvento.tipo_evento === "retirada_medicamento" &&
    laudoVencido(novoEvento.data_fim_vigencia);

  const eventosFiltrados = useMemo(() => {
    return eventos.filter((evento) => {
      const status = normalizarTexto(evento.status);
      const servicoOk = categoriaOk(evento, filtroServico);

      const statusOk =
        filtroStatus === "todos" ||
        (filtroStatus === "ativos" && ehAtivoOperacional(evento)) ||
        status === filtroStatus;

      if (!servicoOk || !statusOk) {
        return false;
      }

      if (filtroAlerta === "dispensacoes_amanha") {
        const amanha = new Date();
        amanha.setDate(amanha.getDate() + 1);
        const dataAmanha = amanha.toISOString().split("T")[0];

        return (
          ehRetirada(evento) &&
          ["agendado", "notificado"].includes(status) &&
          evento.data_evento === dataAmanha
        );
      }

      if (filtroAlerta === "dispensacoes_atrasadas") {
        const hojeLocal = new Date();
        hojeLocal.setHours(0, 0, 0, 0);
        const dataEvento = evento.data_evento
          ? new Date(evento.data_evento + "T00:00:00")
          : null;

        return (
          ehRetirada(evento) &&
          ["agendado", "notificado", "retirada_prevista"].includes(status) &&
          dataEvento &&
          dataEvento < hojeLocal
        );
      }

      if (filtroAlerta === "renovacao_urgente") {
        return ehRenovacao(evento) && ["agendado", "notificado", "renovacao_urgente"].includes(status);
      }

      if (filtroAlerta === "renovacao_recomendada") {
        return ehRenovacao(evento) && ["agendado", "notificado", "renovacao_recomendada"].includes(status);
      }

      if (filtroAlerta) {
        return status === filtroAlerta;
      }

      return true;
    });
  }, [eventos, filtroServico, filtroStatus, filtroAlerta]);

  const resumoOperacional = useMemo(() => {
    const eventosAtivos = eventos.filter(ehAtivoOperacional);
    const eventosConfirmados = eventosAtivos.filter((evento) => {
      const status = normalizarTexto(evento.status);
      return ["agendado", "notificado", "faltou", "renovacao_recomendada", "renovacao_urgente", "risco_interrupcao_tratamento"].includes(status);
    });

    const proximos7 = eventosConfirmados.filter((evento) => {
      if (!evento.data_evento) return false;

      const dataEvento = new Date(`${evento.data_evento}T00:00:00`);
      const dataHoje = new Date(`${hoje}T00:00:00`);
      const diff = (dataEvento - dataHoje) / (1000 * 60 * 60 * 24);

      return diff >= 0 && diff <= 7;
    });

    return {
      hoje: eventosConfirmados.filter((e) => e.data_evento === hoje).length,
      proximos7: proximos7.length,
      pendentes: eventosConfirmados.filter((e) => ["agendado", "notificado", "faltou"].includes(normalizarTexto(e.status))).length,
      retiradasPrevistas: eventosAtivos.filter((e) => normalizarTexto(e.status) === "retirada_prevista").length,
      atrasados: eventosAtivos.filter(
        (e) => e.data_evento < hoje && ["agendado", "notificado", "retirada_prevista"].includes(normalizarTexto(e.status))
      ).length,
      realizados: eventos.filter((e) => ["realizado", "concluido"].includes(normalizarTexto(e.status))).length,
    };
  }, [eventos, hoje]);

  async function buscarPacientesAgenda(termo) {
    setBuscaPaciente(termo);

    if (!termo || termo.trim().length < 3) {
      setPacientesEncontrados([]);
      return;
    }

    try {
      setBuscandoPaciente(true);

      const response = await api.get("/consultorio/agenda/pacientes/buscar", {
        params: { termo: termo.trim() },
      });

      setPacientesEncontrados(response.data.pacientes || []);
    } catch (error) {
      console.error("Erro ao buscar pacientes:", error);
      setPacientesEncontrados([]);
    } finally {
      setBuscandoPaciente(false);
    }
  }

  function selecionarPacienteAgenda(paciente) {
    setNovoEvento({
      ...novoEvento,
      paciente_id: paciente.id,
      paciente_nome: paciente.nome || "",
      telefone: paciente.telefone || "",
    });

    setBuscaPaciente(paciente.nome || "");
    setPacientesEncontrados([]);
  }


  async function buscarPacientesCeafAgenda(termo) {
    setBuscaCeaf(termo);

    if (!termo || termo.trim().length < 3) {
      setPacientesCeafEncontrados([]);
      return;
    }

    try {
      setBuscandoCeaf(true);
      const response = await api.get("/consultorio/agenda/pacientes-ceaf/buscar", {
        params: { termo: termo.trim() },
      });
      setPacientesCeafEncontrados(response.data.pacientes || []);
    } catch (error) {
      console.error("Erro ao buscar pacientes CEAF:", error);
      setPacientesCeafEncontrados([]);
    } finally {
      setBuscandoCeaf(false);
    }
  }

  async function selecionarPacienteCeafAgenda(paciente) {
    try {
      const response = await api.get(`/consultorio/agenda/pacientes-ceaf/${paciente.id}/contexto`);
      const contexto = response.data;
      const dadosPaciente = contexto.paciente || paciente;
      const sugestao = contexto.sugestao || {};

      setContextoCeaf(contexto);
      setNovoEvento({
        ...novoEvento,
        paciente_ceaf_id: dadosPaciente.id,
        paciente_clinico_id: dadosPaciente.paciente_clinico_id || null,
        paciente_id: dadosPaciente.paciente_agenda_id || null,
        paciente_nome: dadosPaciente.nome || "",
        telefone: dadosPaciente.telefone || dadosPaciente.telefone_celular || "",
        servico_origem: sugestao.servico_origem || "CEAF",
        tipo_evento: "retirada_medicamento",
        prioridade: sugestao.prioridade || "NORMAL",
        medicamento: dadosPaciente.medicamento_prescrito || "",
        situacao_laudo: dadosPaciente.situacao_lme || "",
        data_evento: "",
        data_inicio_vigencia: dadosPaciente.data_inicio_medicamento || "",
        data_fim_vigencia: dadosPaciente.data_fim_vigencia || "",
        observacoes: "",
        notificar_whatsapp: true,
      });

      setBuscaCeaf(dadosPaciente.nome || "");
      setPacientesCeafEncontrados([]);
    } catch (error) {
      console.error("Erro ao carregar contexto CEAF:", error);
      alert("Erro ao carregar dados do paciente CEAF.");
    }
  }

  async function gerarAgendaCeafAutomatica() {
    if (!confirm("Gerar agenda CEAF automaticamente para pacientes com vigência registrada?")) {
      return;
    }
    try {
      const response = await api.post("/consultorio/agenda/gerar-ceaf", null, {
        params: { dias_antes_vigencia: 30 },
      });
      alert(
        `Agenda CEAF processada. Criados: ${response.data.criados || 0}. Existentes: ${response.data.existentes || 0}. Ignorados: ${response.data.ignorados || 0}.`
      );
      await carregarAgenda();
    } catch (error) {
      console.error("Erro ao gerar agenda CEAF:", error);
      alert("Erro ao gerar agenda CEAF automática.");
    }
  }

  function abrirReagendamento(evento) {
    setReagendamento({
      evento,
      nova_data: evento.data_evento || "",
      motivo: "",
      tipo_motivo: "equipe",
      observacoes: "",
    });
  }

  async function salvarReagendamento() {
    if (!reagendamento?.nova_data || !reagendamento?.motivo?.trim()) {
      alert("Informe a nova data e o motivo do reagendamento.");
      return;
    }
    try {
      await api.post(`/consultorio/agenda/${reagendamento.evento.id}/reagendar`, {
        nova_data: reagendamento.nova_data,
        motivo: reagendamento.motivo,
        tipo_motivo: reagendamento.tipo_motivo,
        observacoes: reagendamento.observacoes,
      });
      setReagendamento(null);
      await carregarAgenda();
    } catch (error) {
      console.error("Erro ao reagendar:", error);
      alert("Erro ao reagendar compromisso.");
    }
  }

  async function carregarHistoricoAgenda(evento) {
    try {
      const response = await api.get(`/consultorio/agenda/${evento.id}/historico`);
      setHistoricoAgenda({ evento, historico: response.data.historico || [] });
    } catch (error) {
      console.error("Erro ao carregar histórico:", error);
      alert("Erro ao carregar histórico do agendamento.");
    }
  }

  async function atualizarStatus(evento, status) {
    try {
      const response = await api.post(`/consultorio/agenda/${evento.id}/status`, {
        status,
      });

      if (response.data.proximo_agendamento) {
        if (response.data.proximo_agendamento.origem === "risco_interrupcao") {
          alert(
            "A próxima dispensação não foi agendada porque a vigência do laudo termina antes da próxima retirada prevista. Foi gerado alerta de risco de interrupção do tratamento."
          );
        } else {
          alert(
            `Nova dispensação agendada para ${new Date(
              response.data.proximo_agendamento.data_evento + "T00:00:00"
            ).toLocaleDateString("pt-BR")} (30 dias após a retirada).`
          );
        }
      }

      await carregarAgenda();
    } catch (error) {
      console.error("Erro ao atualizar status:", error);
      alert("Erro ao atualizar status.");
    }
  }

  function limparFormularioEvento() {
    setNovoEvento({
      paciente_id: null,
      paciente_ceaf_id: null,
      paciente_clinico_id: null,
      paciente_nome: "",
      telefone: "",
      servico_origem: "dispensacao",
      tipo_evento: "retirada_medicamento",
      medicamento: "",
      situacao_laudo: "",
      data_evento: "",
      data_inicio_vigencia: "",
      data_fim_vigencia: "",
      observacoes: "",
      notificar_whatsapp: true,
    });

    setBuscaPaciente("");
    setPacientesEncontrados([]);
    setBuscaCeaf("");
    setPacientesCeafEncontrados([]);
    setContextoCeaf(null);
    setCapacidadeDia(null);
    setSugestoesDatas([]);
    setMostrarFormulario(false);
  }

  async function salvarNovoEvento() {
    if (!novoEvento.paciente_nome.trim()) {
      alert("Informe o nome do paciente.");
      return;
    }

    if (retiradaComLaudoVencido) {
      alert("Não é permitido agendar retirada de medicamento quando a vigência da LME está vencida. Selecione renovação de LME ou atualize a vigência antes de agendar a retirada.");
      return;
    }

    if (novoEvento.data_evento) {
      const hojeLocal = new Date();
      hojeLocal.setHours(0, 0, 0, 0);

      const dataSelecionada = new Date(`${novoEvento.data_evento}T00:00:00`);

      if (dataSelecionada < hojeLocal) {
        alert("Não é permitido agendar em data passada.");
        return;
      }
    }

    try {
      const payload = {
        ...novoEvento,
        data_evento: novoEvento.data_evento || null,
        data_inicio_vigencia: novoEvento.data_inicio_vigencia || null,
        data_fim_vigencia: novoEvento.data_fim_vigencia || null,
      };

      const response = await api.post("/consultorio/agenda", payload);

      if (response.data.alerta_capacidade?.warning) {
        alert(response.data.alerta_capacidade.mensagem);
      }

      await carregarAgenda();
      limparFormularioEvento();
    } catch (error) {
      console.error("Erro ao salvar evento:", error);
      alert("Erro ao salvar cadastro/evento da agenda.");
    }
  }

  async function verificarCapacidadeDia(servico, data) {
    if (!servico || !data) {
      setCapacidadeDia(null);
      setSugestoesDatas([]);
      return;
    }

    try {
      const response = await api.get("/consultorio/agenda/capacidade-dia", {
        params: {
          servico_origem: servico,
          data_evento: data,
        },
      });

      setCapacidadeDia(response.data);

      if (response.data.capacidade_atingida) {
        const sugestoesResponse = await api.get(
          "/consultorio/agenda/sugerir-datas",
          {
            params: {
              servico_origem: servico,
              data_inicial: data,
            },
          }
        );

        setSugestoesDatas(sugestoesResponse.data.sugestoes || []);
      } else {
        setSugestoesDatas([]);
      }
    } catch (error) {
      console.error("Erro ao verificar capacidade:", error);
      setCapacidadeDia(null);
      setSugestoesDatas([]);
    }
  }

  function classeLinhaAgenda(status) {
    if (status === "risco_interrupcao_tratamento") return "agenda-risco";
    if (status === "renovacao_urgente") return "agenda-urgente";
    if (status === "renovacao_recomendada") return "agenda-atencao";
    if (status === "realizado") return "agenda-sucesso";
    if (status === "atrasado") return "agenda-atrasado";
    return "";
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h2>Agenda Integrada da Farmácia Escola</h2>
          <p className="muted">
            Consolida compromissos do consultório, intervenções, dispensação e renovação de laudos.
          </p>
        </div>

        <div className="action-buttons">
          <button
            className="primary-button"
            onClick={() => setMostrarFormulario(true)}
          >
            Novo cadastro / evento
          </button>

          <button className="secondary-button" onClick={carregarAgenda}>
            Atualizar
          </button>

          <button className="secondary-button" onClick={gerarAgendaCeafAutomatica}>
            Gerar agenda CEAF
          </button>

          <button
            className="secondary-button"
            onClick={() => setMostrarNotificacoes(!mostrarNotificacoes)}
          >
            {mostrarNotificacoes ? "Ocultar notificações" : "Central de Notificações"}
          </button>
        </div>
      </div>

      {mostrarNotificacoes && (
        <CentralNotificacoes />
      )}

      <div className="cards-grid six">
        <div className="metric-card">
          <span>Hoje</span>
          <strong>{resumoOperacional.hoje}</strong>
        </div>

        <div className="metric-card warning">
          <span>Próximos 7 dias</span>
          <strong>{resumoOperacional.proximos7}</strong>
        </div>

        <div className="metric-card">
          <span>Pendentes</span>
          <strong>{resumoOperacional.pendentes}</strong>
        </div>

        <div className="metric-card warning">
          <span>Retiradas previstas</span>
          <strong>{resumoOperacional.retiradasPrevistas}</strong>
        </div>

        <div className="metric-card danger">
          <span>Atrasados</span>
          <strong>{resumoOperacional.atrasados}</strong>
        </div>

        <div className="metric-card success">
          <span>Realizados</span>
          <strong>{resumoOperacional.realizados}</strong>
        </div>
      </div>

      {notificacoes?.resumo && (
        <div className="form-card">
          <div className="section-header">
            <div>
              <h3>Central de alertas</h3>
              <p className="muted">
                Prioriza riscos de interrupção, renovações e dispensações previstas para amanhã.
              </p>
            </div>
          </div>

          <div className="dashboard-grid">
            <div className="summary-card agenda-risco clickable-card" onClick={() => setFiltroAlerta("risco_interrupcao_tratamento")}>
              <strong>Risco de interrupção</strong>
              <div>{notificacoes.resumo.risco_interrupcao || 0}</div>
            </div>

            <div className="summary-card agenda-urgente clickable-card" onClick={() => setFiltroAlerta("renovacao_urgente")}>
              <strong>Renovações urgentes</strong>
              <div>{notificacoes.resumo.renovacoes_urgentes || 0}</div>
            </div>

            <div className="summary-card agenda-atencao clickable-card" onClick={() => setFiltroAlerta("renovacao_recomendada")}>
              <strong>Renovações recomendadas</strong>
              <div>{notificacoes.resumo.renovacoes_recomendadas || 0}</div>
            </div>

            <div className="summary-card agenda-sucesso clickable-card" onClick={() => setFiltroAlerta("dispensacoes_amanha")}>
              <strong>Dispensações amanhã</strong>
              <div>{notificacoes.resumo.dispensacoes_amanha || 0}</div>
            </div>
          </div>
        </div>
      )}

      {mostrarFormulario && (
        <div className="form-card">
          <div className="section-header">
            <div>
              <h3>Novo cadastro / evento da agenda</h3>
              <p className="muted">
                Cadastre pacientes manualmente e, quando necessário, informe a data prevista de retirada, vigência do laudo ou observações.
              </p>
            </div>
          </div>

          <div className="filters-row">
            <label>
              Buscar paciente CEAF
              <input
                value={buscaCeaf}
                onChange={(e) => buscarPacientesCeafAgenda(e.target.value)}
                placeholder="Nome, CPF, CNS ou medicamento"
              />
            </label>

            {buscandoCeaf && <div className="clinical-summary">Buscando paciente CEAF...</div>}

            {pacientesCeafEncontrados.length > 0 && (
              <div className="form-card full-width-card">
                <h4>Pacientes CEAF encontrados</h4>
                <div className="action-buttons">
                  {pacientesCeafEncontrados.map((paciente) => (
                    <button
                      key={paciente.id}
                      type="button"
                      className="secondary-button"
                      onClick={() => selecionarPacienteCeafAgenda(paciente)}
                    >
                      {paciente.nome} — {paciente.medicamento_prescrito || "sem medicamento"}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <label>
              Buscar paciente cadastrado
              <input
                value={buscaPaciente}
                onChange={(e) => buscarPacientesAgenda(e.target.value)}
                placeholder="Digite pelo menos 3 letras, CPF ou CNS"
              />
            </label>

            {buscandoPaciente && (
              <div className="clinical-summary">
                Buscando paciente...
              </div>
            )}

            {pacientesEncontrados.length > 0 && (
              <div className="form-card">
                <h4>Pacientes encontrados</h4>

                <div className="action-buttons">
                  {pacientesEncontrados.map((paciente) => (
                    <button
                      key={paciente.id}
                      type="button"
                      className="secondary-button"
                      onClick={() => selecionarPacienteAgenda(paciente)}
                    >
                      {paciente.nome} — {paciente.telefone || "sem telefone"}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <label>
              Nome do paciente
              <input
                value={novoEvento.paciente_nome}
                onChange={(e) =>
                  setNovoEvento({ ...novoEvento, paciente_nome: e.target.value })
                }
                placeholder="Nome completo"
              />
            </label>

            <label>
              Telefone / WhatsApp
              <input
                value={novoEvento.telefone}
                onChange={(e) =>
                  setNovoEvento({ ...novoEvento, telefone: e.target.value })
                }
                placeholder="67999999999"
              />
            </label>

            <label>
              Serviço
              <select
                value={novoEvento.servico_origem}
                onChange={(e) => {
                  const servico = e.target.value;

                  setNovoEvento({
                    ...novoEvento,
                    servico_origem: servico,
                  });

                  verificarCapacidadeDia(servico, novoEvento.data_evento);
                }}
              >
                <option value="consultorio">Consultório</option>
                <option value="intervencao">Intervenção</option>
                <option value="dispensacao">Dispensação</option>
                <option value="renovacao_laudo">Renovação de laudo</option>
                <option value="CEAF">CEAF</option>
              </select>
            </label>

            <label>
              Tipo de evento
              <select
                value={novoEvento.tipo_evento}
                onChange={(e) => {
                  const tipoSelecionado = e.target.value;
                  const deveLimparData =
                    tipoSelecionado === "retirada_medicamento" &&
                    laudoVencido(novoEvento.data_fim_vigencia);

                  setNovoEvento({
                    ...novoEvento,
                    tipo_evento: tipoSelecionado,
                    data_evento: deveLimparData ? "" : novoEvento.data_evento,
                  });
                }}
              >
                <option value="retirada_medicamento">Retirada de medicamento</option>
                <option value="RENOVACAO_LME">Renovação de LME CEAF</option>
                <option value="retorno_plano_cuidado">Retorno plano de cuidado</option>
                <option value="retorno_intervencao">Retorno intervenção</option>
                <option value="renovacao_laudo">Renovação de laudo</option>
                <option value="risco_perda_medicacao">Risco de perda da medicação</option>
                <option value="risco_encerramento_processo">Risco de encerramento do processo</option>
              </select>
            </label>

            <label>
              Medicamento
              <input
                value={novoEvento.medicamento}
                onChange={(e) =>
                  setNovoEvento({ ...novoEvento, medicamento: e.target.value })
                }
                placeholder="Medicamento"
              />
            </label>

            <label>
              Situação LME
              <input
                value={novoEvento.situacao_laudo}
                onChange={(e) => setNovoEvento({ ...novoEvento, situacao_laudo: e.target.value })}
                placeholder="Situação LME"
              />
            </label>

            <label>
              Data prevista
              <input
                type="date"
                value={novoEvento.data_evento}
                disabled={retiradaComLaudoVencido}
                onChange={(e) => {
                  const data = e.target.value;

                  setNovoEvento({
                    ...novoEvento,
                    data_evento: data,
                  });

                  verificarCapacidadeDia(novoEvento.servico_origem, data);
                }}
              />
            </label>

            {retiradaComLaudoVencido && (
              <div className="clinical-summary danger">
                A data prevista fica bloqueada para retirada de medicamento porque a LME está vencida. Selecione renovação de LME ou atualize a vigência antes de agendar retirada.
              </div>
            )}

            {capacidadeDia && (
              <div
                className={`clinical-summary ${
                  capacidadeDia.capacidade_atingida ? "danger" : "success"
                }`}
              >
                <strong>Capacidade do dia:</strong>

                <p>
                  {capacidadeDia.capacidade_configurada ? (
                    <>
                      {capacidadeDia.agendados} agendado(s) de{" "}
                      {capacidadeDia.capacidade_maxima} vaga(s).{" "}
                      {capacidadeDia.vagas_disponiveis} vaga(s) disponível(is).
                    </>
                  ) : (
                    <>Não há capacidade configurada para este serviço neste dia.</>
                  )}
                </p>

                {capacidadeDia.capacidade_atingida && (
                  <p>Capacidade diária atingida. Considere escolher outra data.</p>
                )}
              </div>
            )}

            {sugestoesDatas.length > 0 && (
              <div className="form-card">
                <h4>Datas sugeridas</h4>

                <div className="action-buttons">
                  {sugestoesDatas.map((item) => (
                    <button
                      key={item.data}
                      type="button"
                      className="secondary-button"
                      onClick={() => {
                        setNovoEvento({
                          ...novoEvento,
                          data_evento: item.data,
                        });

                        verificarCapacidadeDia(novoEvento.servico_origem, item.data);
                      }}
                    >
                      {new Date(item.data + "T00:00:00").toLocaleDateString("pt-BR")} — {" "}
                      {item.vagas_disponiveis} vaga(s)
                    </button>
                  ))}
                </div>
              </div>
            )}

            <label>
              Início vigência do laudo
              <input
                type="date"
                value={novoEvento.data_inicio_vigencia}
                onChange={(e) =>
                  setNovoEvento({
                    ...novoEvento,
                    data_inicio_vigencia: e.target.value,
                  })
                }
              />
            </label>

            <label>
              Fim vigência do laudo
              <input
                type="date"
                value={novoEvento.data_fim_vigencia}
                onChange={(e) => {
                  const novaDataFim = e.target.value;
                  const deveLimparData =
                    novoEvento.tipo_evento === "retirada_medicamento" &&
                    laudoVencido(novaDataFim);

                  setNovoEvento({
                    ...novoEvento,
                    data_fim_vigencia: novaDataFim,
                    data_evento: deveLimparData ? "" : novoEvento.data_evento,
                  });
                }}
              />
            </label>
          </div>

          <label className="full-width-label">
            Observações
            <textarea
              value={novoEvento.observacoes}
              onChange={(e) =>
                setNovoEvento({ ...novoEvento, observacoes: e.target.value })
              }
              placeholder="Observações sobre retirada, disponibilidade, preferência do paciente ou necessidade de reagendamento."
            />
          </label>

          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={novoEvento.notificar_whatsapp}
              onChange={(e) =>
                setNovoEvento({
                  ...novoEvento,
                  notificar_whatsapp: e.target.checked,
                })
              }
            />
            Gerar notificações via WhatsApp
          </label>

          <div className="action-buttons">
            <button className="primary-button" onClick={salvarNovoEvento}>
              Salvar
            </button>

            <button className="secondary-button" onClick={limparFormularioEvento}>
              Cancelar
            </button>
          </div>
        </div>
      )}

      <div className="form-card">
        <h3>Filtros</h3>

        <div className="filters-row">
          <label>
            Categoria
            <select
              value={filtroServico}
              onChange={(e) => setFiltroServico(e.target.value)}
            >
              <option value="todos">Todos</option>
              <option value="consultorio">Consultório</option>
              <option value="intervencao">Intervenções</option>
              <option value="dispensacao">Dispensação</option>
              <option value="renovacao_laudo">Renovação de laudo</option>
            </select>
          </label>

          <label>
            Status
            <select
              value={filtroStatus}
              onChange={(e) => setFiltroStatus(e.target.value)}
            >
              <option value="ativos">Ativos / passíveis de alteração</option>
              <option value="todos">Todos</option>
              <option value="agendado">Agendado</option>
              <option value="notificado">Notificado</option>
              <option value="retirada_prevista">Retirada prevista</option>
              <option value="realizado">Realizado</option>
              <option value="faltou">Faltou</option>
              <option value="reagendado">Reagendado</option>
              <option value="cancelado">Cancelado</option>
              <option value="renovacao_recomendada">Renovação recomendada</option>
              <option value="renovacao_urgente">Renovação urgente</option>
              <option value="risco_interrupcao_tratamento">Risco de interrupção</option>
            </select>
          </label>

          <div className="action-buttons">
            <button
              className={periodoAgenda === "7" ? "primary-button" : "secondary-button"}
              onClick={() => setPeriodoAgenda("7")}
            >
              7 dias
            </button>

            <button
              className={periodoAgenda === "30" ? "primary-button" : "secondary-button"}
              onClick={() => setPeriodoAgenda("30")}
            >
              30 dias
            </button>

            <button
              className={periodoAgenda === "90" ? "primary-button" : "secondary-button"}
              onClick={() => setPeriodoAgenda("90")}
            >
              90 dias
            </button>

            <button
              className={periodoAgenda === "todos" ? "primary-button" : "secondary-button"}
              onClick={() => setPeriodoAgenda("todos")}
            >
              Todos
            </button>

            {filtroAlerta && (
              <button
                className="secondary-button"
                onClick={() => setFiltroAlerta("")}
              >
                Limpar filtro de alerta
              </button>
            )}
          </div>
        </div>
      </div>

      {reagendamento && (
        <div className="form-card">
          <div className="section-header">
            <div>
              <h3>Reagendar compromisso</h3>
              <p className="muted">Paciente: {reagendamento.evento.paciente_nome}</p>
            </div>
          </div>
          <div className="filters-row">
            <label>
              Nova data
              <input
                type="date"
                value={reagendamento.nova_data}
                onChange={(e) => setReagendamento({ ...reagendamento, nova_data: e.target.value })}
              />
            </label>
            <label>
              Tipo de motivo
              <select
                value={reagendamento.tipo_motivo}
                onChange={(e) => setReagendamento({ ...reagendamento, tipo_motivo: e.target.value })}
              >
                <option value="paciente">Paciente</option>
                <option value="equipe">Equipe</option>
                <option value="estoque">Estoque</option>
                <option value="sistema">Sistema</option>
                <option value="outro">Outro</option>
              </select>
            </label>
            <label>
              Motivo
              <input
                value={reagendamento.motivo}
                onChange={(e) => setReagendamento({ ...reagendamento, motivo: e.target.value })}
                placeholder="Motivo do reagendamento"
              />
            </label>
          </div>
          <label className="full-width-label">
            Observações
            <textarea
              value={reagendamento.observacoes}
              onChange={(e) => setReagendamento({ ...reagendamento, observacoes: e.target.value })}
              placeholder="Observações complementares"
            />
          </label>
          <div className="action-buttons">
            <button className="primary-button" onClick={salvarReagendamento}>Salvar reagendamento</button>
            <button className="secondary-button" onClick={() => setReagendamento(null)}>Cancelar</button>
          </div>
        </div>
      )}

      {historicoAgenda && (
        <div className="form-card">
          <div className="section-header">
            <div>
              <h3>Histórico do agendamento</h3>
              <p className="muted">Paciente: {historicoAgenda.evento.paciente_nome}</p>
            </div>
            <button className="secondary-button" onClick={() => setHistoricoAgenda(null)}>Fechar</button>
          </div>
          {historicoAgenda.historico.length === 0 ? (
            <p className="muted">Nenhuma alteração registrada.</p>
          ) : (
            <div className="table-wrapper">
              <table className="agenda-table">
                <thead>
                  <tr><th>Data</th><th>Ação</th><th>Original</th><th>Nova</th><th>Motivo</th><th>Usuário</th></tr>
                </thead>
                <tbody>
                  {historicoAgenda.historico.map((item) => (
                    <tr key={item.id}>
                      <td>{item.criado_em ? new Date(item.criado_em).toLocaleString("pt-BR") : "-"}</td>
                      <td>{item.acao}</td>
                      <td>{item.data_original || "-"}</td>
                      <td>{item.nova_data || "-"}</td>
                      <td>{item.motivo || "-"}</td>
                      <td>{item.usuario || "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      <div className="form-card">
        <h3>Compromissos</h3>

        {loading ? (
          <p className="muted">Carregando agenda...</p>
        ) : eventosFiltrados.length === 0 ? (
          <p className="muted">Nenhum compromisso encontrado.</p>
        ) : (
          <div className="table-wrapper">
            <table className="agenda-table">
              <thead>
                <tr>
                  <th>Data</th>
                  <th>Paciente</th>
                  <th>Serviço</th>
                  <th>Evento</th>
                  <th>Medicamento</th>
                  <th>Vigência / LME</th>
                  <th>Status</th>
                  <th>Telefone</th>
                  <th>Ações</th>
                </tr>
              </thead>

              <tbody>
                {eventosFiltrados.map((evento) => (
                  <tr key={evento.id} className={classeLinhaAgenda(evento.status)}>
                    <td>
                      {evento.data_evento
                        ? new Date(evento.data_evento + "T00:00:00").toLocaleDateString("pt-BR")
                        : "-"}
                    </td>

                    <td>{evento.paciente_nome}</td>
                    <td>{evento.servico_origem}</td>
                    <td>{evento.tipo_evento}</td>
                    <td>{evento.medicamento || "-"}</td>
                    <td>
                      {evento.data_fim_vigencia || "-"}
                      {evento.situacao_laudo ? <small className="muted block">{evento.situacao_laudo}</small> : null}
                    </td>

                    <td>
                      <span className={`timeline-tag ${evento.status}`}>
                        {evento.status}
                      </span>
                    </td>

                    <td>{evento.telefone || "-"}</td>

                    <td>
                      <div className="action-buttons">
                        <button
                          className="secondary-button"
                          onClick={() => atualizarStatus(evento, "realizado")}
                        >
                          Realizado
                        </button>

                        <button
                          className="secondary-button"
                          onClick={() => abrirReagendamento(evento)}
                        >
                          Reagendar
                        </button>

                        <button
                          className="secondary-button"
                          onClick={() => atualizarStatus(evento, "faltou")}
                        >
                          Faltou
                        </button>

                        <button
                          className="secondary-button"
                          onClick={() => atualizarStatus(evento, "cancelado")}
                        >
                          Cancelar
                        </button>

                        <button
                          className="secondary-button"
                          onClick={() => carregarHistoricoAgenda(evento)}
                        >
                          Histórico
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
