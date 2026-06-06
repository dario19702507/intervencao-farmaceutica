import { useState } from "react";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

export default function MainLayout({
  children,
  activePage,
  setActivePage,
  usuario,
  sair,
}) {
  const [open, setOpen] = useState(false);

  return (
    <div className="app-shell">
      <Sidebar
        activePage={activePage}
        setActivePage={setActivePage}
        open={open}
        setOpen={setOpen}
      />

      <main className="main-content">
        <Topbar usuario={usuario} sair={sair} />
        <section className="content-card">{children}</section>
      </main>
    </div>
  );
}