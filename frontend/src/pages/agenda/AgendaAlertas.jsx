import { useEffect, useMemo, useState } from "react";
import { api } from "../../api/api";
import { AlertTriangle, CalendarDays, CheckCircle2, RefreshCw } from "lucide-react";

const PRIORIDADE_PESO = {
  critico: 0,
  critica: 0,
  alta: 1,
  urgente: 1,
  atencao: 2,
  média: 2,
  media: 2,
  informativo: 3,
  baixa: 4,
};

function normalizarPrioridade(item) {
  return String(item?.prioridade_ceaf || item?.prioridade || "informativo").toLowerCase();
}

function prioridadePeso(item) {
  const chave = normalizarPrioridade(item);
  return PRIORIDADE_PESO[chave] ?? 9;
}

function badgePrioridade(item) {
  const prioridade = normalizarPrioridade(item);
  if (["critico", "critica"].includes(prioridade)) return "danger";
  if (["alta", "urgente"].includes(prioridade)) return "alta";
  if (["atencao", "média", "media"].includes(prioridade)) return "warning";
  return "info";
}

function tituloAlerta(item) {
  return item.titulo || item.tipo_alerta || item.tipo || "Alerta";
}

function mensagemAlerta(item) {
  return item.mensagem || item.descricao || item.motivo || "Pendência identificada para avaliação da equipe.";
}

export default function AgendaAlertas() {
  const [retornos, setRetornos] = useState([]);
  const [alertas, setAlertas] = useState([]);
  const [alertasCeaf, setAlertasCeaf] = useState([]);
  const [resumo, setResumo] = useState(null);
  const [resumoCeaf, setResumoCeaf] = useState(null);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState("");

  useEffect(() => {
    carregarDados();
  }, []);

  async function carregarDados() {
    try {
      setLoading(true);
      setErro("");

      const [agendaResponse, alertasResponse, alertasCeafResponse] = await Promise.all([
        api.get("/consultorio/agenda-retornos", {
          params: { somente_pendentes: false },
        }),
        api.get("/consultorio/alertas-pendentes"),
        api.get("/consultorio/agenda/alertas-ceaf", {
          params: { limite: 120 },
        }),
      ]);

      setRetornos(agendaResponse.data.retornos || []);
      setAlertas(alertasResponse.data.alertas || []);
      setResumo(alertasResponse.data.resumo || null);
      setAlertasCeaf(alertasCeafResponse.data.alertas || []);
      setResumoCeaf(alertasCeafResponse.data.resumo || null);
    } catch (error) {
      console.error("Erro ao carregar agenda e alertas:", error);
      setErro("Não foi possível carregar todos os alertas da agenda. Verifique o backend e tente novamente.");
    } finally {
      setLoading(false);
    }
  }

  const alertasPriorizados = useMemo(() => {
    const alertasClinicos = (alertas || []).map((item) => ({
      ...item,
      origem_alerta: item.origem_alerta || "Consultório",
    }));

    const alertasCeafNormalizados = (alertasCeaf || []).map((item) => ({
      ...item,
      origem_alerta: "CEAF",
      prioridade: item.prioridade_ceaf || item.prioridade,
    }));

    return [...alertasCeafNormalizados, ...alertasClinicos]
      .sort((a, b) => prioridadePeso(a) - prioridadePeso(b))
      .slice(0, 120);
  }, [alertas, alertasCeaf]);

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
      <div className="section-header">
        <div>
          <h2>Agenda e Alertas</h2>
          <p className="muted">
            Retornos programados, alertas clínicos e pendências CEAF priorizadas para ação da equipe.
          </p>
        </div>
        <button className="secondary-button" onClick={carregarDados}>
          <RefreshCw size={16} /> Atualizar alertas
        </button>
      </div>

      {erro && <div className="clinical-summary danger">{erro}</div>}

      <div className="cards-grid six">
        <div className="metric-card">
          <span>Retornos registrados</span>
          <strong>{retornos.length}</strong>
          <p>Inclui retornos pendentes e concluídos.</p>
        </div>

        <div className="metric-card">
          <span>Alertas pendentes</span>
          <strong>{alertasPriorizados.length}</strong>
          <p>Clínicos e CEAF em ordem de prioridade.</p>
        </div>

        <div className="metric-card danger">
          <span>CEAF críticos</span>
          <strong>{resumoCeaf?.critico || resumoCeaf?.criticos || 0}</strong>
          <p>LME vencida ou risco assistencial.</p>
        </div>

        <div className="metric-card warning">
          <span>CEAF urgentes</span>
          <strong>{resumoCeaf?.urgente || resumoCeaf?.urgentes || 0}</strong>
          <p>Demandam contato ou agendamento breve.</p>
        </div>

        <div className="metric-card warning">
          <span>Renovações</span>
          <strong>{resumoCeaf?.renovacao_lme || resumoCeaf?.renovacoes || 0}</strong>
          <p>Vigência próxima ou vencida.</p>
        </div>

        <div className="metric-card">
          <span>Prioridade alta</span>
          <strong>{resumo?.alta || 0}</strong>
          <p>Casos clínicos mais sensíveis.</p>
        </div>
      </div>

      <h3 className="section-title">Alertas pendentes priorizados</h3>

      {alertasPriorizados.length === 0 ? (
        <p className="muted">Nenhum alerta pendente.</p>
      ) : (
        <div className="alert-list agenda-alertas-priorizados">
          {alertasPriorizados.map((item, index) => (
            <div
              className={`alert-card alert-${badgePrioridade(item)}`}
              key={`${item.origem_alerta || item.tipo_alerta}-${item.id || item.paciente_ceaf_id || index}`}
            >
              <div className="alert-icon">
                <AlertTriangle size={20} />
              </div>

              <div className="alert-content">
                <div className="agenda-top">
                  <strong>{item.paciente_nome || item.nome || "Paciente não informado"}</strong>
                  <div className="timeline-tags compact-tags">
                    <span>{item.origem_alerta || item.origem || "Agenda"}</span>
                    <span className={`badge badge-${badgePrioridade(item)}`}>
                      {item.prioridade_ceaf || item.prioridade || "informativo"}
                    </span>
                  </div>
                </div>

                <p><strong>{tituloAlerta(item)}:</strong> {mensagemAlerta(item)}</p>

                <div className="timeline-tags compact-tags">
                  {item.medicamento && <span>{item.medicamento}</span>}
                  {item.data_fim_vigencia && <span>Vigência: {formatarDataCurta(item.data_fim_vigencia)}</span>}
                  {item.telefone && <span>Tel.: {item.telefone}</span>}
                  {item.tipo_alerta && <span>{item.tipo_alerta}</span>}
                </div>

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
                  Retorno sugerido: <strong>{formatarDataCurta(item.data_retorno_sugerida)}</strong>
                </p>

                <p className="muted">
                  {item.plano_acompanhamento || "Sem plano informado."}
                </p>
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
    return new Date(valor + (String(valor).includes("T") ? "" : "T00:00:00")).toLocaleDateString("pt-BR");
  } catch {
    return valor;
  }
}
