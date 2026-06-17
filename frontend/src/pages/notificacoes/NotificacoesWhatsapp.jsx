import { useEffect, useMemo, useState } from "react";
import { api } from "../../api/api";
import "./NotificacoesWhatsapp.css";

const prioridadeClasse = {
  NORMAL: "badge normal",
  IMPORTANTE: "badge importante",
  URGENTE: "badge urgente",
};

const statusClasse = {
  PENDENTE: "badge importante",
  SIMULADO: "badge normal",
  ENVIADO: "badge normal",
  ERRO: "badge urgente",
  CANCELADO: "badge neutro",
};

function limparParams(obj) {
  return Object.fromEntries(
    Object.entries(obj || {}).filter(([, valor]) => valor !== "" && valor !== null && valor !== undefined)
  );
}

function formatarData(valor) {
  if (!valor) return "-";
  const data = new Date(valor);
  if (Number.isNaN(data.getTime())) return valor;
  return data.toLocaleString("pt-BR");
}

export default function NotificacoesWhatsapp() {
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState("");
  const [mensagem, setMensagem] = useState("");

  const [dashboardNotificacoes, setDashboardNotificacoes] = useState(null);
  const [dashboardWhatsapp, setDashboardWhatsapp] = useState(null);
  const [notificacoes, setNotificacoes] = useState([]);
  const [notificacoesCeaf, setNotificacoesCeaf] = useState([]);
  const [resumoCeaf, setResumoCeaf] = useState(null);
  const [fila, setFila] = useState([]);
  const [opcoesNotif, setOpcoesNotif] = useState({ tipos: [], prioridades: [], origens: [] });
  const [opcoesZap, setOpcoesZap] = useState({ status: [], provedores: [], origens: [] });

  const [filtrosNotif, setFiltrosNotif] = useState({ lida: "", prioridade: "", tipo: "", necessita_acao: "" });
  const [filtrosZap, setFiltrosZap] = useState({ status: "", prioridade: "" });

  const [formManual, setFormManual] = useState({ telefone: "", mensagem: "", prioridade: "NORMAL" });

  async function carregarTudo() {
    setLoading(true);
    setErro("");
    setMensagem("");
    try {
      const paramsNotif = limparParams({
        ...filtrosNotif,
        lida: filtrosNotif.lida === "" ? undefined : filtrosNotif.lida === "true",
        necessita_acao: filtrosNotif.necessita_acao === "" ? undefined : filtrosNotif.necessita_acao === "true",
      });
      const paramsZap = limparParams(filtrosZap);

      const [dashNotif, listaNotif, ceafPendentes, dashZap, filaZap, opNotif, opZap] = await Promise.all([
        api.get("/consultorio/notificacoes/dashboard"),
        api.get("/consultorio/notificacoes", { params: paramsNotif }),
        api.get("/consultorio/agenda/notificacoes-pendentes-ceaf", { params: { limite: 200 } }),
        api.get("/consultorio/whatsapp/dashboard"),
        api.get("/consultorio/whatsapp/fila", { params: paramsZap }),
        api.get("/consultorio/notificacoes/opcoes"),
        api.get("/consultorio/whatsapp/opcoes"),
      ]);

      setDashboardNotificacoes(dashNotif.data || null);
      setNotificacoes(listaNotif.data?.notificacoes || []);
      setNotificacoesCeaf(ceafPendentes.data?.notificacoes || []);
      setResumoCeaf(ceafPendentes.data?.resumo_alertas || ceafPendentes.data?.resumo || null);
      setDashboardWhatsapp(dashZap.data || null);
      setFila(filaZap.data?.envios || []);
      setOpcoesNotif(opNotif.data || { tipos: [], prioridades: [], origens: [] });
      setOpcoesZap(opZap.data || { status: [], provedores: [], origens: [] });
    } catch (e) {
      console.error(e);
      setErro("Não foi possível carregar notificações/WhatsApp. Verifique o backend e as permissões do usuário.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    carregarTudo();
  }, []);

  async function gerarAutomaticas() {
    try {
      setLoading(true);
      const resp = await api.post("/consultorio/notificacoes/gerar-automaticas");
      setMensagem(resp.data?.mensagem || "Notificações automáticas processadas.");
      await carregarTudo();
    } catch (e) {
      console.error(e);
      setErro("Erro ao gerar notificações automáticas.");
    } finally {
      setLoading(false);
    }
  }

  async function gerarNotificacoesCeaf() {
    try {
      setLoading(true);
      const resp = await api.get("/consultorio/agenda/notificacoes-pendentes-ceaf", { params: { limite: 300 } });
      setNotificacoesCeaf(resp.data?.notificacoes || []);
      setResumoCeaf(resp.data?.resumo_alertas || resp.data?.resumo || null);
      setMensagem("Notificações CEAF atualizadas para preparação de contato.");
    } catch (e) {
      console.error(e);
      setErro("Erro ao atualizar notificações CEAF.");
    } finally {
      setLoading(false);
    }
  }

  async function enfileirarNotificacoes() {
    try {
      setLoading(true);
      const resp = await api.post("/consultorio/whatsapp/enfileirar-notificacoes");
      setMensagem(resp.data?.mensagem || "Notificações enfileiradas para WhatsApp.");
      await carregarTudo();
    } catch (e) {
      console.error(e);
      setErro("Erro ao enfileirar notificações para WhatsApp.");
    } finally {
      setLoading(false);
    }
  }

  async function simularEnvio() {
    try {
      setLoading(true);
      const resp = await api.post("/consultorio/whatsapp/simular-envio");
      setMensagem(resp.data?.mensagem || "Envios simulados processados.");
      await carregarTudo();
    } catch (e) {
      console.error(e);
      setErro("Erro ao simular envio de WhatsApp.");
    } finally {
      setLoading(false);
    }
  }

  async function marcarLida(id) {
    await api.put(`/consultorio/notificacoes/${id}/marcar-lida`);
    await carregarTudo();
  }

  async function marcarTodasLidas() {
    await api.put("/consultorio/notificacoes/marcar-todas-lidas");
    await carregarTudo();
  }

  async function cancelarEnvio(id) {
    await api.put(`/consultorio/whatsapp/fila/${id}/cancelar`);
    await carregarTudo();
  }

  async function reenfileirarEnvio(id) {
    await api.put(`/consultorio/whatsapp/fila/${id}/reenfileirar`);
    await carregarTudo();
  }

  async function criarEnvioManual(evento) {
    evento.preventDefault();
    setErro("");
    setMensagem("");
    if (!formManual.telefone || !formManual.mensagem) {
      setErro("Informe telefone e mensagem para criar envio manual.");
      return;
    }
    try {
      await api.post("/consultorio/whatsapp/envio-manual", formManual);
      setFormManual({ telefone: "", mensagem: "", prioridade: "NORMAL" });
      setMensagem("Envio manual criado na fila.");
      await carregarTudo();
    } catch (e) {
      console.error(e);
      setErro("Erro ao criar envio manual.");
    }
  }

  const cardsNotificacao = useMemo(() => {
    const d = dashboardNotificacoes || {};
    return [
      ["Total", d.total ?? 0],
      ["Não lidas", d.nao_lidas ?? 0],
      ["Importantes", d.importantes ?? 0],
      ["Urgentes", d.urgentes ?? 0],
      ["Retiradas atrasadas", d.retiradas_atrasadas ?? 0],
      ["Renovações pendentes", d.renovacoes_pendentes ?? 0],
    ];
  }, [dashboardNotificacoes]);

  const cardsCeaf = useMemo(() => {
    const d = resumoCeaf || {};
    return [
      ["CEAF pendentes", notificacoesCeaf.length],
      ["Críticos", d.critico ?? d.criticos ?? 0],
      ["Urgentes", d.urgente ?? d.urgentes ?? 0],
      ["Atenção", d.atencao ?? d.atencao_total ?? 0],
      ["Informativos", d.informativo ?? d.informativos ?? 0],
    ];
  }, [resumoCeaf, notificacoesCeaf]);

  const cardsWhatsapp = useMemo(() => {
    const d = dashboardWhatsapp || {};
    return [
      ["Total na fila", d.total ?? 0],
      ["Pendentes", d.pendentes ?? 0],
      ["Simulados", d.simulados ?? 0],
      ["Com erro", d.erros ?? 0],
      ["Cancelados", d.cancelados ?? 0],
    ];
  }, [dashboardWhatsapp]);

  return (
    <div className="notificacoes-page">
      <div className="page-header">
        <div>
          <h1>Notificações e WhatsApp</h1>
          <p>Central operacional para alertas internos, fila de WhatsApp e simulação de envio.</p>
        </div>
        <button className="primary" onClick={carregarTudo} disabled={loading}>{loading ? "Carregando..." : "Atualizar"}</button>
      </div>

      {erro && <div className="alert erro">{erro}</div>}
      {mensagem && <div className="alert sucesso">{mensagem}</div>}

      <section className="grid-cards">
        {cardsNotificacao.map(([label, valor]) => (
          <div className="metric-card" key={label}>
            <span>{label}</span>
            <strong>{valor}</strong>
          </div>
        ))}
      </section>

      <section className="actions-row">
        <button onClick={gerarAutomaticas}>Gerar notificações automáticas</button>
        <button onClick={gerarNotificacoesCeaf}>Atualizar notificações CEAF</button>
        <button onClick={marcarTodasLidas}>Marcar todas como lidas</button>
        <button onClick={enfileirarNotificacoes}>Enfileirar notificações no WhatsApp</button>
        <button onClick={simularEnvio}>Simular envios pendentes</button>
      </section>

      <section className="panel">
        <div className="panel-title">
          <h2>Notificações internas</h2>
          <div className="filters">
            <select value={filtrosNotif.lida} onChange={(e) => setFiltrosNotif({ ...filtrosNotif, lida: e.target.value })}>
              <option value="">Todas</option>
              <option value="false">Não lidas</option>
              <option value="true">Lidas</option>
            </select>
            <select value={filtrosNotif.prioridade} onChange={(e) => setFiltrosNotif({ ...filtrosNotif, prioridade: e.target.value })}>
              <option value="">Prioridade</option>
              {(opcoesNotif.prioridades || []).map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
            <select value={filtrosNotif.tipo} onChange={(e) => setFiltrosNotif({ ...filtrosNotif, tipo: e.target.value })}>
              <option value="">Tipo</option>
              {(opcoesNotif.tipos || []).map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
            <select value={filtrosNotif.necessita_acao} onChange={(e) => setFiltrosNotif({ ...filtrosNotif, necessita_acao: e.target.value })}>
              <option value="">Ação?</option>
              <option value="true">Necessita ação</option>
              <option value="false">Informativa</option>
            </select>
            <button onClick={carregarTudo}>Filtrar</button>
          </div>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Prioridade</th>
                <th>Tipo</th>
                <th>Título</th>
                <th>Mensagem</th>
                <th>Origem</th>
                <th>Criada em</th>
                <th>Status</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {notificacoes.map((n) => (
                <tr key={n.id} className={n.lida ? "linha-lida" : ""}>
                  <td><span className={prioridadeClasse[n.prioridade] || "badge"}>{n.prioridade}</span></td>
                  <td>{n.tipo}</td>
                  <td>{n.titulo}</td>
                  <td>{n.mensagem}</td>
                  <td>{n.origem}</td>
                  <td>{formatarData(n.data_criacao)}</td>
                  <td>{n.lida ? "Lida" : "Não lida"}</td>
                  <td>{!n.lida && <button className="small" onClick={() => marcarLida(n.id)}>Marcar lida</button>}</td>
                </tr>
              ))}
              {notificacoes.length === 0 && <tr><td colSpan="8">Nenhuma notificação encontrada.</td></tr>}
            </tbody>
          </table>
        </div>
      </section>


      <section className="panel ceaf-notificacoes-panel">
        <div className="panel-title">
          <div>
            <h2>Preparação CEAF para contato</h2>
            <p className="muted">Alertas CEAF convertidos em notificações operacionais para posterior WhatsApp. Nenhum envio automático é realizado nesta etapa.</p>
          </div>
          <button onClick={gerarNotificacoesCeaf} disabled={loading}>Atualizar CEAF</button>
        </div>

        <section className="grid-cards compact-grid">
          {cardsCeaf.map(([label, valor]) => (
            <div className="metric-card" key={label}>
              <span>{label}</span>
              <strong>{valor}</strong>
            </div>
          ))}
        </section>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Prioridade</th>
                <th>Paciente</th>
                <th>Telefone</th>
                <th>Medicamento</th>
                <th>Motivo</th>
                <th>Mensagem sugerida</th>
              </tr>
            </thead>
            <tbody>
              {notificacoesCeaf.map((n, idx) => (
                <tr key={`${n.paciente_ceaf_id || n.telefone || idx}-${n.tipo || n.motivo}`}>
                  <td><span className={prioridadeClasse[n.prioridade] || prioridadeClasse[String(n.prioridade || "").toUpperCase()] || "badge"}>{n.prioridade || "-"}</span></td>
                  <td>{n.paciente_nome || n.nome || "-"}</td>
                  <td>{n.telefone || "-"}</td>
                  <td>{n.medicamento || "-"}</td>
                  <td>{n.motivo || n.tipo || n.titulo || "-"}</td>
                  <td>{n.mensagem || n.mensagem_sugerida || "-"}</td>
                </tr>
              ))}
              {notificacoesCeaf.length === 0 && <tr><td colSpan="6">Nenhuma notificação CEAF pendente encontrada.</td></tr>}
            </tbody>
          </table>
        </div>
      </section>

      <section className="grid-cards whatsapp-cards">
        {cardsWhatsapp.map(([label, valor]) => (
          <div className="metric-card" key={label}>
            <span>{label}</span>
            <strong>{valor}</strong>
          </div>
        ))}
      </section>

      <section className="panel two-columns">
        <div>
          <h2>Envio manual WhatsApp</h2>
          <form className="manual-form" onSubmit={criarEnvioManual}>
            <label>Telefone</label>
            <input value={formManual.telefone} onChange={(e) => setFormManual({ ...formManual, telefone: e.target.value })} placeholder="Ex.: 67999999999" />
            <label>Prioridade</label>
            <select value={formManual.prioridade} onChange={(e) => setFormManual({ ...formManual, prioridade: e.target.value })}>
              <option value="NORMAL">NORMAL</option>
              <option value="IMPORTANTE">IMPORTANTE</option>
              <option value="URGENTE">URGENTE</option>
            </select>
            <label>Mensagem</label>
            <textarea value={formManual.mensagem} onChange={(e) => setFormManual({ ...formManual, mensagem: e.target.value })} rows={5} />
            <button className="primary" type="submit">Adicionar à fila</button>
          </form>
        </div>
        <div className="info-box">
          <h3>Estado atual</h3>
          <p>O WhatsApp está em modo preparatório. Os envios são simulados e registrados na fila, sem integração externa.</p>
          <p>Quando a API real for escolhida, esta tela continuará sendo usada para monitorar status, erros e reenfileiramentos.</p>
        </div>
      </section>

      <section className="panel">
        <div className="panel-title">
          <h2>Fila WhatsApp</h2>
          <div className="filters">
            <select value={filtrosZap.status} onChange={(e) => setFiltrosZap({ ...filtrosZap, status: e.target.value })}>
              <option value="">Status</option>
              {(opcoesZap.status || []).map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
            <select value={filtrosZap.prioridade} onChange={(e) => setFiltrosZap({ ...filtrosZap, prioridade: e.target.value })}>
              <option value="">Prioridade</option>
              <option value="NORMAL">NORMAL</option>
              <option value="IMPORTANTE">IMPORTANTE</option>
              <option value="URGENTE">URGENTE</option>
            </select>
            <button onClick={carregarTudo}>Filtrar</button>
          </div>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Status</th>
                <th>Prioridade</th>
                <th>Telefone</th>
                <th>Mensagem</th>
                <th>Origem</th>
                <th>Criado em</th>
                <th>Erro</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {fila.map((envio) => (
                <tr key={envio.id}>
                  <td><span className={statusClasse[envio.status] || "badge"}>{envio.status}</span></td>
                  <td>{envio.prioridade}</td>
                  <td>{envio.telefone || "-"}</td>
                  <td>{envio.mensagem}</td>
                  <td>{envio.origem}</td>
                  <td>{formatarData(envio.criado_em)}</td>
                  <td>{envio.ultimo_erro || "-"}</td>
                  <td className="acoes">
                    {envio.status === "PENDENTE" && <button className="small danger" onClick={() => cancelarEnvio(envio.id)}>Cancelar</button>}
                    {envio.status !== "PENDENTE" && envio.telefone && <button className="small" onClick={() => reenfileirarEnvio(envio.id)}>Reenfileirar</button>}
                  </td>
                </tr>
              ))}
              {fila.length === 0 && <tr><td colSpan="8">Nenhum envio na fila.</td></tr>}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
