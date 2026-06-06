import { useEffect, useState } from "react";
import { api } from "../../api/api";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";

export default function Dashboard({ setActivePage }) {
  const [servicos, setServicos] = useState(null);
  const [desfechos, setDesfechos] = useState(null);
  const [alertas, setAlertas] = useState(null);
  const [loading, setLoading] = useState(true);
  const [dashboardResolucao, setDashboardResolucao] = useState(null);
  const [carregandoResolucao, setCarregandoResolucao] = useState(false);

  useEffect(() => {
    carregarDashboard();
    carregarDashboardResolucao();
  }, []);

  async function carregarDashboard() {
    try {
      setLoading(true);

      const [servicosResponse, desfechosResponse, alertasResponse] =
        await Promise.all([
          api.get("/consultorio/dashboard-servicos"),
          api.get("/consultorio/dashboard-desfechos"),
          api.get("/consultorio/alertas-pendentes"),
        ]);

      setServicos(servicosResponse.data);
      setDesfechos(desfechosResponse.data);
      setAlertas(alertasResponse.data);
    } catch (error) {
      console.error("Erro ao carregar dashboard:", error);
    } finally {
      setLoading(false);
    }
  }

  async function carregarDashboardResolucao() {
    try {
      setCarregandoResolucao(true);

      const response = await api.get(
        "/consultorio/dashboard-resolucao-alertas"
      );

      setDashboardResolucao(response.data);
    } catch (error) {
      console.error(
        "Erro ao carregar dashboard de resolução:",
        error
      );

      setDashboardResolucao(null);
    } finally {
      setCarregandoResolucao(false);
    }
  }

  if (loading) {
    return (
      <div>
        <h2>Dashboard</h2>
        <p className="muted">Carregando indicadores...</p>
      </div>
    );
  }

  const dadosServicos = [
    {
      nome: "PA",
      total: servicos?.pressao_arterial?.total || 0,
      alterados: servicos?.pressao_arterial?.alterados || 0,
    },
    {
      nome: "Glicemia",
      total: servicos?.glicemia?.total || 0,
      alterados: servicos?.glicemia?.alterados || 0,
    },
    {
      nome: "Bioimp.",
      total: servicos?.bioimpedancia?.total || 0,
      alterados: servicos?.bioimpedancia?.risco || 0,
    },
    {
      nome: "PFE",
      total: servicos?.pico_fluxo?.total || 0,
      alterados: servicos?.pico_fluxo?.risco || 0,
    },
  ];

  const dadosDesfechos = Object.entries(desfechos?.melhora_clinica || {}).map(
    ([nome, valor]) => ({
      nome,
      valor,
    })
  );

  return (
    <div>
      <h2>Dashboard</h2>
      <p className="muted">
        Indicadores gerais dos serviços rápidos, desfechos clínicos e alertas.
      </p>

      <div className="cards-grid">
        <div className="metric-card">
          <span>Atendimentos rápidos</span>
          <strong>{servicos?.total_atendimentos_rapidos || 0}</strong>
          <p>Total de atendimentos registrados.</p>
        </div>

        <div className="metric-card">
          <span>Procedimentos</span>
          <strong>{servicos?.total_procedimentos || 0}</strong>
          <p>PA, glicemia, bioimpedância e PFE.</p>
        </div>

        <div className="metric-card">
          <span>Alertas clínicos</span>
          <strong>{servicos?.alertas?.total_alertas || 0}</strong>
          <p>Alterações identificadas nos serviços.</p>
        </div>

        <div className="metric-card">
          <span>Desfechos</span>
          <strong>{desfechos?.total_desfechos || 0}</strong>
          <p>Resultados clínicos registrados.</p>
        </div>

        <div className="metric-card">
          <span>Resolução</span>
          <strong>
            {desfechos?.resolucao_problema?.percentual_resolucao || 0}%
          </strong>
          <p>Problemas resolvidos.</p>
        </div>

        <div className="metric-card">
          <span>Alertas pendentes</span>
          <strong>{alertas?.resumo?.total_alertas || 0}</strong>
          <p>Retornos, riscos e pendências.</p>
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="chart-card">
          <h3>Procedimentos e alterações</h3>
          <p className="muted">Comparação entre total registrado e alterações.</p>

          <div className="chart-box">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={dadosServicos}>
                <XAxis dataKey="nome" />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar
                  dataKey="total"
                  name="Total"
                  fill="#0f766e"
                />

                <Bar
                  dataKey="alterados"
                  name="Alterados/Risco"
                  fill="#dc2626"
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="chart-card">
          <h3>Melhora clínica</h3>
          <p className="muted">Distribuição dos desfechos informados.</p>

          {dadosDesfechos.length === 0 ? (
            <p className="muted">Sem desfechos suficientes para gráfico.</p>
          ) : (
            <div className="chart-box">
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie
                    data={dadosDesfechos}
                    dataKey="valor"
                    nameKey="nome"
                    outerRadius={90}
                    label
                  >
                    {dadosDesfechos.map((_, index) => (
                      <Cell key={index} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>
      <div className="dashboard-card">
      <div className="section-header-row">
        <div>
          <h3>Resolutividade clínica</h3>

          <p className="muted">
            Indicadores operacionais da fila clínica e
            acompanhamento farmacêutico.
          </p>
        </div>
      </div>

      {carregandoResolucao ? (
        <p className="muted">
          Carregando indicadores...
        </p>
      ) : dashboardResolucao ? (
        <>
          <div className="cards-grid four">
            <div className="metric-card">
              <span>Alertas gerados</span>

              <strong>
                {dashboardResolucao.total_alertas_gerados || 0}
              </strong>
            </div>

            <div className="metric-card warning">
              <span>Ativos</span>

              <strong>
                {dashboardResolucao.total_ativos || 0}
              </strong>
            </div>

            <div className="metric-card success">
              <span>Resolvidos</span>

              <strong>
                {dashboardResolucao.total_resolvidos || 0}
              </strong>
            </div>

            <div className="metric-card">
              <span>Taxa resolução</span>

              <strong>
                {dashboardResolucao.taxa_resolucao || 0}%
              </strong>
            </div>
          </div>

          <div className="dashboard-split-grid">
            <div className="dashboard-subcard">
              <h4>Desfechos</h4>

              {Object.entries(
                dashboardResolucao.por_desfecho || {}
              ).map(([desfecho, total]) => (
                <div
                  key={desfecho}
                  className="indicator-row"
                >
                  <span>{desfecho}</span>

                  <strong>{total}</strong>
                </div>
              ))}
            </div>

            <div className="dashboard-subcard">
              <h4>Por prioridade</h4>

              {Object.entries(
                dashboardResolucao.por_prioridade || {}
              ).map(([prioridade, total]) => (
                <div
                  key={prioridade}
                  className="indicator-row"
                >
                  <span>{prioridade}</span>

                  <strong>{total}</strong>
                </div>
              ))}
            </div>
          </div>

          <div className="dashboard-subcard">
            <h4>Resoluções recentes</h4>

            <div className="recent-resolution-list">
                {dashboardResolucao.resolucoes_recentes?.slice(0, 3).map(
                  (item, index) => (
                  <div
                    key={`${item.paciente_nome}-${index}`}
                    className="recent-resolution-item"
                  >
                    <div>
                      <strong>
                        {item.paciente_nome}
                      </strong>

                      <p>
                        {item.mensagem_alerta}
                      </p>
                    </div>

                    <div className="resolution-side">
                      <span className="timeline-tag">
                        {item.desfecho}
                      </span>

                      <small>
                        {item.resolvido_por}
                      </small>
                    </div>
                  </div>
                )
              )}
              {dashboardResolucao.resolucoes_recentes?.length > 3 && (
                <button
                  className="secondary-button"
                  onClick={() => setActivePage?.("fila-clinica")}
                >
                  Ver lista completa
                </button>
)}
            </div>
          </div>
        </>
      ) : (
        <p className="muted">
          Não foi possível carregar os indicadores.
        </p>
      )}
    </div>
    </div>
  );
}