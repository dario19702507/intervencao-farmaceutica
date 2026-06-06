export default function Dashboard() {
  return (
    <div>
      <h2>Dashboard</h2>
      <p className="muted">Visão geral dos serviços rápidos e do consultório farmacêutico.</p>

      <div className="cards-grid">
        <div className="metric-card">
          <span>Serviços rápidos</span>
          <strong>—</strong>
          <p>Aguardando integração com API</p>
        </div>

        <div className="metric-card">
          <span>Pacientes clínicos</span>
          <strong>—</strong>
          <p>Aguardando integração com API</p>
        </div>

        <div className="metric-card">
          <span>Alertas pendentes</span>
          <strong>—</strong>
          <p>Aguardando integração com API</p>
        </div>
      </div>
    </div>
  );
}