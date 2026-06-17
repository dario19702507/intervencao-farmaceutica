import { useEffect, useMemo, useState } from "react";
import { CalendarDays, BellRing, Pill, AlertTriangle, LayoutDashboard, RefreshCw } from "lucide-react";
import AgendaAlertas from "./AgendaAlertas.jsx";
import AgendaIntegrada from "./AgendaIntegrada.jsx";
import CatalogoMedicamentos from "./CatalogoMedicamentos.jsx";
import ConciliacaoCeaf from "./ConciliacaoCeaf.jsx";
import NotificacoesWhatsapp from "../notificacoes/NotificacoesWhatsapp.jsx";
import "./AgendaWorkspace.css";

const TABS = [
  {
    key: "visao-geral",
    label: "Visão Geral",
    icon: LayoutDashboard,
    description: "Retornos, alertas e visão rápida da agenda.",
  },
  {
    key: "agenda",
    label: "Agenda",
    icon: CalendarDays,
    description: "Eventos, capacidade, reagendamentos e sugestões de datas.",
  },
  {
    key: "conciliacao-ceaf",
    label: "Conciliação CEAF",
    icon: RefreshCw,
    description: "Sincroniza retiradas mensais CEAF, bloqueios por LME vencida e pendências de renovação.",
  },
  {
    key: "notificacoes",
    label: "Notificações",
    icon: BellRing,
    description: "Notificações internas e comunicação operacional.",
  },
  {
    key: "whatsapp",
    label: "WhatsApp",
    icon: BellRing,
    description: "Fila de WhatsApp, envio manual e monitoramento.",
  },
  {
    key: "catalogo",
    label: "Catálogo",
    icon: Pill,
    description: "Catálogo simplificado de medicamentos para padronização farmacoterapêutica.",
  },
];

const LEGACY_TAB_BY_HASH = {
  "#visao-geral": "visao-geral",
  "#agenda": "agenda",
  "#eventos": "agenda",
  "#conciliacao-ceaf": "conciliacao-ceaf",
  "#conciliacao": "conciliacao-ceaf",
  "#notificacoes": "notificacoes",
  "#whatsapp": "whatsapp",
  "#catalogo": "catalogo",
  "#medicamentos": "catalogo",
};

function getInitialTab() {
  const params = new URLSearchParams(window.location.search);
  const tab = params.get("tab");
  if (TABS.some((item) => item.key === tab)) return tab;
  return LEGACY_TAB_BY_HASH[window.location.hash] || "visao-geral";
}

export default function AgendaWorkspace({ setActivePage }) {
  const [aba, setAba] = useState(getInitialTab);

  const tabAtual = useMemo(() => TABS.find((item) => item.key === aba) || TABS[0], [aba]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    params.set("tab", aba);
    const novoUrl = `${window.location.pathname}?${params.toString()}`;
    window.history.replaceState(null, "", novoUrl);
  }, [aba]);

  function renderConteudo() {
    if (aba === "agenda") return <AgendaIntegrada setActivePage={setActivePage} />;
    if (aba === "conciliacao-ceaf") return <ConciliacaoCeaf setActivePage={setActivePage} />;
    if (aba === "notificacoes") return <NotificacoesWhatsapp setActivePage={setActivePage} abaInicial="notificacoes" />;
    if (aba === "whatsapp") return <NotificacoesWhatsapp setActivePage={setActivePage} abaInicial="whatsapp" />;
    if (aba === "catalogo") return <CatalogoMedicamentos setActivePage={setActivePage} />;
    return <AgendaAlertas setActivePage={setActivePage} />;
  }

  return (
    <div className="agenda-workspace-page">
      <section className="workspace-hero">
        <div>
          <p className="eyebrow">Agenda e Comunicação</p>
          <h1>Agenda</h1>
          <p>
            Retornos, alertas, notificações, WhatsApp e catálogo de medicamentos reunidos em uma única área de trabalho.
          </p>
        </div>
        <div className="workspace-hero-card">
          <AlertTriangle size={20} />
          <span>Use as abas para alternar entre operação diária, comunicação e apoio medicamentoso.</span>
        </div>
      </section>

      <nav className="workspace-tabs" aria-label="Áreas da agenda">
        {TABS.map((tab) => {
          const Icon = tab.icon;
          const ativo = aba === tab.key;
          return (
            <button
              key={tab.key}
              type="button"
              className={ativo ? "workspace-tab active" : "workspace-tab"}
              onClick={() => setAba(tab.key)}
              aria-pressed={ativo}
            >
              <Icon size={18} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </nav>

      <section className="workspace-context">
        <strong>{tabAtual.label}</strong>
        <span>{tabAtual.description}</span>
      </section>

      <section className="workspace-content">{renderConteudo()}</section>
    </div>
  );
}
