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

function tendenciaToChart(obj) {
  return Object.entries(obj || {})
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([mes, valores]) => ({
      mes,
      intervencoes: valores.intervencoes || 0,
      taxa_aceitacao: valores.taxa_aceitacao || 0,
      taxa_acompanhamento: valores.taxa_acompanhamento || 0,
      taxa_encaminhamento: valores.taxa_encaminhamento || 0,
    }));
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
  const [editandoId, setEditandoId] = useState(null);
  const [profissionais, setProfissionais] = useState([]);
  const [filtros, setFiltros] = useState({
  periodo: 'mes',
  data_inicio: '',
  data_fim: '',
  categoria_profissional: '',
});

  const [novoUsuario, setNovoUsuario] = useState({
  nome: '',
  email: '',
  password: '',
  perfil: 'farmaceutico',
  categoria_profissional: 'Farmacêutico',
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

async function exportarCSV() {
  const query = montarQuery();

  const r = await fetch(`${API}/intervencoes/exportar/csv${query}`, {
    headers: authHeaders(),
  });

  if (!r.ok) {
    setMsg('Erro ao exportar CSV.');
    return;
  }

  const blob = await r.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');

  a.href = url;
  a.download = 'intervencoes_farmaceuticas_filtradas.csv';
  document.body.appendChild(a);
  a.click();

  a.remove();
  window.URL.revokeObjectURL(url);
}
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

function montarQuery() {
  const params = new URLSearchParams();
  const hoje = new Date();
  let inicio = '';
  let fim = '';

  if (filtros.periodo === 'semana') {
    const d = new Date(hoje);
    d.setDate(hoje.getDate() - 7);
    inicio = d.toISOString().slice(0, 10);
    fim = hoje.toISOString().slice(0, 10);
  }

  if (filtros.periodo === 'quinzena') {
    const d = new Date(hoje);
    d.setDate(hoje.getDate() - 15);
    inicio = d.toISOString().slice(0, 10);
    fim = hoje.toISOString().slice(0, 10);
  }

  if (filtros.periodo === 'mes') {
    inicio = new Date(hoje.getFullYear(), hoje.getMonth(), 1).toISOString().slice(0, 10);
    fim = hoje.toISOString().slice(0, 10);
  }

  if (filtros.periodo === 'ano') {
    inicio = new Date(hoje.getFullYear(), 0, 1).toISOString().slice(0, 10);
    fim = hoje.toISOString().slice(0, 10);
  }

  if (filtros.periodo === 'customizado') {
    inicio = filtros.data_inicio;
    fim = filtros.data_fim;
  }

  if (inicio) params.append('data_inicio', inicio);
  if (fim) params.append('data_fim', fim);
  if (filtros.categoria_profissional) params.append('categoria_profissional', filtros.categoria_profissional);

  return params.toString() ? `?${params.toString()}` : '';
}

async function load() {
  const query = montarQuery();

  try {
    const meRes = await fetch(`${API}/me`, { headers: authHeaders() });
    const meJson = await meRes.json();
    setMe(meJson);

    const o = await fetch(`${API}/opcoes`, { headers: authHeaders() });
    setOp(await o.json());

    const i = await fetch(`${API}/indicadores${query}`, { headers: authHeaders() });
    setIndic(await i.json());

    const l = await fetch(`${API}/intervencoes${query}`, { headers: authHeaders() });
    setLista(await l.json());

    const p = await fetch(`${API}/profissionais`, { headers: authHeaders() });
    if (p.ok) {
      setProfissionais(await p.json());
    } else {
      setProfissionais([]);
    }

    if (meJson?.perfil === 'admin') {
      const u = await fetch(`${API}/users`, { headers: authHeaders() });
      if (u.ok) {
        setUsuarios(await u.json());
      }
    }
  } catch (error) {
    console.error(error);
    setMsg('Erro ao carregar dados do sistema.');
  }
}

function aplicarFiltros(e) {
  e.preventDefault();
  load();
}

function limparFiltros() {
  setFiltros({
    periodo: 'mes',
    data_inicio: '',
    data_fim: '',
    categoria_profissional: '',
  });

  setTimeout(() => load(), 0);
}
useEffect(() => {
  if (token) {
    load();
  }
}, [token]);
 async function salvar(e) {
  e.preventDefault();

  const url = editandoId
    ? `${API}/intervencoes/${editandoId}`
    : `${API}/intervencoes`;

  const method = editandoId ? 'PUT' : 'POST';

  const r = await fetch(url, {
    method,
    headers: authHeaders(),
    body: JSON.stringify(form),
  });

  if (!r.ok) {
    setMsg(editandoId ? 'Erro ao atualizar.' : 'Erro ao salvar. Confira os campos.');
    return;
  }

  setMsg(editandoId ? 'Intervenção atualizada com sucesso.' : 'Intervenção registrada com sucesso.');

  setForm({
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

  setEditandoId(null);
  load();
}

function editarRegistro(r) {
  setForm({
    data_atendimento: r.data_atendimento,
    paciente_nome: r.paciente_nome,
    data_nascimento: r.data_nascimento,
    tipo_atendimento: r.tipo_atendimento,
    motivo_atendimento: r.motivo_atendimento,
    comorbidade: r.comorbidade,
    tipos_intervencao: r.tipos_intervencao,
    resultado: r.resultado,
    observacoes: r.observacoes || '',
  });

  setEditandoId(r.id);
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

  async function inativarRegistro(id) {
    const ok = window.confirm('Deseja inativar este registro?');
    if (!ok) return;

    const r = await fetch(`${API}/intervencoes/${id}/inativar`, {
      method: 'PUT',
      headers: authHeaders(),
    });

    if (!r.ok) {
      setMsg('Erro ao inativar registro.');
      return;
    }

    setMsg('Registro inativado com sucesso.');
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
      categoria_profissional: 'Farmacêutico',
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
	  <button onClick={exportarCSV}>Exportar CSV</button>
          {me?.perfil === 'admin' && <button onClick={() => setTab('admin')}>Administração</button>}
          <button onClick={() => { localStorage.clear(); setToken(''); }}>Sair</button>
        </div>
      </header>

      {msg && <div className="alert">{msg}</div>}

      {tab === 'intervencoes' && (
        <>
<section className="card">
  <h2>Filtros analíticos</h2>
  <form onSubmit={aplicarFiltros} className="filters">

    <label>Período
      <select
        value={filtros.periodo}
        onChange={e => setFiltros({ ...filtros, periodo: e.target.value })}
      >
        <option value="mes">Mês atual</option>
        <option value="semana">Últimos 7 dias</option>
        <option value="quinzena">Últimos 15 dias</option>
        <option value="ano">Ano atual</option>
        <option value="customizado">Personalizado</option>
      </select>
    </label>

    {filtros.periodo === 'customizado' && (
      <>
        <label>Data inicial
          <input
            type="date"
            value={filtros.data_inicio}
            onChange={e => setFiltros({ ...filtros, data_inicio: e.target.value })}
          />
        </label>

        <label>Data final
          <input
            type="date"
            value={filtros.data_fim}
            onChange={e => setFiltros({ ...filtros, data_fim: e.target.value })}
          />
        </label>
      </>
    )}

    <label>Categoria profissional
      <select
        value={filtros.categoria_profissional}
        onChange={e => setFiltros({ ...filtros, categoria_profissional: e.target.value })}
      >
        <option value="">Todos</option>
        <option value="Farmacêutico">Farmacêutico</option>
        <option value="Técnico">Técnico</option>
        <option value="Estagiário">Estagiário</option>
        <option value="Docente">Docente</option>
      </select>
    </label>

    <div style={{ display: 'flex', gap: 8, alignItems: 'end' }}>
      <button type="submit">Aplicar filtros</button>
      <button type="button" onClick={limparFiltros}>Limpar filtros</button>
    </div>
  </form>
</section>
          <section className="grid">
            <form className="card" onSubmit={salvar}>
              <h2>{editandoId ? 'Editar intervenção' : 'Nova intervenção'}</h2>

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

              <button>{editandoId ? 'Atualizar intervenção' : 'Salvar intervenção'}</button>

            </form>

            <section className="card">
              <h2>Indicadores</h2>
              <div className="kpis">
  		<strong>{indic?.total_intervencoes || 0}<span>intervenções</span></strong>
  		<strong>{indic?.total_pacientes || 0}<span>pacientes</span></strong>
  		<strong>{indic?.taxa_aceitacao || 0}%<span>aceitação</span></strong>
  		<strong>{indic?.taxa_acompanhamento || 0}%<span>acompanhamento</span></strong>
  		<strong>{indic?.taxa_encaminhamento || 0}%<span>encaminhamento</span></strong>
</div>

              <Chart title="Por tipo de intervenção" data={objToChart(indic?.por_tipo_intervencao)} />
              <Chart title="Por resultado" data={objToChart(indic?.por_resultado)} />
              <Chart title="Por comorbidade" data={objToChart(indic?.por_comorbidade)} />
	      <Chart title="Por faixa etária" data={objToChart(indic?.por_faixa_etaria)} />
	      <Chart title="Por profissional" data={objToChart(indic?.por_profissional)} />
	      <Chart title="Por categoria profissional" data={objToChart(indic?.por_categoria_profissional)} />
<TrendChart
  title="Tendência mensal de intervenções"
  data={tendenciaToChart(indic?.tendencia_mensal)}
  dataKey="intervencoes"
/>

<TrendChart
  title="Tendência mensal de aceitação (%)"
  data={tendenciaToChart(indic?.tendencia_mensal)}
  dataKey="taxa_aceitacao"
/>

<TrendChart
  title="Tendência mensal de encaminhamento (%)"
  data={tendenciaToChart(indic?.tendencia_mensal)}
  dataKey="taxa_encaminhamento"
/>
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
		  <th>Criado por</th>
		  <th>Atualizado por</th>
		  <th>Última atualização</th>
		  <th>Ações</th>
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
		    <td>{r.criado_por || '-'}</td>
		    <td>{r.atualizado_por || '-'}</td>
		    <td>{r.updated_at ? new Date(r.updated_at).toLocaleString('pt-BR') : '-'}</td>
		    <td>
  		    <td style={{ display: 'flex', gap: 6 }}>
		      <button onClick={() => editarRegistro(r)}>Editar</button>
		      <button onClick={() => inativarRegistro(r.id)}>Inativar</button>
		    </td>
		    </td>
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
	  <label>Categoria profissional
  	    <select
    	      value={novoUsuario.categoria_profissional}
    	      onChange={e => setNovoUsuario({ ...novoUsuario, categoria_profissional: e.target.value })}
  >
    	      <option value="Farmacêutico">Farmacêutico</option>
    	      <option value="Técnico">Técnico</option>
    	      <option value="Estagiário">Estagiário</option>
    	      <option value="Docente">Docente</option>
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
		  <th>Categoria</th>
                </tr>
              </thead>
              <tbody>
                {usuarios.map(u => (
                  <tr key={u.id}>
                    <td>{u.nome}</td>
                    <td>{u.email}</td>
                    <td>{u.perfil}</td>
		    <td>{u.categoria_profissional || '-'}</td>
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

function TrendChart({ title, data, dataKey }) {
  return (
    <div className="chart">
      <h3>{title}</h3>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data}>
          <XAxis dataKey="mes" />
          <YAxis allowDecimals={false} />
          <Tooltip />
          <Bar dataKey={dataKey} />
        </BarChart>
      </ResponsiveContainer>
    </div>
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