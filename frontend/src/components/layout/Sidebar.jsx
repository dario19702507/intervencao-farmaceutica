import {
  LayoutDashboard,
  Activity,
  Stethoscope,
  CalendarDays,
  FileText,
  Menu,
  X,
  AlertTriangle,
  BarChart3,
  UserCog,
  Microscope,
  Users
} from "lucide-react";

const items = [
  { key: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { key: "servicos", label: "Serviços Rápidos", icon: Activity },
  { key: "consultorio", label: "Consultório", icon: Stethoscope },
  { key: "agenda", label: "Agenda e Alertas", icon: CalendarDays,},
  { key: "agenda-integrada", label: "Agenda Integrada", icon: CalendarDays,},
  { key: "pacientes", label: "Pacientes", icon: Users },
  { key: "relatorios", label: "Relatórios", icon: FileText },
  { key: "fila-clinica", label: "Fila Clínica", icon: AlertTriangle },
  { key: "dashboard-epidemiologico", label: "Dashboard Epidemiológico",icon: BarChart3,},
  { key: "perfil-profissional", label: "Perfil Profissional", icon: UserCog,},
  { key: "indicadores-cientificos", label: "Indicadores Científicos", icon: Microscope,},
];



export default function Sidebar({ activePage, setActivePage, open, setOpen }) {
  return (
    <>
      <button className="mobile-menu-button" onClick={() => setOpen(true)}>
        <Menu size={22} />
      </button>

      <aside className={`sidebar ${open ? "open" : ""}`}>
        <div className="sidebar-header">
          <div>
            <h2>Farmácia Escola</h2>
            <span>Consultório Farmacêutico</span>
          </div>
          <button className="close-sidebar" onClick={() => setOpen(false)}>
            <X size={20} />
          </button>
        </div>

        <nav className="sidebar-nav">
          {items.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.key}
                className={`nav-item ${activePage === item.key ? "active" : ""}`}
                onClick={() => {
                  setActivePage(item.key);
                  setOpen(false);
                }}
              >
                <Icon size={20} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </aside>

      {open && <div className="overlay" onClick={() => setOpen(false)} />}
    </>
  );
}