import { LogOut } from "lucide-react";
import { useLocation } from "react-router-dom";
import { findRouteByPath } from "../../navigation/catalog.jsx";

export default function Topbar({ usuario, sair }) {
  const location = useLocation();
  const pageInfo = findRouteByPath(location.pathname);

  return (
    <header className="topbar institutional-topbar">
      <div className="topbar-brand-block">
        <div className="institutional-logos compact">
          <img src="/logos/farmacia_escola.png" alt="Farmácia Escola UFMS" />
          <img src="/logos/ufms.png" alt="UFMS" />
        </div>
        <div>
          <h1>{pageInfo.title}</h1>
          <p>{pageInfo.subtitle}</p>
        </div>
      </div>

      <div className="topbar-actions">
        <div className="user-chip">
          <span className="status-dot" />
          {usuario?.nome || usuario?.email || "Usuário"}
        </div>

        <span className="profile-chip">
          {usuario?.perfil || "sem perfil"} · {usuario?.categoria_profissional || "sem categoria"}
        </span>

        <button className="logout-button" onClick={sair}>
          <LogOut size={17} />
          Sair
        </button>
      </div>
    </header>
  );
}
