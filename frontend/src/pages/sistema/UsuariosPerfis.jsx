import { useEffect, useMemo, useState } from "react";
import { api } from "../../api/api";

const PERFIS = [
  { value: "admin", label: "Administrador" },
  { value: "farmaceutico", label: "Farmacêutico" },
  { value: "estagiario", label: "Estagiário" },
  { value: "pesquisador", label: "Pesquisador" },
  { value: "visualizacao", label: "Leitura" },
];

const CATEGORIAS = ["Farmacêutico", "Docente", "Residente", "Estagiário", "Técnico", "Pesquisador", "Administrativo"];
const MODULOS = [
  ["intervencoes", "Intervenções"],
  ["consultorio", "Consultório"],
  ["documentos", "Documentos"],
  ["relatorios", "Relatórios"],
  ["agenda", "Agenda"],
  ["administracao", "Administração"],
];

const ESTADO_INICIAL = {
  nome: "",
  email: "",
  password: "",
  perfil: "farmaceutico",
  categoria_profissional: "Farmacêutico",
};

function perfilLabel(perfil) {
  return PERFIS.find((item) => item.value === perfil)?.label || perfil || "Não informado";
}

function permissaoTexto(permissao) {
  if (!permissao?.ver) return "Sem acesso";
  if (permissao?.editar) return "Ver e editar";
  return "Somente leitura";
}

export default function UsuariosPerfis() {
  const [usuarios, setUsuarios] = useState([]);
  const [form, setForm] = useState(ESTADO_INICIAL);
  const [selecionado, setSelecionado] = useState(null);
  const [carregando, setCarregando] = useState(false);
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState("");
  const [mensagem, setMensagem] = useState("");

  useEffect(() => {
    carregarUsuarios();
  }, []);

  async function carregarUsuarios() {
    try {
      setCarregando(true);
      setErro("");
      const response = await api.get("/users");
      setUsuarios(response.data || []);
    } catch (error) {
      console.error("Erro ao carregar usuários:", error.response?.data || error);
      setErro("Não foi possível carregar usuários. Confirme se seu perfil é administrador.");
    } finally {
      setCarregando(false);
    }
  }

  function limparFormulario() {
    setSelecionado(null);
    setForm(ESTADO_INICIAL);
    setErro("");
    setMensagem("");
  }

  function editarUsuario(usuario) {
    setSelecionado(usuario);
    setForm({
      nome: usuario.nome || "",
      email: usuario.email || "",
      password: "",
      perfil: usuario.perfil || "farmaceutico",
      categoria_profissional: usuario.categoria_profissional || "Farmacêutico",
    });
    setErro("");
    setMensagem("");
  }

  async function salvarUsuario(event) {
    event.preventDefault();
    setErro("");
    setMensagem("");

    if (!form.nome.trim() || !form.email.trim()) {
      setErro("Informe nome e e-mail do usuário.");
      return;
    }

    if (!selecionado && form.password.length < 6) {
      setErro("Informe uma senha inicial com pelo menos 6 caracteres.");
      return;
    }

    try {
      setSalvando(true);

      if (selecionado) {
        await api.put(`/users/${selecionado.id}`, {
          nome: form.nome,
          email: form.email,
          perfil: form.perfil,
          categoria_profissional: form.categoria_profissional,
        });
      } else {
        await api.post("/users", form);
      }

      setMensagem(selecionado ? "Usuário atualizado com sucesso." : "Usuário criado com sucesso.");
      limparFormulario();
      await carregarUsuarios();
    } catch (error) {
      console.error("Erro ao salvar usuário:", error.response?.data || error);
      setErro(error.response?.data?.detail || "Não foi possível salvar o usuário.");
    } finally {
      setSalvando(false);
    }
  }

  async function redefinirSenha(usuario) {
    const novaSenha = window.prompt(`Nova senha para ${usuario.nome}. Use pelo menos 6 caracteres:`);
    if (!novaSenha) return;
    if (novaSenha.length < 6) {
      setErro("A nova senha deve ter pelo menos 6 caracteres.");
      return;
    }

    try {
      setErro("");
      setMensagem("");
      await api.put(`/users/${usuario.id}/password`, { password: novaSenha });
      setMensagem("Senha redefinida com sucesso.");
    } catch (error) {
      console.error("Erro ao redefinir senha:", error.response?.data || error);
      setErro(error.response?.data?.detail || "Não foi possível redefinir a senha.");
    }
  }

  const usuarioSelecionado = useMemo(
    () => usuarios.find((usuario) => usuario.id === selecionado?.id) || selecionado,
    [usuarios, selecionado]
  );

  return (
    <div>
      <h2>Usuários e Perfis</h2>
      <p className="muted">
        Cadastro único para Intervenções, Consultório, Documentos, Agenda, Relatórios e Administração.
        As permissões são consolidadas pelo perfil do usuário, evitando múltiplos logins.
      </p>

      {erro && <div className="alert-card warning">{erro}</div>}
      {mensagem && <div className="alert-card success">{mensagem}</div>}

      <form className="form-card" onSubmit={salvarUsuario}>
        <h3>{selecionado ? "Editar usuário" : "Novo usuário"}</h3>

        <div className="form-grid two-columns">
          <label>
            Nome
            <input
              className="input"
              value={form.nome}
              onChange={(e) => setForm({ ...form, nome: e.target.value })}
              placeholder="Nome completo"
            />
          </label>

          <label>
            E-mail
            <input
              className="input"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              placeholder="usuario@instituicao.br"
              type="email"
            />
          </label>

          {!selecionado && (
            <label>
              Senha inicial
              <input
                className="input"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                placeholder="Senha temporária"
                type="password"
              />
            </label>
          )}

          <label>
            Perfil
            <select
              className="input"
              value={form.perfil}
              onChange={(e) => setForm({ ...form, perfil: e.target.value })}
            >
              {PERFIS.map((perfil) => (
                <option key={perfil.value} value={perfil.value}>{perfil.label}</option>
              ))}
            </select>
          </label>

          <label>
            Categoria profissional
            <select
              className="input"
              value={form.categoria_profissional}
              onChange={(e) => setForm({ ...form, categoria_profissional: e.target.value })}
            >
              {CATEGORIAS.map((categoria) => (
                <option key={categoria} value={categoria}>{categoria}</option>
              ))}
            </select>
          </label>
        </div>

        <div className="button-row">
          <button className="primary-button" type="submit" disabled={salvando}>
            {salvando ? "Salvando..." : selecionado ? "Salvar alterações" : "Criar usuário"}
          </button>
          {selecionado && (
            <button className="secondary-button" type="button" onClick={limparFormulario}>
              Cancelar edição
            </button>
          )}
        </div>
      </form>

      {usuarioSelecionado?.permissoes && (
        <div className="table-card">
          <table className="data-table">
            <thead>
              <tr>
                <th colSpan="3">Matriz de permissões do perfil: {perfilLabel(usuarioSelecionado.perfil)}</th>
              </tr>
              <tr>
                <th>Módulo</th>
                <th>Permissão</th>
                <th>Interpretação operacional</th>
              </tr>
            </thead>
            <tbody>
              {MODULOS.map(([key, label]) => (
                <tr key={key}>
                  <td>{label}</td>
                  <td><span className="badge">{permissaoTexto(usuarioSelecionado.permissoes[key])}</span></td>
                  <td>{usuarioSelecionado.permissoes[key]?.editar ? "Pode registrar e alterar dados." : usuarioSelecionado.permissoes[key]?.ver ? "Pode consultar, sem alterar." : "Sem acesso ao módulo."}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="table-card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Nome</th>
              <th>E-mail</th>
              <th>Perfil</th>
              <th>Categoria</th>
              <th>Ações</th>
            </tr>
          </thead>
          <tbody>
            {carregando && (
              <tr><td colSpan="5">Carregando usuários...</td></tr>
            )}
            {!carregando && usuarios.length === 0 && (
              <tr><td colSpan="5">Nenhum usuário encontrado.</td></tr>
            )}
            {usuarios.map((usuario) => (
              <tr key={usuario.id}>
                <td>{usuario.nome}</td>
                <td>{usuario.email}</td>
                <td><span className="badge">{perfilLabel(usuario.perfil)}</span></td>
                <td>{usuario.categoria_profissional || "-"}</td>
                <td>
                  <div className="table-actions">
                    <button className="secondary-button" type="button" onClick={() => editarUsuario(usuario)}>
                      Editar
                    </button>
                    <button className="secondary-button" type="button" onClick={() => redefinirSenha(usuario)}>
                      Senha
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
