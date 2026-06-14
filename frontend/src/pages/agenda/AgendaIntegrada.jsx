import { useEffect, useMemo, useState } from "react";
import { api } from "../../api/api";
import "./AgendaIntegrada.css";
import CentralNotificacoes from "./CentralNotificacoes";

export default function AgendaIntegrada() {
  const [eventos, setEventos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filtroServico, setFiltroServico] = useState("todos");
  const [filtroStatus, setFiltroStatus] = useState("todos");
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

  const [novoEvento, setNovoEvento] = useState({
    paciente_id: null,
    paciente_nome: "",
    telefone: "",
    servico_origem: "dispensacao",
    tipo_evento: "retirada_medicamento",
    medicamento: "",
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

  const eventosFiltrados = useMemo(() => {
    return eventos.filter((evento) => {
      const servicoOk =
        filtroServico === "todos" || evento.servico_origem === filtroServico;

      const statusOk =
        filtroStatus === "todos" || evento.status === filtroStatus;

      if (!servicoOk || !statusOk) {
        return false;
      }

      if (filtroAlerta === "dispensacoes_amanha") {
        const amanha = new Date();
        amanha.setDate(amanha.getDate() + 1);

        const dataAmanha = amanha.toISOString().split("T")[0];

        return (
          evento.servico_origem === "dispensacao" &&
          evento.status === "agendado" &&
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
          evento.servico_origem === "dispensacao" &&
          ["agendado", "notificado", "reagendado"].includes(evento.status) &&
          dataEvento &&
          dataEvento < hojeLocal
        );
      }

      if (filtroAlerta) {
        return evento.status === filtroAlerta;
      }

      return true;
    });
  }, [eventos, filtroServico, filtroStatus, filtroAlerta]);

  const hoje = new Date().toISOString().slice(0, 10);

  const resumoOperacional = useMemo(() => {
    const proximos7 = eventos.filter((evento) => {
      if (!evento.data_evento) return false;

      const dataEvento = new Date(`${evento.data_evento}T00:00:00`);
      const dataHoje = new Date(`${hoje}T00:00:00`);
      const diff = (dataEvento - dataHoje) / (1000 * 60 * 60 * 24);

      return diff >= 0 && diff <= 7;
    });

    return {
      hoje: eventos.filter((e) => e.data_evento === hoje).length,
      proximos7: proximos7.length,
      pendentes: eventos.filter((e) => e.status === "agendado").length,
      atrasados: eventos.filter(
        (e) => e.data_evento < hoje && e.status === "agendado"
      ).length,
      realizados: eventos.filter((e) => e.status === "realizado").length,
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
      paciente_nome: "",
      telefone: "",
      servico_origem: "dispensacao",
      tipo_evento: "retirada_medicamento",
      medicamento: "",
      data_evento: "",
      data_inicio_vigencia: "",
      data_fim_vigencia: "",
      observacoes: "",
      notificar_whatsapp: true,
    });

    setBuscaPaciente("");
    setPacientesEncontrados([]);
    setCapacidadeDia(null);
    setSugestoesDatas([]);
    setMostrarFormulario(false);
  }

  async function salvarNovoEvento() {
    if (!novoEvento.paciente_nome.trim()) {
      alert("Informe o nome do paciente.");
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

      <div className="cards-grid five">
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
              </select>
            </label>

            <label>
              Tipo de evento
              <select
                value={novoEvento.tipo_evento}
                onChange={(e) =>
                  setNovoEvento({ ...novoEvento, tipo_evento: e.target.value })
                }
              >
                <option value="retorno_plano_cuidado">Retorno plano de cuidado</option>
                <option value="retorno_intervencao">Retorno intervenção</option>
                <option value="retirada_medicamento">Retirada de medicamento</option>
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
              Data prevista
              <input
                type="date"
                value={novoEvento.data_evento}
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
                onChange={(e) =>
                  setNovoEvento({
                    ...novoEvento,
                    data_fim_vigencia: e.target.value,
                  })
                }
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
            Serviço
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
              <option value="todos">Todos</option>
              <option value="agendado">Agendado</option>
              <option value="notificado">Notificado</option>
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
