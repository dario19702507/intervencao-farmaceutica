import { useEffect, useMemo, useState } from "react";
import { api } from "../../api/api";
import "./AgendaCatalogo.css";

const vazioEvento = {
  paciente_id: "",
  paciente_nome: "",
  telefone: "",
  servico_origem: "farmacia_escola",
  tipo_evento: "RETIRADA",
  prioridade: "NORMAL",
  titulo: "",
  medicamento_id: "",
  data_evento: "",
  data_inicio_vigencia: "",
  data_fim_vigencia: "",
  observacoes: "",
  notificar_whatsapp: true,
};

const vazioMedicamento = {
  farmaco: "",
  apresentacao: "",
  concentracao: "",
  forma_farmaceutica: "",
  componente: "CEAF",
  frequencia_dispensacao: "MENSAL",
  observacoes: "",
};

function normalizarListaPacientes(payload) {
  if (Array.isArray(payload)) return payload;
  return payload?.pacientes || payload?.items || payload?.data || [];
}

function formatarData(data) {
  if (!data) return "-";
  const [ano, mes, dia] = String(data).split("-");
  if (!ano || !mes || !dia) return data;
  return `${dia}/${mes}/${ano}`;
}

export default function AgendaCatalogo() {
  const [aba, setAba] = useState("agenda");
  const [loading, setLoading] = useState(false);
  const [mensagem, setMensagem] = useState("");
  const [erro, setErro] = useState("");

  const [opcoes, setOpcoes] = useState({
    tipos_evento: ["INCLUSAO", "RETIRADA", "RENOVACAO", "ADEQUACAO", "ENCERRAMENTO"],
    prioridades: ["NORMAL", "IMPORTANTE", "URGENTE"],
    status: ["AGENDADO", "REALIZADO", "ATRASADO", "CANCELADO"],
    frequencias_dispensacao: ["MENSAL", "BIMESTRAL", "TRIMESTRAL", "SEMESTRAL", "ANUAL"],
  });
  const [dashboard, setDashboard] = useState(null);
  const [eventos, setEventos] = useState([]);
  const [medicamentos, setMedicamentos] = useState([]);
  const [pacientes, setPacientes] = useState([]);

  const [filtrosAgenda, setFiltrosAgenda] = useState({ status: "", data_inicio: "", data_fim: "" });
  const [buscaMedicamento, setBuscaMedicamento] = useState("");

  const [evento, setEvento] = useState(vazioEvento);
  const [medicamento, setMedicamento] = useState(vazioMedicamento);
  const [medicamentoEditandoId, setMedicamentoEditandoId] = useState(null);

  async function carregarTudo() {
    setLoading(true);
    setErro("");
    try {
      const [opcoesResp, dashboardResp, agendaResp, medsResp, pacientesResp] = await Promise.all([
        api.get("/consultorio/agenda/opcoes"),
        api.get("/consultorio/agenda/dashboard"),
        api.get("/consultorio/agenda", {
          params: Object.fromEntries(
            Object.entries(filtrosAgenda).filter(([_, valor]) => valor !== "")
          ),
        }),
        api.get("/consultorio/catalogo-medicamentos", { params: { busca: buscaMedicamento || undefined, ativo: true } }),
        api.get("/consultorio/pacientes-clinicos"),
      ]);

      setOpcoes(opcoesResp.data || opcoes);
      setDashboard(dashboardResp.data || null);
      setEventos(agendaResp.data?.eventos || []);
      setMedicamentos(medsResp.data?.medicamentos || []);
      setPacientes(normalizarListaPacientes(pacientesResp.data));
    } catch (e) {
      console.error(e);
      setErro("Não foi possível carregar Agenda/Catálogo. Verifique se o backend está ativo.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    carregarTudo();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function filtrarAgenda(e) {
    e.preventDefault();
    await carregarTudo();
  }

  async function buscarMedicamentos(e) {
    e.preventDefault();
    try {
      const resp = await api.get("/consultorio/catalogo-medicamentos", {
        params: { busca: buscaMedicamento || undefined, ativo: true },
      });
      setMedicamentos(resp.data?.medicamentos || []);
    } catch (err) {
      console.error(err);
      setErro("Erro ao buscar medicamentos.");
    }
  }

  function selecionarPaciente(id) {
    const selecionado = pacientes.find((p) => String(p.id) === String(id));
    setEvento((atual) => ({
      ...atual,
      paciente_id: id,
      paciente_nome: selecionado?.nome || selecionado?.paciente_nome || atual.paciente_nome,
      telefone: selecionado?.telefone || selecionado?.telefone_principal || atual.telefone,
    }));
  }

  async function criarEvento(e) {
    e.preventDefault();
    setMensagem("");
    setErro("");

    if (!evento.paciente_nome || !evento.data_evento || !evento.tipo_evento) {
      setErro("Informe paciente, tipo de evento e data prevista.");
      return;
    }

    const payload = {
      ...evento,
      paciente_id: evento.paciente_id ? Number(evento.paciente_id) : null,
      medicamento_id: evento.medicamento_id ? Number(evento.medicamento_id) : null,
      titulo: evento.titulo || `${evento.tipo_evento} - ${evento.paciente_nome}`,
      data_inicio_vigencia: evento.data_inicio_vigencia || null,
      data_fim_vigencia: evento.data_fim_vigencia || null,
    };

    try {
      await api.post("/consultorio/agenda", payload);
      setMensagem("Evento criado com sucesso.");
      setEvento(vazioEvento);
      await carregarTudo();
    } catch (err) {
      console.error(err);
      setErro(err.response?.data?.detail || "Erro ao criar evento da agenda.");
    }
  }

  async function salvarMedicamento(e) {
    e.preventDefault();
    setMensagem("");
    setErro("");

    if (!medicamento.farmaco || !medicamento.apresentacao) {
      setErro("Informe o fármaco e a apresentação.");
      return;
    }

    try {
      if (medicamentoEditandoId) {
        await api.put(`/consultorio/catalogo-medicamentos/${medicamentoEditandoId}`, medicamento);
        setMensagem("Medicamento atualizado com sucesso.");
      } else {
        await api.post("/consultorio/catalogo-medicamentos", medicamento);
        setMensagem("Medicamento cadastrado com sucesso.");
      }
      setMedicamento(vazioMedicamento);
      setMedicamentoEditandoId(null);
      await carregarTudo();
    } catch (err) {
      console.error(err);
      setErro(err.response?.data?.detail || "Erro ao salvar medicamento.");
    }
  }

  async function semearCatalogo() {
    setMensagem("");
    setErro("");
    try {
      const resp = await api.post("/consultorio/catalogo-medicamentos/seed");
      setMensagem(resp.data?.mensagem || "Catálogo padrão processado.");
      await carregarTudo();
    } catch (err) {
      console.error(err);
      setErro(err.response?.data?.detail || "Erro ao carregar catálogo padrão.");
    }
  }

  async function inativarMedicamento(id) {
    const confirmar = window.confirm("Inativar este medicamento do catálogo?");
    if (!confirmar) return;
    try {
      await api.delete(`/consultorio/catalogo-medicamentos/${id}`);
      setMensagem("Medicamento inativado.");
      await carregarTudo();
    } catch (err) {
      console.error(err);
      setErro("Erro ao inativar medicamento.");
    }
  }

  function editarMedicamento(item) {
    setAba("catalogo");
    setMedicamentoEditandoId(item.id);
    setMedicamento({
      farmaco: item.farmaco || "",
      apresentacao: item.apresentacao || "",
      concentracao: item.concentracao || "",
      forma_farmaceutica: item.forma_farmaceutica || "",
      componente: item.componente || "",
      frequencia_dispensacao: item.frequencia_dispensacao || "",
      observacoes: item.observacoes || "",
    });
  }

  const eventosOrdenados = useMemo(() => {
    return [...eventos].sort((a, b) => String(a.data_evento).localeCompare(String(b.data_evento)));
  }, [eventos]);

  return (
    <div className="agenda-catalogo-page">
      <div className="page-header-row">
        <div>
          <h2>Agenda e Catálogo de Medicamentos</h2>
          <p className="muted">Controle eventos do cuidado e use uma lista padronizada de fármacos/apresentações.</p>
        </div>
        <button className="btn secondary" onClick={carregarTudo} disabled={loading}>
          {loading ? "Atualizando..." : "Atualizar"}
        </button>
      </div>

      {mensagem && <div className="alert success">{mensagem}</div>}
      {erro && <div className="alert error">{erro}</div>}

      <div className="metric-row agenda-metrics">
        <div className="mini-card"><span>Hoje</span><strong>{dashboard?.eventos_hoje ?? 0}</strong></div>
        <div className="mini-card"><span>Semana</span><strong>{dashboard?.eventos_semana ?? 0}</strong></div>
        <div className="mini-card"><span>Mês</span><strong>{dashboard?.eventos_mes ?? 0}</strong></div>
        <div className="mini-card warning"><span>Atrasados</span><strong>{dashboard?.eventos_atrasados ?? 0}</strong></div>
        <div className="mini-card danger"><span>Urgentes</span><strong>{dashboard?.eventos_urgentes ?? 0}</strong></div>
      </div>

      <div className="tabs-line">
        <button className={aba === "agenda" ? "active" : ""} onClick={() => setAba("agenda")}>Agenda</button>
        <button className={aba === "catalogo" ? "active" : ""} onClick={() => setAba("catalogo")}>Catálogo de Medicamentos</button>
      </div>

      {aba === "agenda" && (
        <div className="two-columns">
          <section className="panel-card">
            <h3>Novo evento</h3>
            <form className="form-grid" onSubmit={criarEvento}>
              <label>
                Paciente clínico
                <select value={evento.paciente_id} onChange={(e) => selecionarPaciente(e.target.value)}>
                  <option value="">Selecionar da lista ou digitar abaixo</option>
                  {pacientes.map((p) => (
                    <option key={p.id} value={p.id}>{p.nome || p.paciente_nome || `Paciente ${p.id}`}</option>
                  ))}
                </select>
              </label>
              <label>
                Nome do paciente *
                <input value={evento.paciente_nome} onChange={(e) => setEvento({ ...evento, paciente_nome: e.target.value })} />
              </label>
              <label>
                Telefone
                <input value={evento.telefone || ""} onChange={(e) => setEvento({ ...evento, telefone: e.target.value })} />
              </label>
              <label>
                Tipo de evento *
                <select value={evento.tipo_evento} onChange={(e) => setEvento({ ...evento, tipo_evento: e.target.value })}>
                  {opcoes.tipos_evento?.map((item) => <option key={item} value={item}>{item}</option>)}
                </select>
              </label>
              <label>
                Prioridade
                <select value={evento.prioridade} onChange={(e) => setEvento({ ...evento, prioridade: e.target.value })}>
                  {opcoes.prioridades?.map((item) => <option key={item} value={item}>{item}</option>)}
                </select>
              </label>
              <label>
                Data prevista *
                <input type="date" value={evento.data_evento} onChange={(e) => setEvento({ ...evento, data_evento: e.target.value })} />
              </label>
              <label className="full">
                Medicamento padronizado
                <select value={evento.medicamento_id} onChange={(e) => setEvento({ ...evento, medicamento_id: e.target.value })}>
                  <option value="">Sem vínculo específico</option>
                  {medicamentos.map((m) => (
                    <option key={m.id} value={m.id}>{m.descricao_completa}</option>
                  ))}
                </select>
              </label>
              <label>
                Início da vigência
                <input type="date" value={evento.data_inicio_vigencia} onChange={(e) => setEvento({ ...evento, data_inicio_vigencia: e.target.value })} />
              </label>
              <label>
                Fim da vigência
                <input type="date" value={evento.data_fim_vigencia} onChange={(e) => setEvento({ ...evento, data_fim_vigencia: e.target.value })} />
              </label>
              <label className="full">
                Título
                <input value={evento.titulo} onChange={(e) => setEvento({ ...evento, titulo: e.target.value })} placeholder="Gerado automaticamente se ficar vazio" />
              </label>
              <label className="full">
                Observações
                <textarea value={evento.observacoes} onChange={(e) => setEvento({ ...evento, observacoes: e.target.value })} rows={3} />
              </label>
              <label className="check-row full">
                <input type="checkbox" checked={evento.notificar_whatsapp} onChange={(e) => setEvento({ ...evento, notificar_whatsapp: e.target.checked })} />
                Preparar para notificação futura via WhatsApp
              </label>
              <button className="btn primary full" type="submit">Salvar evento</button>
            </form>
          </section>

          <section className="panel-card">
            <div className="section-title-row">
              <h3>Eventos agendados</h3>
            </div>
            <form className="filters-row" onSubmit={filtrarAgenda}>
              <select value={filtrosAgenda.status} onChange={(e) => setFiltrosAgenda({ ...filtrosAgenda, status: e.target.value })}>
                <option value="">Todos os status</option>
                <option value="agendado">agendado</option>
                <option value="AGENDADO">AGENDADO</option>
                {opcoes.status?.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
              <input type="date" value={filtrosAgenda.data_inicio} onChange={(e) => setFiltrosAgenda({ ...filtrosAgenda, data_inicio: e.target.value })} />
              <input type="date" value={filtrosAgenda.data_fim} onChange={(e) => setFiltrosAgenda({ ...filtrosAgenda, data_fim: e.target.value })} />
              <button className="btn secondary" type="submit">Filtrar</button>
            </form>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr><th>Data</th><th>Paciente</th><th>Tipo</th><th>Medicamento</th><th>Status</th><th>Prioridade</th></tr>
                </thead>
                <tbody>
                  {eventosOrdenados.map((ev) => (
                    <tr key={ev.id}>
                      <td>{formatarData(ev.data_evento)}</td>
                      <td>{ev.paciente_nome}</td>
                      <td>{ev.tipo_evento}</td>
                      <td>{ev.medicamento || "-"}</td>
                      <td><span className="pill">{ev.status}</span></td>
                      <td><span className={`pill priority-${String(ev.prioridade || "NORMAL").toLowerCase()}`}>{ev.prioridade || "NORMAL"}</span></td>
                    </tr>
                  ))}
                  {!eventosOrdenados.length && <tr><td colSpan="6" className="empty">Nenhum evento encontrado.</td></tr>}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      )}

      {aba === "catalogo" && (
        <div className="two-columns">
          <section className="panel-card">
            <h3>{medicamentoEditandoId ? "Editar medicamento" : "Novo medicamento"}</h3>
            <form className="form-grid" onSubmit={salvarMedicamento}>
              <label>
                Fármaco *
                <input value={medicamento.farmaco} onChange={(e) => setMedicamento({ ...medicamento, farmaco: e.target.value })} />
              </label>
              <label>
                Apresentação *
                <input value={medicamento.apresentacao} onChange={(e) => setMedicamento({ ...medicamento, apresentacao: e.target.value })} />
              </label>
              <label>
                Concentração
                <input value={medicamento.concentracao || ""} onChange={(e) => setMedicamento({ ...medicamento, concentracao: e.target.value })} />
              </label>
              <label>
                Forma farmacêutica
                <input value={medicamento.forma_farmaceutica || ""} onChange={(e) => setMedicamento({ ...medicamento, forma_farmaceutica: e.target.value })} />
              </label>
              <label>
                Componente
                <input value={medicamento.componente || ""} onChange={(e) => setMedicamento({ ...medicamento, componente: e.target.value })} />
              </label>
              <label>
                Frequência
                <select value={medicamento.frequencia_dispensacao || ""} onChange={(e) => setMedicamento({ ...medicamento, frequencia_dispensacao: e.target.value })}>
                  <option value="">Não definida</option>
                  {opcoes.frequencias_dispensacao?.map((f) => <option key={f} value={f}>{f}</option>)}
                </select>
              </label>
              <label className="full">
                Observações
                <textarea rows={3} value={medicamento.observacoes || ""} onChange={(e) => setMedicamento({ ...medicamento, observacoes: e.target.value })} />
              </label>
              <button className="btn primary full" type="submit">{medicamentoEditandoId ? "Atualizar" : "Cadastrar"}</button>
              {medicamentoEditandoId && (
                <button className="btn secondary full" type="button" onClick={() => { setMedicamento(vazioMedicamento); setMedicamentoEditandoId(null); }}>Cancelar edição</button>
              )}
            </form>
          </section>

          <section className="panel-card">
            <div className="section-title-row">
              <h3>Catálogo padronizado</h3>
              <button className="btn secondary" onClick={semearCatalogo}>Carregar padrão</button>
            </div>
            <form className="filters-row" onSubmit={buscarMedicamentos}>
              <input placeholder="Buscar fármaco, apresentação ou concentração" value={buscaMedicamento} onChange={(e) => setBuscaMedicamento(e.target.value)} />
              <button className="btn secondary" type="submit">Buscar</button>
            </form>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr><th>Medicamento</th><th>Componente</th><th>Frequência</th><th>Ações</th></tr>
                </thead>
                <tbody>
                  {medicamentos.map((m) => (
                    <tr key={m.id}>
                      <td><strong>{m.farmaco}</strong><br /><small>{m.apresentacao} {m.concentracao ? `• ${m.concentracao}` : ""}</small></td>
                      <td>{m.componente || "-"}</td>
                      <td>{m.frequencia_dispensacao || "-"}</td>
                      <td className="actions-cell">
                        <button className="link-btn" onClick={() => editarMedicamento(m)}>Editar</button>
                        <button className="link-btn danger-text" onClick={() => inativarMedicamento(m.id)}>Inativar</button>
                      </td>
                    </tr>
                  ))}
                  {!medicamentos.length && <tr><td colSpan="4" className="empty">Nenhum medicamento encontrado.</td></tr>}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
