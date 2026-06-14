import { useMemo, useState } from "react";
import { BarChart3, FileSpreadsheet, Gauge, Microscope, RefreshCw, TrendingUp } from "lucide-react";
import Dashboard from "../dashboard/Dashboard.jsx";
import DashboardEpidemiologico from "../dashboard/DashboardEpidemiologico.jsx";
import IndicadoresCientificos from "../cientifico/IndicadoresCientificos.jsx";
import RelatoriosGerenciais from "../relatorios_gerenciais/RelatoriosGerenciais.jsx";
import IntegracaoIntervencoes from "./IntegracaoIntervencoes.jsx";
import "./AnalyticsWorkspace.css";

const ABAS = [
  {
    key: "executivo",
    label: "Visão Executiva",
    icon: Gauge,
    descricao: "Indicadores gerais e visão rápida do serviço.",
  },
  {
    key: "assistencial",
    label: "Assistencial e Epidemiológico",
    icon: BarChart3,
    descricao: "Serviços, risco, efetividade, farmacoterapia e indicadores populacionais.",
  },
  {
    key: "cientifico",
    label: "Científico",
    icon: Microscope,
    descricao: "Indicadores para pesquisa, produção científica e análises institucionais.",
  },
  {
    key: "relatorios",
    label: "Relatórios",
    icon: FileSpreadsheet,
    descricao: "Exportações gerenciais em PDF e Excel.",
  },
  {
    key: "integracao",
    label: "Integração das Intervenções",
    icon: RefreshCw,
    descricao: "Governança da integração do App de Intervenções: staging, checkpoints, consistência e rastreabilidade.",
  },
];

export default function AnalyticsWorkspace() {
  const [abaAtiva, setAbaAtiva] = useState("executivo");

  const aba = useMemo(
    () => ABAS.find((item) => item.key === abaAtiva) || ABAS[0],
    [abaAtiva]
  );

  function renderConteudo() {
    if (abaAtiva === "executivo") return <Dashboard />;
    if (abaAtiva === "assistencial") return <DashboardEpidemiologico />;
    if (abaAtiva === "cientifico") return <IndicadoresCientificos />;
    if (abaAtiva === "relatorios") return <RelatoriosGerenciais />;
    if (abaAtiva === "integracao") return <IntegracaoIntervencoes />;
    return <Dashboard />;
  }

  return (
    <div className="analytics-workspace-page">
      <section className="analytics-workspace-hero">
        <div>
          <p className="workspace-eyebrow">Gestão e Inteligência</p>
          <h2>Analytics</h2>
          <p>
            Centraliza painéis, indicadores epidemiológicos, indicadores científicos e relatórios gerenciais em um único espaço.
          </p>
        </div>
        <div className="analytics-workspace-hero-card">
          <TrendingUp size={22} />
          <span>Indicadores integrados</span>
        </div>
      </section>

      <section className="workspace-tabs" aria-label="Áreas de analytics">
        {ABAS.map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.key}
              type="button"
              className={abaAtiva === item.key ? "active" : ""}
              onClick={() => setAbaAtiva(item.key)}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </section>

      <section className="analytics-workspace-contexto">
        <strong>{aba.label}</strong>
        <span>{aba.descricao}</span>
      </section>

      <section className="workspace-panel analytics-workspace-panel">
        {renderConteudo()}
      </section>
    </div>
  );
}
