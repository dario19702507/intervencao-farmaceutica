import { useState } from "react";
import { api } from "../api/api";
import { LockKeyhole, UserRound } from "lucide-react";

export default function Login({ onLogin }) {
  const [email, setEmail] = useState("admin@farmacia.local");
  const [senha, setSenha] = useState("admin123");
  const [loading, setLoading] = useState(false);

  async function entrar(e) {
  e.preventDefault();

  try {
    setLoading(true);

    const formData = new URLSearchParams();
    formData.append("grant_type", "password");
    formData.append("username", email);
    formData.append("password", senha);
    formData.append("scope", "");
    formData.append("client_id", "string");
    formData.append("client_secret", "string");

    const response = await api.post("/auth/login", formData, {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
    });

    const token = response.data.access_token;

    if (!token) {
      alert("Token não retornado pelo servidor.");
      return;
    }

    localStorage.setItem("token", token);
    localStorage.setItem("usuario_email", email);

    onLogin({
      email,
      perfil: "carregando",
      categoria_profissional: "carregando",
    });
  } catch (error) {
    console.error("Erro no login:", error);
    alert("Erro ao fazer login. Verifique usuário e senha.");
  } finally {
    setLoading(false);
  }
}

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-brand">
          <div className="login-logo-stack">
            <img src="/logos/farmacia_escola.png" alt="Farmácia Escola UFMS" />
            <img src="/logos/ufms.png" alt="UFMS" />
          </div>

          <h1>Sistema Integrado de Atenção Farmacêutica</h1>
          <p>Farmácia Escola UFMS · Consultório Farmacêutico e Prontuário Clínico</p>
        </div>

        <form onSubmit={entrar} className="login-form">
          <label>
            <span>E-mail</span>
            <div className="login-input-wrap">
              <UserRound size={18} />
              <input
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="seu@email.com"
              />
            </div>
          </label>

          <label>
            <span>Senha</span>
            <div className="login-input-wrap">
              <LockKeyhole size={18} />
              <input
                type="password"
                value={senha}
                onChange={(e) => setSenha(e.target.value)}
                placeholder="Senha"
              />
            </div>
          </label>

          <button className="login-button" disabled={loading}>
            {loading ? "Entrando..." : "Entrar no sistema"}
          </button>
        </form>

        <p className="login-footer">
          Farmácia Escola Profa. Ana Maria Cervantes Baraza · UFMS
        </p>
      </div>
    </div>
  );
}
