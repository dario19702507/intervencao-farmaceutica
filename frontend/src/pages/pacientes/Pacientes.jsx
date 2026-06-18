import { useState } from "react";
import { api } from "../../api/api";

export default function Pacientes() {
  const [pacientes, setPacientes] = useState([]);
  const [termo, setTermo] = useState("");
  const [loading, setLoading] = useState(false);
  const [buscaRealizada, setBuscaRealizada] = useState(false);
  const [mensagemBusca, setMensagemBusca] = useState("Digite ao menos 3 caracteres para buscar um paciente.");

  const [historico, setHistorico] = useState(null);
  const [pacienteSelecionado, setPacienteSelecionado] = useState(null);
  const [loadingHistorico, setLoadingHistorico] = useState(false);

  const [pacienteEditando, setPacienteEditando] = useState(null);
  const [formPaciente, setFormPaciente] = useState({});

  async function carregarPacientes(busca = termo) {
    const termoBusca = (busca || "").trim();

    if (termoBusca.length < 3) {
      setPacientes([]);
      setBuscaRealizada(false);
      setMensagemBusca("Digite ao menos 3 caracteres para buscar por nome, CPF, CNS ou telefone.");
      return;
    }

    try {
      setLoading(true);
      setBuscaRealizada(true);
      setMensagemBusca("");

      const response = await api.get("/consultorio/pacientes", {
        params: {
          termo: termoBusca,
          limit: 30,
        },
      });

      const lista = response.data.pacientes || [];
      setPacientes(lista);

      if (lista.length === 0) {
        setMensagemBusca("Nenhum paciente encontrado para o termo informado.");
      } else if ((response.data.total || lista.length) > lista.length) {
        setMensagemBusca(`Exibindo ${lista.length} pacientes. Refine a busca para resultados mais específicos.`);
      } else {
        setMensagemBusca(`${lista.length} paciente(s) encontrado(s).`);
      }
    } catch (error) {
      console.error(error);
      setMensagemBusca("Erro ao buscar pacientes.");
      alert("Erro ao carregar pacientes.");
    } finally {
      setLoading(false);
    }
  }

  async function abrirHistorico(paciente) {
    try {
      setLoadingHistorico(true);
      setPacienteSelecionado(paciente);

      const response = await api.get(
        `/consultorio/pacientes/${paciente.id}/historico`
      );

      setHistorico(response.data);
    } catch (error) {
      console.error(error);
      alert("Erro ao carregar histórico do paciente.");
    } finally {
      setLoadingHistorico(false);
    }
  }

  function abrirEdicaoPaciente(paciente) {
    setPacienteEditando(paciente);
    setFormPaciente({
      nome: paciente.nome || "",
      cpf: paciente.cpf || "",
      cns: paciente.cns || "",
      telefone: paciente.telefone || "",
      telefone_alternativo: paciente.telefone_alternativo || "",
      municipio: paciente.municipio || "",
      logradouro: paciente.logradouro || "",
      numero_residencia: paciente.numero_residencia || "",
      complemento_residencia: paciente.complemento_residencia || "",
      ativo: paciente.ativo ?? true,
    });
  }

  async function salvarEdicaoPaciente() {
    if (!pacienteEditando) return;

    try {
      await api.put(
        `/consultorio/pacientes/${pacienteEditando.id}`,
        formPaciente
      );

      alert("Paciente atualizado com sucesso.");

      const pacienteAtualizado = {
        ...pacienteEditando,
        ...formPaciente,
      };

      setPacienteEditando(null);
      setFormPaciente({});

      if ((termo || "").trim().length >= 3) {
        await carregarPacientes(termo);
      }

      if (pacienteSelecionado?.id === pacienteAtualizado.id) {
        await abrirHistorico(pacienteAtualizado);
      }
    } catch (error) {
      console.error(error);
      alert("Erro ao atualizar paciente.");
    }
  }

  function atualizarCampo(campo, valor) {
    setFormPaciente((atual) => ({
      ...atual,
      [campo]: valor,
    }));
  }

  return (
    <div className="agenda-container">
      <div className="page-header">
        <div>
          <h2>Cadastro Mestre de Pacientes</h2>
          <p>Pacientes vinculados aos módulos da Farmácia Escola.</p>
        </div>
      </div>

      <div className="form-card">
        <label>
          Pesquisar paciente
          <input
            type="text"
            value={termo}
            placeholder="Nome, CPF, CNS ou telefone"
            onChange={(e) => {
              const valor = e.target.value;
              setTermo(valor);
              if (valor.trim().length < 3) {
                setPacientes([]);
                setBuscaRealizada(false);
                setMensagemBusca("Digite ao menos 3 caracteres para buscar por nome, CPF, CNS ou telefone.");
              }
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                carregarPacientes(termo);
              }
            }}
          />
        </label>

        <button
          className="primary-button"
          disabled={loading || termo.trim().length < 3}
          onClick={() => carregarPacientes(termo)}
        >
          {loading ? "Buscando..." : "Pesquisar"}
        </button>
      </div>

      <div className="form-card">
        <h3>Resultado da busca</h3>
        {mensagemBusca && <p className="muted-text">{mensagemBusca}</p>}

        {loading ? (
          <p>Carregando...</p>
        ) : pacientes.length > 0 ? (
          <table className="agenda-table">
            <thead>
              <tr>
                <th>Nome</th>
                <th>Telefone</th>
                <th>CPF</th>
                <th>Origem</th>
                <th>Status</th>
                <th>Ações</th>
              </tr>
            </thead>

            <tbody>
              {pacientes.map((p) => (
                <tr key={p.id}>
                  <td>{p.nome}</td>
                  <td>{p.telefone || "-"}</td>
                  <td>{p.cpf || "-"}</td>
                  <td>{p.origem || "-"}</td>
                  <td>{p.ativo ? "Ativo" : "Inativo"}</td>
                  <td>
                    <button
                      className="secondary-button"
                      onClick={() => abrirHistorico(p)}
                    >
                      Histórico
                    </button>

                    <button
                      className="secondary-button"
                      onClick={() => abrirEdicaoPaciente(p)}
                    >
                      Editar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : buscaRealizada ? (
          <p>Nenhum paciente localizado.</p>
        ) : (
          <p>Use o campo acima para localizar o paciente no cadastro mestre.</p>
        )}
      </div>

      {pacienteEditando && (
        <div className="form-card">
          <div className="page-header">
            <div>
              <h3>Editar paciente</h3>
              <p>{pacienteEditando.nome}</p>
            </div>

            <button
              className="secondary-button"
              onClick={() => {
                setPacienteEditando(null);
                setFormPaciente({});
              }}
            >
              Cancelar
            </button>
          </div>

          <div className="filters-row">
            <label>
              Nome
              <input
                type="text"
                value={formPaciente.nome || ""}
                onChange={(e) => atualizarCampo("nome", e.target.value)}
              />
            </label>

            <label>
              CPF
              <input
                type="text"
                value={formPaciente.cpf || ""}
                onChange={(e) => atualizarCampo("cpf", e.target.value)}
              />
            </label>

            <label>
              CNS
              <input
                type="text"
                value={formPaciente.cns || ""}
                onChange={(e) => atualizarCampo("cns", e.target.value)}
              />
            </label>

            <label>
              Telefone
              <input
                type="text"
                value={formPaciente.telefone || ""}
                onChange={(e) => atualizarCampo("telefone", e.target.value)}
              />
            </label>

            <label>
              Telefone alternativo
              <input
                type="text"
                value={formPaciente.telefone_alternativo || ""}
                onChange={(e) =>
                  atualizarCampo("telefone_alternativo", e.target.value)
                }
              />
            </label>

            <label>
              Município
              <input
                type="text"
                value={formPaciente.municipio || ""}
                onChange={(e) => atualizarCampo("municipio", e.target.value)}
              />
            </label>

            <label>
              Logradouro
              <input
                type="text"
                value={formPaciente.logradouro || ""}
                onChange={(e) => atualizarCampo("logradouro", e.target.value)}
              />
            </label>

            <label>
              Número
              <input
                type="text"
                value={formPaciente.numero_residencia || ""}
                onChange={(e) =>
                  atualizarCampo("numero_residencia", e.target.value)
                }
              />
            </label>

            <label>
              Complemento
              <input
                type="text"
                value={formPaciente.complemento_residencia || ""}
                onChange={(e) =>
                  atualizarCampo("complemento_residencia", e.target.value)
                }
              />
            </label>

            <label>
              Status
              <select
                value={formPaciente.ativo ? "ativo" : "inativo"}
                onChange={(e) =>
                  atualizarCampo("ativo", e.target.value === "ativo")
                }
              >
                <option value="ativo">Ativo</option>
                <option value="inativo">Inativo</option>
              </select>
            </label>
          </div>

          <div className="action-buttons">
            <button className="primary-button" onClick={salvarEdicaoPaciente}>
              Salvar alterações
            </button>
          </div>
        </div>
      )}

      {pacienteSelecionado && (
        <div className="form-card">
          <div className="page-header">
            <div>
              <h3>Histórico Unificado</h3>
              <p>{pacienteSelecionado.nome}</p>
            </div>

            <button
              className="secondary-button"
              onClick={() => {
                setPacienteSelecionado(null);
                setHistorico(null);
              }}
            >
              Fechar
            </button>
          </div>

          {loadingHistorico ? (
            <p>Carregando histórico...</p>
          ) : historico ? (
            <>
              <div className="dashboard-grid">
                <div className="summary-card">
                  <strong>Agenda</strong>
                  <div>{historico.resumo.total_eventos_agenda}</div>
                </div>

                <div className="summary-card">
                  <strong>Atendimentos rápidos</strong>
                  <div>{historico.resumo.total_cadastros_simplificados}</div>
                </div>

                <div className="summary-card">
                  <strong>Cadastros clínicos</strong>
                  <div>{historico.resumo.total_cadastros_clinicos}</div>
                </div>

                <div className="summary-card">
                  <strong>Notificações</strong>
                  <div>{historico.resumo.total_notificacoes}</div>
                  <small>
                    Pendentes: {historico.resumo.notificacoes_pendentes || 0} |
                    Enviadas: {historico.resumo.notificacoes_enviadas || 0} |
                    Erro: {historico.resumo.notificacoes_erro || 0}
                  </small>
                </div>
              </div>

              {historico.painel_paciente && (
              <>
                <h4>Painel do Paciente</h4>

                {historico.painel_paciente?.status_paciente && (
                  <div
                    className={`status-paciente-card status-${historico.painel_paciente.status_paciente.cor}`}
                  >
                    <strong>
                      {historico.painel_paciente.status_paciente.descricao}
                    </strong>
                  </div>
                )}

                <div className="summary-grid">

                  <div className="summary-card">
                    <strong>Última dispensação</strong>
                    <div>
                      {historico.painel_paciente.ultima_dispensacao?.data_evento
                        ? new Date(
                            historico.painel_paciente.ultima_dispensacao.data_evento +
                            "T00:00:00"
                          ).toLocaleDateString("pt-BR")
                        : "-"}
                    </div>
                  </div>

                  <div className="summary-card">
                    <strong>Próxima dispensação</strong>
                    <div>
                      {historico.painel_paciente.proxima_dispensacao?.data_evento
                        ? new Date(
                            historico.painel_paciente.proxima_dispensacao.data_evento +
                            "T00:00:00"
                          ).toLocaleDateString("pt-BR")
                        : "-"}
                    </div>
                  </div>

                  <div className="summary-card">
                    <strong>Vigência do laudo</strong>
                    <div>
                      {historico.painel_paciente.laudo_mais_recente?.data_fim_vigencia
                        ? new Date(
                            historico.painel_paciente.laudo_mais_recente.data_fim_vigencia +
                            "T00:00:00"
                          ).toLocaleDateString("pt-BR")
                        : "-"}
                    </div>
                  </div>

                  <div className="summary-card">
                    <strong>Última notificação</strong>
                    <div>
                      {historico.painel_paciente.ultima_notificacao?.tipo_notificacao || "-"}
                    </div>
                  </div>

                  <div className="summary-card">
                    <strong>Atendimentos rápidos</strong>
                    <div>
                      {historico.painel_paciente.total_atendimentos_rapidos}
                    </div>
                  </div>

                  <div className="summary-card">
                    <strong>Cadastros clínicos</strong>
                    <div>
                      {historico.painel_paciente.total_cadastros_clinicos}
                    </div>
                  </div>

                </div>
              </>
            )}

              <h4>Timeline unificada</h4>

              {historico.timeline?.length === 0 ? (
                <p>Nenhum evento na timeline.</p>
              ) : (
                <div className="timeline-list">
                  {historico.timeline.map((item, index) => (
                    <div key={index} className="timeline-item">
                      <div className="timeline-date">
                        {item.data
                          ? new Date(item.data + "T00:00:00").toLocaleDateString(
                              "pt-BR"
                            )
                          : "-"}
                      </div>

                      <div className="timeline-content">
                        <strong>
                          {item.origem} — {item.tipo}
                        </strong>

                        <p>{item.descricao || item.titulo || "-"}</p>

                        <span className="timeline-status">
                          {item.status || "-"}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <h4>Agenda</h4>
              {historico.agenda?.length === 0 ? (
                <p>Nenhum evento de agenda.</p>
              ) : (
                <table className="agenda-table">
                  <thead>
                    <tr>
                      <th>Data</th>
                      <th>Serviço</th>
                      <th>Tipo</th>
                      <th>Medicamento</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {historico.agenda.map((e) => (
                      <tr key={e.id}>
                        <td>
                          {e.data_evento
                            ? new Date(
                                e.data_evento + "T00:00:00"
                              ).toLocaleDateString("pt-BR")
                            : "-"}
                        </td>
                        <td>{e.servico_origem}</td>
                        <td>{e.tipo_evento}</td>
                        <td>{e.medicamento || "-"}</td>
                        <td>{e.status}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              <h4>Atendimento rápido</h4>
              {historico.pacientes_simplificados?.length === 0 ? (
                <p>Nenhum cadastro simplificado vinculado.</p>
              ) : (
                <table className="agenda-table">
                  <thead>
                    <tr>
                      <th>Nome</th>
                      <th>Telefone</th>
                      <th>Bairro</th>
                    </tr>
                  </thead>
                  <tbody>
                    {historico.pacientes_simplificados.map((p) => (
                      <tr key={p.id}>
                        <td>{p.nome}</td>
                        <td>{p.telefone || "-"}</td>
                        <td>{p.bairro || "-"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              <h4>Consultório clínico</h4>
              {historico.pacientes_clinicos?.length === 0 ? (
                <p>Nenhum cadastro clínico vinculado.</p>
              ) : (
                <table className="agenda-table">
                  <thead>
                    <tr>
                      <th>Nome</th>
                      <th>Telefone</th>
                      <th>CPF</th>
                      <th>CNS</th>
                    </tr>
                  </thead>
                  <tbody>
                    {historico.pacientes_clinicos.map((p) => (
                      <tr key={p.id}>
                        <td>{p.nome}</td>
                        <td>{p.telefone || "-"}</td>
                        <td>{p.cpf || "-"}</td>
                        <td>{p.cns || "-"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              <h4>Notificações</h4>
              {historico.notificacoes?.length === 0 ? (
                <p>Nenhuma notificação vinculada.</p>
              ) : (
                <table className="agenda-table">
                  <thead>
                    <tr>
                      <th>Tipo</th>
                      <th>Data programada</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {historico.notificacoes.map((n) => (
                      <tr key={n.id}>
                        <td>{n.tipo_notificacao}</td>
                        <td>
                          {n.data_programada
                            ? new Date(
                                n.data_programada + "T00:00:00"
                              ).toLocaleDateString("pt-BR")
                            : "-"}
                        </td>
                        <td>{n.status}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </>
          ) : (
            <p>Selecione um paciente para visualizar o histórico.</p>
          )}
        </div>
      )}
    </div>
  );
}
