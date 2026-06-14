import { useEffect, useState } from "react";
import { api } from "../../api/api";

export default function CentralOperacional() {
  const [dados, setDados] = useState(null);
  const [carregando, setCarregando] = useState(false);

  async function carregarPainel() {
    try {
      setCarregando(true);
      const resposta = await api.get(
        "/consultorio/dashboard-notificacoes/painel-operacional"
      );
      setDados(resposta.data);
    } catch (error) {
      console.error(error);
      alert("Erro ao carregar painel operacional.");
    } finally {
      setCarregando(false);
    }
  }

  useEffect(() => {
    carregarPainel();
  }, []);

  function renderLista(titulo, itens) {
    return (
      <div className="form-card">
        <h3>{titulo}</h3>

        {!itens || itens.length === 0 ? (
          <p>Nenhum registro encontrado.</p>
        ) : (
          <table className="agenda-table">
            <thead>
              <tr>
                <th>Prioridade</th>
                <th>Paciente</th>
                <th>Medicamento</th>
                <th>Data</th>
                <th>Status</th>
              </tr>
            </thead>

            <tbody>
              {itens.map((item) => (
                <tr key={item.id}>
                  <td>
                    {item.prioridade_visual?.icone}{" "}
                    {item.prioridade_visual?.rotulo}
                  </td>
                  <td>{item.paciente_nome || "-"}</td>
                  <td>{item.medicamento || "-"}</td>
                  <td>
                    {item.data_evento
                      ? new Date(item.data_evento + "T00:00:00")
                          .toLocaleDateString("pt-BR")
                      : "-"}
                  </td>
                  <td>{item.status || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    );
  }

  if (carregando && !dados) {
    return <p>Carregando painel operacional...</p>;
  }

  return (
    <div className="agenda-container">
      <div className="page-header">
        <div>
          <h2>Central Operacional da Farmácia Escola</h2>
          <p>Agenda, notificações e prioridades assistenciais</p>
        </div>

        <button className="primary-button" onClick={carregarPainel}>
          Atualizar
        </button>
      </div>

      {dados && (
        <>
          <div className="summary-grid">
            <div className="summary-card">
              <strong>Retiradas hoje</strong>
              <div>{dados.resumo?.retiradas_hoje || 0}</div>
            </div>

            <div className="summary-card">
              <strong>Retiradas amanhã</strong>
              <div>{dados.resumo?.retiradas_amanha || 0}</div>
            </div>

            <div className="summary-card">
              <strong>Renovações em 30 dias</strong>
              <div>{dados.resumo?.renovacoes_30_dias || 0}</div>
            </div>

            <div className="summary-card">
              <strong>Risco de interrupção</strong>
              <div>{dados.resumo?.risco_interrupcao || 0}</div>
            </div>

            <div className="summary-card">
              <strong>Notificações pendentes</strong>
              <div>{dados.resumo?.notificacoes_pendentes || 0}</div>
            </div>
          </div>

          {renderLista("Retiradas de hoje", dados.retiradas_hoje)}
          {renderLista("Retiradas de amanhã", dados.retiradas_amanha)}
          {renderLista("Renovações nos próximos 30 dias", dados.renovacoes_30_dias)}
          {renderLista("Risco de interrupção do tratamento", dados.risco_interrupcao)}
        </>
      )}
    </div>
  );
}