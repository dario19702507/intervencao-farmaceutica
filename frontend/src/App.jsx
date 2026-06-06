import { useEffect, useState } from "react";
import { api } from "./api/api";
import MainLayout from "./components/layout/MainLayout";
import Dashboard from "./pages/dashboard/Dashboard";
import ServicosRapidos from "./pages/servicos/ServicosRapidos";
import Consultorio from "./pages/consultorio/Consultorio";
import AgendaAlertas from "./pages/agenda/AgendaAlertas";
import Relatorios from "./pages/relatorios/Relatorios";
import Login from "./pages/Login";
import "./style.css";
import FilaClinica from "./pages/fila/FilaClinica";
import DashboardEpidemiologico from "./pages/dashboard/DashboardEpidemiologico";
import PerfilProfissional from "./pages/perfil/PerfilProfissional";
import IndicadoresCientificos from "./pages/cientifico/IndicadoresCientificos.jsx";
import AgendaIntegrada from "./pages/agenda/AgendaIntegrada";
import Pacientes from "./pages/pacientes/Pacientes";

export default function App() {
  const [usuario, setUsuario] = useState(() => {
    const token = localStorage.getItem("token");
    const email = localStorage.getItem("usuario_email");

    if (token && email) {
      return { email };
    }

    return null;
  });

  const [activePage, setActivePage] = useState("dashboard");

  useEffect(() => {
    async function carregarUsuarioLogado() {
      const token = localStorage.getItem("token");

      if (!token) return;

      try {
        const response = await api.get("/consultorio/me");

        setUsuario({
          email: response.data.email,
          nome: response.data.nome,
          perfil: response.data.perfil,
          categoria_profissional: response.data.categoria_profissional,
        });
      } catch (error) {
        console.error("Erro ao carregar usuário logado:", error);
        localStorage.removeItem("token");
        localStorage.removeItem("usuario_email");
        setUsuario(null);
      }
    }

    carregarUsuarioLogado();
  }, []);

  function sair() {
    localStorage.removeItem("token");
    localStorage.removeItem("usuario_email");
    setUsuario(null);
  }

  const renderPage = () => {
    switch (activePage) {
      case "servicos":
        return <ServicosRapidos setActivePage={setActivePage} />;
      case "consultorio":
        return <Consultorio usuario={usuario} />;
      case "agenda":
        return <AgendaAlertas />;
      case "agenda-integrada":
        return <AgendaIntegrada />;
      case "pacientes":
        return <Pacientes />;
      case "relatorios":
        return <Relatorios />;
      case "fila-clinica":
        return <FilaClinica setActivePage={setActivePage} />;
      case "dashboard-epidemiologico":
        return <DashboardEpidemiologico />;
      case "perfil-profissional":
        return <PerfilProfissional />;
      case "indicadores-cientificos":
        return <IndicadoresCientificos />;  
      default:
        return <Dashboard setActivePage={setActivePage} />;
    }
  };

  if (!usuario) {
    return <Login onLogin={setUsuario} />;
  }

  return (
    <MainLayout
      activePage={activePage}
      setActivePage={setActivePage}
      usuario={usuario}
      sair={sair}
    >
      {renderPage()}
    </MainLayout>
  )  
}