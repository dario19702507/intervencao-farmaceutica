import { useEffect, useState } from "react";
import { api } from "../../api/api";
import { AlertTriangle, CalendarDays, CheckCircle2 } from "lucide-react";

export default function AgendaAlertas() {
  const [retornos, setRetornos] = useState([]);
  const [alertas, setAlertas] = useState([]);
  const [resumo, setResumo] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    carregarDados();
  }, []);

  async function carregarDados() {
    try {
      setLoading(true);

      const [agendaResponse, alertasResponse] = await Promise.all([
        api.get("/consultorio/agenda-retornos", {
          params: { somente_pendentes: false },
        }),
        api.get("/consultorio/alertas-pendentes"),
      ]);

      setRetornos(agendaResponse.data.retornos || []);
      setAlertas(alertasResponse.data.alertas || []);
      setResumo(alertasResponse.data.resumo || null);
    } catch (error) {
      console.error("Erro ao carregar agenda e alertas:", error);
    } finally {
      setLoading(false);
    }
  }
  async function converterParaClinico(alerta) {
  try {
    const pacienteSimplificadoId =
      alerta.paciente_simplificado_id || alerta.paciente_id;

    if (!pacienteSimplificadoId) {
      alert("Paciente simplificado não localizado neste alerta.");
      return;
    }

    const response = await api.post(
      `/consultorio/converter-para-clinico/${pacienteSimplificadoId}`,
      {
        aceite_verbal: true,
        motivo_conversao:
          "Paciente convertido para acompanhamento clínico após alerta clínico.",
        endereco: "",
        cpf: "",
        cns: "",
        nome_mae: "",
        observacoes_prontuario:
          "Prontuário aberto a partir de alerta clínico em serviços rápidos.",
      }
    );

    console.log("PACIENTE CLÍNICO:", response.data);

    alert("Paciente convertido para acompanhamento clínico.");

    carregarDados();
  } catch (error) {
    console.error("Erro ao converter paciente:", error.response?.data || error);

    alert(
      `Erro ao converter paciente: ${
        error.response?.data?.detail || "verifique o console"
      }`
    );
  }
}
  if (loading) {
    return (
      <div>
        <h2>Agenda e Alertas</h2>
        <p className="muted">Carregando informações...</p>
      </div>
    );
  }

  return (
    <div>
      <h2>Agenda e Alertas</h2>
      <p className="muted">
        Retornos programados, alertas clínicos e pendências do consultório.
      </p>

      <div className="cards-grid three">
        <div className="metric-card">
          <span>Retornos registrados</span>
          <strong>{retornos.length}</strong>
          <p>Inclui retornos pendentes e concluídos.</p>
        </div>

        <div className="metric-card">
          <span>Alertas pendentes</span>
          <strong>{resumo?.total_alertas || 0}</strong>
          <p>Eventos que demandam atenção.</p>
        </div>

        <div className="metric-card">
          <span>Prioridade alta</span>
          <strong>{resumo?.alta || 0}</strong>
          <p>Casos mais sensíveis.</p>
        </div>
      </div>

      <h3 className="section-title">Agenda de retornos</h3>

      {retornos.length === 0 ? (
        <p className="muted">Nenhum retorno registrado.</p>
      ) : (
        <div className="agenda-list">
          {retornos.map((item) => (
            <div className="agenda-card" key={item.evolucao_id}>
              <div className="agenda-icon">
                {item.retorno_concluido ? (
                  <CheckCircle2 size={20} />
                ) : (
                  <CalendarDays size={20} />
                )}
              </div>

              <div className="agenda-content">
                <div className="agenda-top">
                  <strong>{item.paciente_nome}</strong>
                  <span
                    className={
                      item.retorno_concluido
                        ? "badge badge-success"
                        : "badge badge-warning"
                    }
                  >
                    {item.retorno_concluido ? "Concluído" : "Pendente"}
                  </span>
                </div>

                <p>
                  Retorno sugerido:{" "}
                  <strong>{formatarDataCurta(item.data_retorno_sugerida)}</strong>
                </p>

                <p className="muted">
                  {item.plano_acompanhamento || "Sem plano informado."}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}

      <h3 className="section-title">Alertas pendentes</h3>

      {alertas.length === 0 ? (
        <p className="muted">Nenhum alerta pendente.</p>
      ) : (
        <div className="alert-list">
          {alertas.map((item, index) => (
            <div
              className={`alert-card alert-${item.prioridade}`}
              key={`${item.tipo_alerta}-${index}`}
            >
              <div className="alert-icon">
                <AlertTriangle size={20} />
              </div>

              <div className="alert-content">
                <div className="agenda-top">
                  <strong>{item.paciente_nome || "Paciente não informado"}</strong>
                  <span className={`badge badge-${item.prioridade}`}>
                    {item.prioridade}
                  </span>
                </div>

                <p>{item.mensagem}</p>

                {item.riscos && item.riscos.length > 0 && (
                  <div className="timeline-tags">
                    {item.riscos.map((risco) => (
                      <span key={risco}>{risco}</span>
                    ))}
                  </div>
                )}
                {item.tipo_alerta === "risco_nao_convertido" && (
                  <button
                    className="mini-action-button"
                    onClick={() => converterParaClinico(item)}
                  >
                    Converter para clínico
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function formatarDataCurta(valor) {
  if (!valor) return "Sem data";

  try {
    return new Date(valor).toLocaleDateString("pt-BR");
  } catch {
    return valor;
  }
}