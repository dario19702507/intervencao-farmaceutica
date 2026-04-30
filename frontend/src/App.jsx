import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import './style.css';

const API = import.meta.env.VITE_API_URL;
const hoje = new Date().toISOString().slice(0, 10);

function authHeaders() {
  return {
    Authorization: `Bearer ${localStorage.getItem('token')}`,
    'Content-Type': 'application/json',
  };
}

function objToChart(obj) {
  return Object.entries(obj || {}).map(([name, value]) => ({ name, value }));
}

function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [me, setMe] = useState(null);
  const [email, setEmail] = useState('admin@farmacia.local');
  const [password, setPassword] = useState('admin123');
  const [op, setOp] = useState(null);
  const [indic, setIndic] = useState(null);
  const [lista, setLista] = useState([]);
  const [usuarios, setUsuarios] = useState([]);
  const [msg, setMsg] = useState('');
  const [tab, setTab] = useState('intervencoes');

  const [novoUsuario, setNovoUsuario] = useState({
    nome: '',
    email: '',
    password: '',
    perfil: 'farmaceutico',
  });

  const [resetSenha, setResetSenha] = useState({
    user_id: '',
    password: '',
  });

  const [form, setForm] = useState({
    data_atendimento: hoje,
    paciente_nome: '',
    data_nascimento: '',
    tipo_atendimento: 'Presencial',
    motivo_atendimento: 'Documentação (inclusão/renovação/adequação)',
    comorbidade: 'Asma/DPOC',
    tipos_intervencao: ['Orientação documental'],
    resultado: 'Aceitação',
    observacoes: '',
  });

  async function login(e) {
    e.preventDefault();
    const fd = new URLSearchParams();
    fd.append('username', email);
    fd.append('password', password);

    const r = await fetch(`${API}/auth/login`, {
      method: 'POST',
      body: fd,
    });

    if (!r.ok) {
      setMsg('Login inválido');
      return;
    }

    const j = await r.json();
    localStorage.setItem('token', j.access_token);
    setToken(j.access_token);
  }

  async function load() {
    const [meRes, o, i, l] = await Promise.all([
      fetch(`${API}/me`, { headers: authHeaders() }),
      fetch(`${API}/opcoes`, { headers: authHeaders() }),
      fetch(`${API}/indicadores`, { headers: authHeaders() }),
      fetch(`${API}/intervencoes`, { headers: authHeaders() }),
    ]);

    const meJson = await meRes.json();
    setMe(meJson);
    setOp(await o.json());
    setIndic(await i.json());
    setLista(await l.json());

    if (meJson?.perfil === 'admin') {
      const u = await fetch(`${API}/users`, { headers: authHeaders() });
      setUsuarios(await u.json());
    }
  }

  useEffect(() => {
    if (token) load();
  }, [token]);

  async function salvar(e) {
    e.preventDefault();

    const r = await fetch(`${API}/intervencoes`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(form),
    });

    if (!r.ok) {
      setMsg('Erro ao salvar. Confira os campos.');
      return;
    }

    setMsg('Intervenção registrada com sucesso.');
    setForm({
      ...form,
      paciente_nome: '',
      data_nascimento: '',
      observacoes: '',
    });

    load();
  }

  async function criarUsuario(e) {
    e.preventDefault();

    const r = await fetch(`${API}/users`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(novoUsuario),
    });

    if (!r.ok) {
      setMsg('Erro ao criar usuário.');
      return;
    }

    setMsg('Usuário criado com sucesso.');
    setNovoUsuario({
      nome: '',
      email: '',
      password: '',
      perfil: 'farmaceutico',
    });

    load();
  }

async function redefinirSenha(e) {
  e.preventDefault();

  if (!resetSenha.user_id) {
    setMsg('Selecione um usuário.');
    return;
  }

  if (!resetSenha.password || resetSenha.password.length < 6) {
    setMsg('A senha deve ter pelo menos 6 caracteres.');
    return;
  }

  const r = await fetch(`${API}/users/${resetSenha.user_id}/password`, {
    method: 'PUT',
    headers: authHeaders(),
    body: JSON.stringify({ password: resetSenha.password }),
  });

  if (!r.ok) {
    setMsg('Erro ao redefinir senha.');
    return;
  }

  setMsg('Senha redefinida com sucesso.');
  setResetSenha({ user_id: '', password: '' });
  load();
}

  function toggleTipo(t) {
    const s = new Set(form.tipos_intervencao);
    s.has(t) ? s.delete(t) : s.add(t);
    setForm({ ...form, tipos_intervencao: [...s] });
  }

  if (!token) {
    return (
      <main className="login">
        <form onSubmit={login} className="card">
          <h1>Intervenção Farmacêutica</h1>
          <p>Acesso multiusuário</p>
          <input value={email} onChange={e => setEmail(e.target.value)} placeholder="e-mail" />
          <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="senha" />
          <button>Entrar</button>
          <small>Usuário inicial: admin@farmacia.local / admin123</small>
          {msg && <b>{msg}</b>}
        </form>
      </main>
    );
  }

  return (
    <main>
      <header>
        <div>
          <h1>Sistema de Intervenção Farmacêutica</h1>
          <p>Coleta de dados, acompanhamento e indicadores assistenciais</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={() => setTab('intervencoes')}>Intervenções</button>
	  <button onClick={() => {
	    window.open(`${API}/intervencoes/exportar/csv`, '_blank');
	  }}>
 	    Exportar CSV
	   </button>
          {me?.perfil === 'admin' && <button onClick={() => setTab('admin')}>Administração</button>}
          <button onClick={() => { localStorage.clear(); setToken(''); }}>Sair</button>
        </div>
      </header>

      {msg && <div className="alert">{msg}</div>}

      {tab === 'intervencoes' && (
        <>
          <section className="grid">
            <form className="card" onSubmit={salvar}>
              <h2>Nova intervenção</h2>

              <label>Data de atendimento
                <input type="date" required value={form.data_atendimento} onChange={e => setForm({ ...form, data_atendimento: e.target.value })} />
              </label>

              <label>Paciente
                <input required value={form.paciente_nome} onChange={e => setForm({ ...form, paciente_nome: e.target.value.toUpperCase() })} placeholder="NOME COMPLETO" />
              </label>

              <label>Data de nascimento
                <input type="date" required value={form.data_nascimento} onChange={e => setForm({ ...form, data_nascimento: e.target.value })} />
              </label>

              <label>Tipo de atendimento
                <select value={form.tipo_atendimento} onChange={e => setForm({ ...form, tipo_atendimento: e.target.value })}>
                  {op?.tipos_atendimento?.map(x => <option key={x}>{x}</option>)}
                </select>
              </label>

              <label>Motivo
                <select value={form.motivo_atendimento} onChange={e => setForm({ ...form, motivo_atendimento: e.target.value })}>
                  {op?.motivos?.map(x => <option key={x}>{x}</option>)}
                </select>
              </label>

              <label>Comorbidade
                <select value={form.comorbidade} onChange={e => setForm({ ...form, comorbidade: e.target.value })}>
                  {op?.comorbidades?.map(x => <option key={x}>{x}</option>)}
                </select>
              </label>

              <fieldset>
                <legend>Tipo de intervenção</legend>
                {op?.tipos_intervencao?.map(t => (
                  <label className="check" key={t}>
                    <input type="checkbox" checked={form.tipos_intervencao.includes(t)} onChange={() => toggleTipo(t)} />
                    {t}
                  </label>
                ))}
              </fieldset>

              <label>Resultado
                <select value={form.resultado} onChange={e => setForm({ ...form, resultado: e.target.value })}>
                  {op?.resultados?.map(x => <option key={x}>{x}</option>)}
                </select>
              </label>

              <label>Observações
                <textarea value={form.observacoes} onChange={e => setForm({ ...form, observacoes: e.target.value })} />
              </label>

              <button>Salvar intervenção</button>
            </form>

            <section className="card">
              <h2>Indicadores</h2>
              <div className="kpis">
                <strong>{indic?.total_intervencoes || 0}<span>intervenções</span></strong>
                <strong>{indic?.total_pacientes || 0}<span>pacientes</span></strong>
              </div>

              <Chart title="Por tipo de intervenção" data={objToChart(indic?.por_tipo_intervencao)} />
              <Chart title="Por resultado" data={objToChart(indic?.por_resultado)} />
              <Chart title="Por comorbidade" data={objToChart(indic?.por_comorbidade)} />
            </section>
          </section>

          <section className="card">
            <h2>Registros recentes</h2>
            <table>
              <thead>
                <tr>
                  <th>Data</th>
                  <th>Paciente</th>
                  <th>Comorbidade</th>
                  <th>Intervenção</th>
                  <th>Resultado</th>
                  <th>Profissional</th>
                </tr>
              </thead>
              <tbody>
                {lista.map(r => (
                  <tr key={r.id}>
                    <td>{r.data_atendimento}</td>
                    <td>{r.paciente_nome}</td>
                    <td>{r.comorbidade}</td>
                    <td>{r.tipos_intervencao.join(', ')}</td>
                    <td>{r.resultado}</td>
                    <td>{r.profissional}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        </>
      )}

      {tab === 'admin' && me?.perfil === 'admin' && (
        <section className="grid">
          <form className="card" onSubmit={criarUsuario}>
            <h2>Novo usuário</h2>
            <label>Nome<input value={novoUsuario.nome} onChange={e => setNovoUsuario({ ...novoUsuario, nome: e.target.value })} /></label>
            <label>E-mail<input value={novoUsuario.email} onChange={e => setNovoUsuario({ ...novoUsuario, email: e.target.value })} /></label>
            <label>Senha<input type="password" value={novoUsuario.password} onChange={e => setNovoUsuario({ ...novoUsuario, password: e.target.value })} /></label>
            <label>Perfil
              <select value={novoUsuario.perfil} onChange={e => setNovoUsuario({ ...novoUsuario, perfil: e.target.value })}>
                <option value="admin">admin</option>
                <option value="farmaceutico">farmaceutico</option>
                <option value="leitor">leitor</option>
              </select>
            </label>
            <button>Criar usuário</button>
          </form>

          <form className="card" onSubmit={redefinirSenha}>
            <h2>Redefinir senha</h2>
            <label>Usuário
              <select value={resetSenha.user_id} onChange={e => setResetSenha({ ...resetSenha, user_id: e.target.value })}>
                <option value="">Selecione</option>
                {usuarios.map(u => <option key={u.id} value={u.id}>{u.nome} ({u.email})</option>)}
              </select>
            </label>
            <label>Nova senha<input type="password" value={resetSenha.password} onChange={e => setResetSenha({ ...resetSenha, password: e.target.value })} /></label>
            <button>Redefinir senha</button>
          </form>

          <section className="card">
            <h2>Usuários cadastrados</h2>
            <table>
              <thead>
                <tr>
                  <th>Nome</th>
                  <th>E-mail</th>
                  <th>Perfil</th>
                </tr>
              </thead>
              <tbody>
                {usuarios.map(u => (
                  <tr key={u.id}>
                    <td>{u.nome}</td>
                    <td>{u.email}</td>
                    <td>{u.perfil}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        </section>
      )}
    </main>
  );
}

function Chart({ title, data }) {
  return (
    <div className="chart">
      <h3>{title}</h3>
      <ResponsiveContainer width="100%" height={210}>
        <BarChart data={data}>
          <XAxis dataKey="name" hide />
          <YAxis allowDecimals={false} />
          <Tooltip />
          <Bar dataKey="value" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

createRoot(document.getElementById('root')).render(<App />);