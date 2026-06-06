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

    const response = await fetch("http://127.0.0.1:8000/auth/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        "accept": "application/json",
      },
      body: formData.toString(),
    });

    const data = await response.json();

    if (!response.ok) {
      console.error("Erro no login:", data);
      alert("Erro ao fazer login.");
      return;
    }

    const token = data.access_token;

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
          <div className="login-icon">
            <LockKeyhole size={30} />
          </div>

          <h1>Farmácia Escola</h1>
          <p>Consultório Farmacêutico e Prontuário Clínico</p>
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
          Sistema de cuidado farmacêutico · ambiente de desenvolvimento
        </p>
      </div>
    </div>
  );
}