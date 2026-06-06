import { LogOut } from "lucide-react";

export default function Topbar({ usuario, sair }) {
  return (
    <header className="topbar">
      <div>
        <h1>Sistema de Cuidado Farmacêutico</h1>
        <p>Serviços rápidos, prontuário clínico e indicadores do consultório.</p>
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