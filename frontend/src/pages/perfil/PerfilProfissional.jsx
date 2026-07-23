import { useEffect, useState } from "react";
import { api } from "../../api/api";

export default function PerfilProfissional() {
  const [perfil, setPerfil] = useState({
    nome_completo: "",
    crf: "",
    assinatura_digital: "",
    categoria_profissional: "",
    email: "",
  });

  const [salvando, setSalvando] = useState(false);

  useEffect(() => {
    carregarPerfil();
  }, []);

  async function carregarPerfil() {
    try {
      const response = await api.get("/consultorio/me/perfil-profissional");

      setPerfil({
        nome_completo: response.data.nome_completo || "",
        crf: response.data.crf || "",
        assinatura_digital: response.data.assinatura_digital || "",
        categoria_profissional: response.data.categoria_profissional || "",
        email: response.data.email || "",
      });
    } catch (error) {
      console.error("Erro ao carregar perfil:", error);
    }
  }

  async function salvarPerfil() {
    try {
      setSalvando(true);

      await api.put("/consultorio/me/perfil-profissional", {
        nome_completo: perfil.nome_completo,
        crf: perfil.crf,
        assinatura_digital: perfil.assinatura_digital,
      });

      await carregarPerfil();

      alert("Perfil profissional atualizado com sucesso.");
    } catch (error) {
      console.error("Erro ao salvar perfil:", error.response?.data || error);
      alert("Erro ao salvar perfil profissional.");
    } finally {
      setSalvando(false);
    }
  }

  return (
    <div>
      <h2>Perfil Profissional</h2>

      <p className="muted">
        Dados utilizados na identificação institucional e assinatura dos documentos.
      </p>

      <div className="form-card">
        <input
          className="input"
          placeholder="Nome completo"
          value={perfil.nome_completo}
          onChange={(e) =>
            setPerfil({ ...perfil, nome_completo: e.target.value })
          }
        />

        <input
          className="input"
          placeholder="CRF"
          value={perfil.crf}
          onChange={(e) =>
            setPerfil({ ...perfil, crf: e.target.value })
          }
        />

        <input
          className="input"
          placeholder="Categoria profissional"
          value={perfil.categoria_profissional}
          readOnly
        />

        <input
          className="input"
          placeholder="E-mail"
          value={perfil.email}
          readOnly
        />

        <textarea
          className="textarea"
          placeholder="Assinatura digital textual"
          value={perfil.assinatura_digital}
          onChange={(e) =>
            setPerfil({
              ...perfil,
              assinatura_digital: e.target.value,
            })
          }
        />

        <button
          className="primary-button"
          onClick={salvarPerfil}
          disabled={salvando}
        >
          {salvando ? "Salvando..." : "Salvar perfil profissional"}
        </button>
      </div>
    </div>
  );
}