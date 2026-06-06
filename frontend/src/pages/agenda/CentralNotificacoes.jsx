import { useEffect, useState } from "react";
import { api } from "../../api";

function normalizarStatus(valor) {
  return (valor || "").toString().trim().toLowerCase();
}

export default function CentralNotificacoes() {
  const [notificacoes, setNotificacoes] = useState([]);
  const [status, setStatus] = useState("pendente");
  const [tipo, setTipo] = useState("todos");
  const [loading, setLoading] = useState(false);

  async function carregarNotificacoes() {
    try {
      setLoading(true);

      const params = {};

      if (status !== "todos") params.status = status;
      if (tipo !== "todos") params.tipo_notificacao = tipo;

      const response = await api.get(
        "/consultorio/agenda/notificacoes/listar",
        { params }
      );

      setNotificacoes(response.data.notificacoes || []);
    } catch (error) {
      console.error("Erro ao carregar notificações:", error);
      alert("Erro ao carregar notificações.");
    } finally {
      setLoading(false);
    }
  }

  async function gerarNotificacoes() {
    try {
      const response = await api.post(
        "/consultorio/agenda/notificacoes/gerar"
      );

      alert(
        `Geração concluída. Criadas: ${response.data.notificacoes_criadas}. Ignoradas: ${response.data.notificacoes_ignoradas}.`
      );

      await carregarNotificacoes();
    } catch (error) {
      console.error("Erro ao gerar notificações:", error);
      alert("Erro ao gerar notificações.");
    }
  }

  async function atualizarStatusNotificacao(id, novoStatus) {
    try {
      await api.put(`/consultorio/agenda/notificacoes/${id}/status`, {
        status: novoStatus,
      });

      await carregarNotificacoes();
    } catch (error) {
      console.error("Erro ao atualizar notificação:", error);
      alert("Erro ao atualizar notificação.");
    }
  }

  useEffect(() => {
    carregarNotificacoes();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, tipo]);

  return (
    <div className="form-card">
      <div className="section-header">
        <div>
          <h2>Central de Notificações</h2>
          <p className="muted">
            Acompanhe notificações pendentes, enviadas, com erro ou canceladas.
          </p>
        </div>

        <div className="action-buttons">
          <button className="primary-button" onClick={gerarNotificacoes}>
            Gerar notificações
          </button>

          <button className="secondary-button" onClick={carregarNotificacoes}>
            Atualizar
          </button>
        </div>
      </div>

      <div className="filters-row">
        <label>
          Status
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="pendente">Pendentes</option>
            <option value="enviada">Enviadas</option>
            <option value="erro">Erro</option>
            <option value="cancelada">Canceladas</option>
            <option value="todos">Todas</option>
          </select>
        </label>

        <label>
          Tipo
          <select value={tipo} onChange={(e) => setTipo(e.target.value)}>
            <option value="todos">Todos</option>
            <option value="dispensacao_amanha">Dispensação amanhã</option>
            <option value="renovacao_recomendada">Renovação recomendada</option>
            <option value="renovacao_urgente">Renovação urgente</option>
            <option value="risco_interrupcao_tratamento">
              Risco de interrupção
            </option>
          </select>
        </label>
      </div>

      <h3>Notificações ({notificacoes.length})</h3>

      {loading ? (
        <p className="muted">Carregando...</p>
      ) : notificacoes.length === 0 ? (
        <p className="muted">Nenhuma notificação encontrada.</p>
      ) : (
        <div className="table-wrapper">
          <table className="agenda-table">
            <thead>
              <tr>
                <th>Tipo</th>
                <th>Paciente</th>
                <th>Telefone</th>
                <th>Data programada</th>
                <th>Status</th>
                <th>Mensagem</th>
                <th>Ações</th>
              </tr>
            </thead>

            <tbody>
              {notificacoes.map((n) => {
                const statusAtual = normalizarStatus(n.status);

                return (
                  <tr key={n.id}>
                    <td>{n.tipo_notificacao}</td>
                    <td>{n.paciente_nome || "-"}</td>
                    <td>{n.telefone || "-"}</td>
                    <td>
                      {n.data_programada
                        ? new Date(
                            n.data_programada + "T00:00:00"
                          ).toLocaleDateString("pt-BR")
                        : "-"}
                    </td>
                    <td>{n.status || "-"}</td>
                    <td className="mensagem-notificacao">{n.mensagem}</td>
                    <td>
                      <div className="action-buttons">
                        {statusAtual === "pendente" && (
                          <>
                            <button
                              className="secondary-button"
                              onClick={() =>
                                atualizarStatusNotificacao(n.id, "enviada")
                              }
                            >
                              ✓ Enviada
                            </button>

                            <button
                              className="secondary-button"
                              onClick={() =>
                                atualizarStatusNotificacao(n.id, "erro")
                              }
                            >
                              ⚠ Erro
                            </button>

                            <button
                              className="secondary-button"
                              onClick={() =>
                                atualizarStatusNotificacao(n.id, "cancelada")
                              }
                            >
                              ✖ Cancelar
                            </button>
                          </>
                        )}

                        {statusAtual === "erro" && (
                          <button
                            className="secondary-button"
                            onClick={() =>
                              atualizarStatusNotificacao(n.id, "pendente")
                            }
                          >
                            ↻ Reenviar
                          </button>
                        )}

                        {statusAtual === "cancelada" && (
                          <button
                            className="secondary-button"
                            onClick={() =>
                              atualizarStatusNotificacao(n.id, "pendente")
                            }
                          >
                            Reativar
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
