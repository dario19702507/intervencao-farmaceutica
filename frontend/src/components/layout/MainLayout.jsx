import { useState } from "react";
import RouteTelemetry from "../router/RouteTelemetry";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

export default function MainLayout({ children, usuario, sair }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="app-shell">
      <RouteTelemetry usuario={usuario} />
      <Sidebar usuario={usuario} open={open} setOpen={setOpen} />

      <main className="main-content">
        <Topbar usuario={usuario} sair={sair} />
        <section className="content-card">{children}</section>
      </main>
    </div>
  );
}
