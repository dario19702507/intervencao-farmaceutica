import { Suspense, useEffect, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { api } from "./api/api";
import MainLayout from "./components/layout/MainLayout";
import AppRoute from "./components/router/AppRoute";
import RequireAuth from "./components/router/RequireAuth";
import { LEGACY_REDIRECTS, ROUTES } from "./navigation/catalog.jsx";
import "./style.css";

function LoadingPage() {
  return (
    <div className="loading-page">
      <div className="loading-card">Carregando módulo...</div>
    </div>
  );
}

export default function App() {
  const [usuario, setUsuario] = useState(() => {
    const token = localStorage.getItem("token");
    const email = localStorage.getItem("usuario_email");

    if (token && email) {
      return { email, perfil: "carregando", categoria_profissional: "carregando" };
    }

    return null;
  });

  useEffect(() => {
    async function carregarUsuarioLogado() {
      const token = localStorage.getItem("token");

      if (!token) return;

      try {
        const response = await api.get("/me");

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

  return (
    <RequireAuth usuario={usuario} setUsuario={setUsuario}>
      <MainLayout usuario={usuario} sair={sair}>
        <Suspense fallback={<LoadingPage />}>
          <Routes>
            {ROUTES.map((route) => (
              <Route
                key={route.key}
                path={route.path}
                element={<AppRoute route={route} usuario={usuario} />}
              />
            ))}

            {LEGACY_REDIRECTS.map((redirect) => (
              <Route
                key={`${redirect.from}->${redirect.to}`}
                path={redirect.from}
                element={<Navigate to={redirect.to} replace />}
              />
            ))}

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </MainLayout>
    </RequireAuth>
  );
}
