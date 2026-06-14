import { useEffect, useMemo, useState } from "react";
import { api } from "../../api/api";
import PrmIndicadores from "../analytics/PrmIndicadores.jsx";
import IntervencoesPadronizadasIndicadores from "../analytics/IntervencoesPadronizadasIndicadores.jsx";
import "../analytics/AnalyticsWorkspace.css";

import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  CartesianGrid,
  Legend,
} from "recharts";

const COLORS = {
  maxima: "#dc2626",
  alta: "#ea580c",
  moderada: "#ca8a04",
  rotina: "#16a34a",
  geral: "#2563eb",
  neutro: "#64748b",
};

function objetoParaGrafico(obj = {}) {
  return Object.entries(obj || {}).map(([name, total]) => ({
    name,
    total: Number(total || 0),
  }));
}

function prioridadePeso(prioridade = "") {
  const texto = prioridade.toUpperCase();

  if (texto.includes("MÁXIMA") || texto.includes("MAXIMA")) return "maxima";
  if (texto.includes("ALTA")) return "alta";
  if (texto.includes("MODERADA")) return "moderada";
  return "rotina";
}

export default function DashboardEpidemiologico() {
  const [servicos, setServicos] = useState(null);
  const [filaClinica, setFilaClinica] = useState([]);
  const [desfechos, setDesfechos] = useState(null);
  const [antropometrico, setAntropometrico] = useState(null);
  const [cardiovascular, setCardiovascular] = useState(null);
  const [glicemico, setGlicemico] = useState(null);
  const [carregando, setCarregando] = useState(false);
  const [dataInicio, setDataInicio] = useState("");
  const [dataFim, setDataFim] = useState("");
  const [serieTemporal, setSerieTemporal] = useState([]);
  const [evolucaoRisco, setEvolucaoRisco] = useState(null);
  const [dashboardFarmaco, setDashboardFarmaco] = useState(null);
  const [abaDashboard, setAbaDashboard] = useState("geral");
  const [dashboardEfetividade, setDashboardEfetividade] = useState(null);

  useEffect(() => {
    carregarDashboard();
  }, [dataInicio, dataFim]);

  async function carregarDashboard() {
    try {
      setCarregando(true);

      const params = {};

      if (dataInicio) params.data_inicio = dataInicio;
      if (dataFim) params.data_fim = dataFim;

      const evolucaoRiscoResponse = await api.get(
        "/consultorio/evolucao-risco-populacional"
      );

      const efetividadeResponse = await api.get(
        "/consultorio/dashboard-efetividade-cuidado"
      );

setDashboardEfetividade(efetividadeResponse.data);

      const farmacoResponse = await api.get(
        "/consultorio/dashboard-farmacoterapeutico"
      );

setDashboardFarmaco(farmacoResponse.data);

setEvolucaoRisco(evolucaoRiscoResponse.data);

      const [
        servicosResponse,
        filaResponse,
        desfechosResponse,
        antropometricoResponse,
        cardiovascularResponse,
        glicemicoResponse,
      ] = await Promise.all([
        api.get("/consultorio/dashboard-servicos", { params }),
        api.get("/consultorio/fila-clinica"),
        api.get("/consultorio/dashboard-desfechos", { params }),
        api.get("/consultorio/dashboard-antropometrico"),
        api.get("/consultorio/dashboard-cardiovascular"),
        api.get("/consultorio/dashboard-glicemico"),
      ]);

      setServicos(servicosResponse.data);
      setFilaClinica(filaResponse.data || []);
      setDesfechos(desfechosResponse.data);
      setAntropometrico(antropometricoResponse.data);
      setCardiovascular(cardiovascularResponse.data);
      setGlicemico(glicemicoResponse.data);
    } catch (error) {
      console.error("Erro ao carregar dashboard epidemiológico:", error);
    } finally {
      setCarregando(false);
    }
      const serieResponse = await api.get(
      "/consultorio/dashboard-serie-temporal"
    );

    setSerieTemporal(serieResponse.data || []);
      }

  async function abrirPdfAutenticado(url) {
    try {
      const response = await api.get(url, {
        responseType: "blob",
      });

      const fileURL = window.URL.createObjectURL(
        new Blob([response.data], { type: "application/pdf" })
      );

      window.open(fileURL, "_blank");
    } catch (error) {
      console.error("Erro ao abrir PDF:", error.response?.data || error);
      alert("Erro ao abrir PDF autenticado.");
    }
  }

  async function baixarExcelAutenticado(url, nomeArquivo) {
    try {
      const response = await api.get(url, {
        responseType: "blob",
      });

      const link = document.createElement("a");
      const fileURL = window.URL.createObjectURL(new Blob([response.data]));

      link.href = fileURL;
      link.setAttribute("download", nomeArquivo);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error("Erro ao baixar Excel:", error.response?.data || error);
      alert("Erro ao baixar Excel autenticado.");
    }
  }

  const prioridadeClinica = useMemo(() => {
    const resumo = {
      maxima: 0,
      alta: 0,
      moderada: 0,
      rotina: 0,
    };

    filaClinica.forEach((item) => {
      const chave = prioridadePeso(item.prioridade);
      resumo[chave] += 1;
    });

    return resumo;
  }, [filaClinica]);

  const riscoData = [
    { name: "Máxima", value: prioridadeClinica.maxima, color: COLORS.maxima },
    { name: "Alta", value: prioridadeClinica.alta, color: COLORS.alta },
    { name: "Moderada", value: prioridadeClinica.moderada, color: COLORS.moderada },
    { name: "Rotina", value: prioridadeClinica.rotina, color: COLORS.rotina },
  ];

  const atendimentosData = servicos
    ? [
        { name: "PA", total: servicos.pressao_arterial?.total || 0 },
        { name: "Glicemia", total: servicos.glicemia?.total || 0 },
        { name: "Bioimpedância", total: servicos.bioimpedancia?.total || 0 },
        { name: "Pico de fluxo", total: servicos.pico_fluxo?.total || 0 },
      ]
    : [];

  const alertasServicosData = servicos
    ? [
        {
          name: "PA alterada",
          total: servicos.alertas?.pa_alterada || 0,
          color: COLORS.alta,
        },
        {
          name: "Glicemia alterada",
          total: servicos.alertas?.glicemia_alterada || 0,
          color: COLORS.moderada,
        },
        {
          name: "Bioimpedância risco",
          total: servicos.alertas?.bioimpedancia_risco || 0,
          color: COLORS.maxima,
        },
        {
          name: "PFE risco",
          total: servicos.alertas?.pico_fluxo_risco || 0,
          color: "#7c3aed",
        },
      ]
    : [];

  const desfechosResolucaoData = desfechos
    ? [
        {
          name: "Resolvidos",
          total: desfechos.resolucao_problema?.resolvidos || 0,
          color: COLORS.rotina,
        },
        {
          name: "Não resolvidos",
          total: desfechos.resolucao_problema?.nao_resolvidos || 0,
          color: COLORS.maxima,
        },
      ]
    : [];

  const melhoraClinicaData = objetoParaGrafico(desfechos?.melhora_clinica || {});
  const adesaoData = objetoParaGrafico(desfechos?.adesao_tratamento || {});

  const imcClassificacaoData = objetoParaGrafico(
    antropometrico?.classificacoes_imc || {}
  );

  const gorduraVisceralData = objetoParaGrafico(
    antropometrico?.classificacoes_gordura_visceral || {}
  );

  const riscoCardiovascularData = cardiovascular
    ? [
        {
          name: "Normal",
          total: cardiovascular.classificacoes?.normal || 0,
          color: COLORS.rotina,
        },
        {
          name: "PA elevada",
          total: cardiovascular.classificacoes?.pa_elevada || 0,
          color: COLORS.moderada,
        },
        {
          name: "Hipertensão",
          total: cardiovascular.classificacoes?.hipertensao || 0,
          color: COLORS.alta,
        },
        {
          name: "Crise hipertensiva",
          total: cardiovascular.classificacoes?.crise_hipertensiva || 0,
          color: COLORS.maxima,
        },
      ]
    : [];

  const riscoGlicemicoData = glicemico
    ? [
        {
          name: "Normal",
          total: glicemico.classificacoes?.normal || 0,
          color: COLORS.rotina,
        },
        {
          name: "Alterada",
          total: glicemico.classificacoes?.alterada || 0,
          color: COLORS.moderada,
        },
        {
          name: "Possível diabetes",
          total: glicemico.classificacoes?.possivel_diabetes || 0,
          color: COLORS.maxima,
        },
      ]
    : [];

  const tiposGlicemiaData = objetoParaGrafico(glicemico?.tipos_jejum || {});

  if (carregando) {
    return <p className="muted">Carregando dashboard...</p>;
  }

  if (!servicos) {
    return <p className="muted">Sem dados disponíveis.</p>;
  }


  const dadosTendenciaRisco = evolucaoRisco
  ? Object.entries(evolucaoRisco.resumo || {}).map(([nome, valor]) => ({
      nome,
      valor,
    }))
  : [];

const dadosRiscoAtual = evolucaoRisco
  ? evolucaoRisco.pacientes.reduce((acc, paciente) => {
      const risco = paciente.risco_atual || "não_classificado";
      acc[risco] = (acc[risco] || 0) + 1;
      return acc;
    }, {})
  : {};

const dadosRiscoAtualGrafico = Object.entries(dadosRiscoAtual).map(
  ([nome, valor]) => ({
    nome,
    valor,
  })
);

const scoreMedioAtual =
  evolucaoRisco?.pacientes?.length > 0
    ? (
        evolucaoRisco.pacientes.reduce(
          (soma, paciente) => soma + (paciente.score_atual || 0),
          0
        ) / evolucaoRisco.pacientes.length
      ).toFixed(2)
    : 0;

    const dadosRiscoFarmaco = dashboardFarmaco
  ? Object.entries(dashboardFarmaco.risco_farmacoterapeutico || {}).map(
      ([nome, valor]) => ({ nome, valor })
    )
  : [];

const dadosTendenciaFarmaco = dashboardFarmaco
  ? Object.entries(dashboardFarmaco.tendencias || {}).map(
      ([nome, valor]) => ({ nome, valor })
    )
  : [];

const dadosAdesaoFarmaco = dashboardFarmaco
  ? [
      {
        nome: "Boa adesão",
        valor: dashboardFarmaco.adesao?.boa_adesao || 0,
      },
      {
        nome: "Baixa adesão",
        valor: dashboardFarmaco.adesao?.baixa_adesao || 0,
      },
    ]
  : [];

    const dadosResultadosPlanos = dashboardEfetividade
      ? Object.entries(dashboardEfetividade.resultados || {}).map(
          ([nome, valor]) => ({ nome, valor })
        )
      : [];

    const dadosProblemasPlanos = dashboardEfetividade
      ? Object.entries(dashboardEfetividade.problemas || {}).map(
          ([nome, valor]) => ({ nome, valor })
        )
      : [];

  return (
    <div>
      <h2>Dashboard Epidemiológico</h2>
      <p className="muted">
        Indicadores clínicos, assistenciais e epidemiológicos consolidados.
      </p>

      <div className="prontuario-tabs">
        <button
          className={abaDashboard === "geral" ? "active" : ""}
          onClick={() => setAbaDashboard("geral")}
        >
          Visão geral
        </button>

        <button
          className={abaDashboard === "servicos" ? "active" : ""}
          onClick={() => setAbaDashboard("servicos")}
        >
          Serviços rápidos
        </button>

        <button
          className={abaDashboard === "risco" ? "active" : ""}
          onClick={() => setAbaDashboard("risco")}
        >
          Risco longitudinal
        </button>

        <button
          className={abaDashboard === "farmaco" ? "active" : ""}
          onClick={() => setAbaDashboard("farmaco")}
        >
          Farmacoterapia
        </button>

        <button
          className={abaDashboard === "efetividade" ? "active" : ""}
          onClick={() => setAbaDashboard("efetividade")}
        >
          Efetividade do cuidado
        </button>

        <button
          className={abaDashboard === "prm" ? "active" : ""}
          onClick={() => setAbaDashboard("prm")}
        >
          PRM
        </button>

        <button
          className={abaDashboard === "intervencoes" ? "active" : ""}
          onClick={() => setAbaDashboard("intervencoes")}
        >
          Intervenções
        </button>

        <button
          className={abaDashboard === "cientifico" ? "active" : ""}
          onClick={() => setAbaDashboard("cientifico")}
        >
          Indicadores científicos
        </button>
      </div>

      <div className="filters-card">
        <div className="filters-grid">
          <div>
            <label>Data inicial</label>
            <input
              type="date"
              className="input"
              value={dataInicio}
              onChange={(e) => setDataInicio(e.target.value)}
            />
          </div>

          <div>
            <label>Data final</label>
            <input
              type="date"
              className="input"
              value={dataFim}
              onChange={(e) => setDataFim(e.target.value)}
            />
          </div>

          <div className="filter-actions">
            <button
              className="secondary-button"
              onClick={() => {
                setDataInicio("");
                setDataFim("");
              }}
            >
              Limpar filtros
            </button>
          </div>
        </div>
      </div>
      {abaDashboard === "geral" && (
        <div className="prontuario-tab-content">
      <h3 className="dashboard-section-title">Resumo assistencial</h3>
      <div className="kpi-grid">
        <div className="kpi-card general">
          <span>Atendimentos rápidos</span>
          <strong>{servicos.total_atendimentos_rapidos || 0}</strong>
        </div>

        <div className="kpi-card general">
          <span>Procedimentos</span>
          <strong>{servicos.total_procedimentos || 0}</strong>
        </div>

        <div className="kpi-card warning">
          <span>Alertas clínicos</span>
          <strong>{servicos.alertas?.total_alertas || 0}</strong>
        </div>

        <div className="kpi-card success">
          <span>Pacientes na fila</span>
          <strong>{filaClinica.length || 0}</strong>
        </div>
      </div>

      <h3 className="dashboard-section-title">Prioridade clínica</h3>
      <div className="kpi-grid">
        <div className="kpi-card danger">
          <span>Prioridade máxima</span>
          <strong>{prioridadeClinica.maxima}</strong>
        </div>

        <div className="kpi-card warning">
          <span>Prioridade alta</span>
          <strong>{prioridadeClinica.alta}</strong>
        </div>

        <div className="kpi-card moderate">
          <span>Prioridade moderada</span>
          <strong>{prioridadeClinica.moderada}</strong>
        </div>

        <div className="kpi-card success">
          <span>Rotina</span>
          <strong>{prioridadeClinica.rotina}</strong>
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="chart-card">
          <h3>Distribuição de prioridade clínica</h3>
          <ResponsiveContainer width="100%" height={320}>
            <PieChart>
              <Pie data={riscoData} dataKey="value" nameKey="name" outerRadius={110} label>
                {riscoData.map((entry, index) => (
                  <Cell key={`risco-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3>Volume de procedimentos</h3>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={atendimentosData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="total" fill={COLORS.geral} radius={[10, 10, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

        </div>
      )}

      {abaDashboard === "servicos" && (
        <div className="prontuario-tab-content">
      <h3 className="dashboard-section-title">Alertas por serviço rápido</h3>
      <div className="dashboard-grid">
        <div className="chart-card">
          <h3>Distribuição de alertas</h3>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={alertasServicosData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="total" radius={[10, 10, 0, 0]}>
                {alertasServicosData.map((entry, index) => (
                  <Cell key={`alerta-servico-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3>Resumo por procedimento</h3>
          <div className="summary-list">
            <div>
              <strong>PA alterada:</strong> {servicos.pressao_arterial?.alterados || 0} / {servicos.pressao_arterial?.total || 0}
            </div>
            <div>
              <strong>Glicemia alterada:</strong> {servicos.glicemia?.alterados || 0} / {servicos.glicemia?.total || 0}
            </div>
            <div>
              <strong>Bioimpedância em risco:</strong> {servicos.bioimpedancia?.risco || 0} / {servicos.bioimpedancia?.total || 0}
            </div>
            <div>
              <strong>Pico de fluxo em risco:</strong> {servicos.pico_fluxo?.risco || 0} / {servicos.pico_fluxo?.total || 0}
            </div>
          </div>
        </div>
      </div>

      {desfechos && (
        <>
          <h3 className="dashboard-section-title">Desfechos clínicos</h3>
          <div className="kpi-grid">
            <div className="kpi-card general">
              <span>Desfechos registrados</span>
              <strong>{desfechos.total_desfechos || 0}</strong>
            </div>

            <div className="kpi-card success">
              <span>Resolvidos</span>
              <strong>{desfechos.resolucao_problema?.resolvidos || 0}</strong>
            </div>

            <div className="kpi-card warning">
              <span>Taxa de resolução</span>
              <strong>{desfechos.resolucao_problema?.percentual_resolucao || 0}%</strong>
            </div>

            <div className="kpi-card danger">
              <span>Encaminhamentos</span>
              <strong>{desfechos.encaminhamentos?.total || 0}</strong>
            </div>
          </div>

          <div className="dashboard-grid">
            <div className="chart-card">
              <h3>Resolução de problemas</h3>
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={desfechosResolucaoData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="total" radius={[10, 10, 0, 0]}>
                    {desfechosResolucaoData.map((entry, index) => (
                      <Cell key={`resolucao-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-card">
              <h3>Adesão ao tratamento</h3>
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={adesaoData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="total" fill="#0f766e" radius={[10, 10, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="dashboard-grid">
            <div className="chart-card">
              <h3>Melhora clínica</h3>
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={melhoraClinicaData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="total" fill="#2563eb" radius={[10, 10, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}

      {antropometrico && (
        <>
          <h3 className="dashboard-section-title">Indicadores antropométricos</h3>
          <div className="kpi-grid">
            <div className="kpi-card general">
              <span>Avaliações antropométricas</span>
              <strong>{antropometrico.total_avaliacoes || 0}</strong>
            </div>

            <div className="kpi-card moderate">
              <span>IMC médio</span>
              <strong>{antropometrico.media_imc || 0}</strong>
            </div>

            <div className="kpi-card warning">
              <span>Gordura corporal média</span>
              <strong>{antropometrico.media_gordura_corporal || 0}%</strong>
            </div>

            <div className="kpi-card success">
              <span>Massa muscular média</span>
              <strong>{antropometrico.media_massa_muscular || 0}%</strong>
            </div>
          </div>

          <div className="dashboard-grid">
            <div className="chart-card">
              <h3>Classificação por IMC</h3>
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={imcClassificacaoData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="total" fill="#0891b2" radius={[10, 10, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-card">
              <h3>Gordura visceral</h3>
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={gorduraVisceralData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="total" fill="#7c3aed" radius={[10, 10, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}

      {cardiovascular && (
        <>
          <h3 className="dashboard-section-title">Indicadores cardiovasculares</h3>
          <div className="kpi-grid">
            <div className="kpi-card general">
              <span>Aferições de PA</span>
              <strong>{cardiovascular.total_afericoes || 0}</strong>
            </div>

            <div className="kpi-card success">
              <span>PAS média</span>
              <strong>{cardiovascular.media_pas || 0}</strong>
            </div>

            <div className="kpi-card moderate">
              <span>PAD média</span>
              <strong>{cardiovascular.media_pad || 0}</strong>
            </div>

            <div className="kpi-card warning">
              <span>PA alteradas</span>
              <strong>
                {(cardiovascular.classificacoes?.pa_elevada || 0) +
                  (cardiovascular.classificacoes?.hipertensao || 0) +
                  (cardiovascular.classificacoes?.crise_hipertensiva || 0)}
              </strong>
            </div>
          </div>

          <div className="dashboard-grid">
            <div className="chart-card">
              <h3>Classificação cardiovascular</h3>
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={riscoCardiovascularData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="total" radius={[10, 10, 0, 0]}>
                    {riscoCardiovascularData.map((entry, index) => (
                      <Cell key={`cardio-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-card">
              <h3>Resumo cardiovascular</h3>
              <div className="summary-list">
                <div><strong>Normal:</strong> {cardiovascular.classificacoes?.normal || 0}</div>
                <div><strong>PA elevada:</strong> {cardiovascular.classificacoes?.pa_elevada || 0}</div>
                <div><strong>Hipertensão:</strong> {cardiovascular.classificacoes?.hipertensao || 0}</div>
                <div><strong>Crise hipertensiva:</strong> {cardiovascular.classificacoes?.crise_hipertensiva || 0}</div>
              </div>
            </div>
          </div>
        </>
      )}

      {glicemico && (
        <>
          <h3 className="dashboard-section-title">Indicadores glicêmicos</h3>
          <div className="kpi-grid">
            <div className="kpi-card general">
              <span>Aferições glicêmicas</span>
              <strong>{glicemico.total_afericoes || 0}</strong>
            </div>

            <div className="kpi-card success">
              <span>Glicemia média</span>
              <strong>{glicemico.media_glicemia || 0}</strong>
            </div>

            <div className="kpi-card warning">
              <span>Glicemias alteradas</span>
              <strong>{glicemico.classificacoes?.alterada || 0}</strong>
            </div>

            <div className="kpi-card danger">
              <span>Possível diabetes</span>
              <strong>{glicemico.classificacoes?.possivel_diabetes || 0}</strong>
            </div>
          </div>

          <div className="dashboard-grid">
            <div className="chart-card">
              <h3>Classificação glicêmica</h3>
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={riscoGlicemicoData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="total" radius={[10, 10, 0, 0]}>
                    {riscoGlicemicoData.map((entry, index) => (
                      <Cell key={`glicemia-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-card">
              <h3>Tipo de aferição glicêmica</h3>
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={tiposGlicemiaData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="total" fill="#9333ea" radius={[10, 10, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
          <div className="chart-card">
            <h3>Série temporal clínica</h3>

            <p className="muted">
              Evolução mensal dos atendimentos, alterações clínicas e resoluções.
            </p>

            <div className="chart-box">
              <ResponsiveContainer width="100%" height={320}>
                <LineChart data={serieTemporal}>
                  <XAxis dataKey="mes" />
                  <YAxis allowDecimals={false} />
                  <Tooltip />

                  <Line
                    type="monotone"
                    dataKey="atendimentos"
                    name="Atendimentos"
                    stroke="#0f766e"
                    strokeWidth={3}
                  />

                  <Line
                    type="monotone"
                    dataKey="total_alteracoes"
                    name="Alterações clínicas"
                    stroke="#dc2626"
                    strokeWidth={3}
                  />

                  <Line
                    type="monotone"
                    dataKey="alertas_resolvidos"
                    name="Alertas resolvidos"
                    stroke="#2563eb"
                    strokeWidth={3}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}
        </div>
      )}

      {abaDashboard === "risco" && (
        <div className="prontuario-tab-content">
      <div className="chart-card">
        <h3>Evolução longitudinal do risco populacional</h3>

        <p className="muted">
          Tendência dos pacientes acompanhados segundo variação do score de risco.
        </p>

        <div className="cards-grid four">
          <div className="metric-card success">
            <span>Melhora</span>
            <strong>{evolucaoRisco?.resumo?.melhora || 0}</strong>
          </div>

          <div className="metric-card">
            <span>Estabilidade</span>
            <strong>{evolucaoRisco?.resumo?.estabilidade || 0}</strong>
          </div>

          <div className="metric-card danger">
            <span>Piora</span>
            <strong>{evolucaoRisco?.resumo?.piora || 0}</strong>
          </div>

          <div className="metric-card warning">
            <span>Score médio</span>
            <strong>{scoreMedioAtual}</strong>
          </div>
        </div>

        <div className="dashboard-grid">
          <div className="chart-box">
            <h4>Tendência clínica</h4>

            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={dadosTendenciaRisco}
                  dataKey="valor"
                  nameKey="nome"
                  outerRadius={90}
                  label
                >
                  {dadosTendenciaRisco.map((entry, index) => (
                    <Cell
                      key={`cell-tendencia-${index}`}
                      fill={
                        entry.nome === "melhora"
                          ? "#16a34a"
                          : entry.nome === "piora"
                          ? "#dc2626"
                          : "#2563eb"
                      }
                    />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-box">
            <h4>Risco atual</h4>

            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={dadosRiscoAtualGrafico}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="nome" />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="valor" name="Pacientes" fill="#0f766e" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
        </div>
      )}

      {abaDashboard === "farmaco" && (
        <div className="prontuario-tab-content">
      <div className="chart-card">
        <h3>Dashboard farmacoterapêutico</h3>

        <p className="muted">
          Indicadores de polifarmácia, risco farmacoterapêutico, adesão e intervenções.
        </p>

        <div className="cards-grid four">
          <div className="metric-card danger">
            <span>Pacientes em polifarmácia</span>
            <strong>{dashboardFarmaco?.pacientes_polifarmacia || 0}</strong>
          </div>

          <div className="metric-card warning">
            <span>Média de medicamentos</span>
            <strong>
              {dashboardFarmaco?.media_medicamentos_por_paciente || 0}
            </strong>
          </div>

          <div className="metric-card success">
            <span>Taxa de aceitação</span>
            <strong>
              {dashboardFarmaco?.intervencoes?.taxa_aceitacao || 0}%
            </strong>
          </div>

          <div className="metric-card">
            <span>Encaminhamentos</span>
            <strong>
              {dashboardFarmaco?.intervencoes?.encaminhamentos || 0}
            </strong>
          </div>
        </div>

        <div className="dashboard-grid">
          <div className="chart-box">
            <h4>Risco farmacoterapêutico</h4>

            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={dadosRiscoFarmaco}
                  dataKey="valor"
                  nameKey="nome"
                  outerRadius={90}
                  label
                >
                  {dadosRiscoFarmaco.map((entry, index) => (
                    <Cell
                      key={`risco-farmaco-${index}`}
                      fill={
                        entry.nome === "alto"
                          ? "#dc2626"
                          : entry.nome === "moderado"
                          ? "#f59e0b"
                          : "#16a34a"
                      }
                    />
                  ))}
                </Pie>

                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-box">
            <h4>Tendência farmacoterapêutica</h4>

            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={dadosTendenciaFarmaco}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="nome" />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="valor" name="Pacientes" fill="#0f766e" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-box">
            <h4>Adesão terapêutica</h4>

            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={dadosAdesaoFarmaco}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="nome" />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="valor" name="Registros" fill="#2563eb" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
        </div>
      )}

      {abaDashboard === "efetividade" && (
          <div className="prontuario-tab-content">
            <div className="chart-card">
              <h3>Efetividade do cuidado farmacêutico</h3>

              <p className="muted">
                Indicadores relacionados aos planos de cuidado, conclusão e alcance dos objetivos terapêuticos.
              </p>

              <div className="cards-grid four">
                <div className="metric-card">
                  <span>Planos ativos</span>
                  <strong>{dashboardEfetividade?.planos?.ativos || 0}</strong>
                </div>

                <div className="metric-card success">
                  <span>Planos concluídos</span>
                  <strong>{dashboardEfetividade?.planos?.concluidos || 0}</strong>
                </div>

                <div className="metric-card warning">
                  <span>Taxa de sucesso</span>
                  <strong>{dashboardEfetividade?.taxa_sucesso || 0}%</strong>
                </div>

                <div className="metric-card">
                  <span>Tempo médio</span>
                  <strong>
                    {dashboardEfetividade?.tempo_medio_conclusao_dias || 0} dias
                  </strong>
                </div>
              </div>

              <div className="dashboard-grid">
                <div className="chart-box">
                  <h4>Resultado dos planos</h4>

                  <ResponsiveContainer width="100%" height={260}>
                    <PieChart>
                      <Pie
                        data={dadosResultadosPlanos}
                        dataKey="valor"
                        nameKey="nome"
                        outerRadius={90}
                        label
                      >
                        {dadosResultadosPlanos.map((entry, index) => (
                          <Cell
                            key={`resultado-plano-${index}`}
                            fill={
                              entry.nome === "atingidos"
                                ? "#16a34a"
                                : entry.nome === "parcialmente_atingidos"
                                ? "#f59e0b"
                                : "#dc2626"
                            }
                          />
                        ))}
                      </Pie>

                      <Tooltip />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </div>

                <div className="chart-box">
                  <h4>Problemas acompanhados</h4>

                  <ResponsiveContainer width="100%" height={320}>
                    <BarChart data={dadosProblemasPlanos}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="nome" />
                      <YAxis allowDecimals={false} />
                      <Tooltip />
                      <Bar dataKey="valor" name="Planos" fill="#0f766e" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </div>
        )}

      {abaDashboard === "prm" && (
        <PrmIndicadores />
      )}

      {abaDashboard === "intervencoes" && (
        <IntervencoesPadronizadasIndicadores />
      )}

      {abaDashboard === "cientifico" && (
        <div className="prontuario-tab-content">
          <h3 className="dashboard-section-title">Indicadores científicos e exportações</h3>
          <p className="muted">
            Relatórios e bases exportáveis para gestão, pesquisa e avaliação institucional.
          </p>

      <div className="dashboard-actions">
        <button
          className="primary-button"
          onClick={() => abrirPdfAutenticado("/consultorio/relatorio-cientifico-pdf")}
        >
          Relatório científico PDF
        </button>

        <button
          className="secondary-button"
          onClick={() =>
            baixarExcelAutenticado(
              "/consultorio/exportacao-cientifica-excel",
              "exportacao_cientifica.xlsx"
            )
          }
        >
          Exportação científica
        </button>

        <button
          className="secondary-button"
          onClick={() =>
            baixarExcelAutenticado(
              "/consultorio/exportacao-pesquisa-anonimizada",
              "pesquisa_anonimizada_completa.xlsx"
            )
          }
        >
          Pesquisa anonimizada
        </button>
      </div>

          <div className="chart-card">
            <h3>Resumo científico disponível</h3>
            <div className="summary-list">
              <div>
                <strong>Pacientes clínicos:</strong> {dashboardFarmaco?.total_pacientes || 0}
              </div>
              <div>
                <strong>Pacientes em polifarmácia:</strong> {dashboardFarmaco?.pacientes_polifarmacia || 0}
              </div>
              <div>
                <strong>Taxa de polifarmácia:</strong> {dashboardFarmaco?.taxa_polifarmacia || 0}%
              </div>
              <div>
                <strong>Intervenções farmacoterapêuticas:</strong> {dashboardFarmaco?.intervencoes?.total || 0}
              </div>
              <div>
                <strong>Taxa de aceitação:</strong> {dashboardFarmaco?.intervencoes?.taxa_aceitacao || 0}%
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}