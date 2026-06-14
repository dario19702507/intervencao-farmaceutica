import { useEffect, useMemo, useState } from "react";
import { api } from "../../api/api";
import "./IntegracaoIntervencoes.css";

const ABAS = [
  { key: "resumo", label: "Resumo" },
  { key: "sincronizacao", label: "Sincronização" },
  { key: "checkpoints", label: "Checkpoints" },
  { key: "consistencia", label: "Consistência" },
  { key: "rastreabilidade", label: "Rastreabilidade" },
];

function Card({ titulo, valor, detalhe }) {
  return (
    <div className="integracao-card">
      <span>{titulo}</span>
      <strong>{valor ?? 0}</strong>
      {detalhe ? <small>{detalhe}</small> : null}
    </div>
  );
}

function Badge({ children, tipo = "neutro" }) {
  return <span className={`integracao-badge ${tipo}`}>{children}</span>;
}

function formatarData(valor) {
  if (!valor) return "-";
  try {
    return new Date(valor).toLocaleString("pt-BR");
  } catch (_) {
    return String(valor);
  }
}

export default function IntegracaoIntervencoes() {
  const [aba, setAba] = useState("resumo");
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState("");
  const [resumo, setResumo] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [checkpoints, setCheckpoints] = useState({ checkpoints: [] });
  const [consistencia, setConsistencia] = useState({ problemas: [], resumo: {} });
  const [rastreabilidade, setRastreabilidade] = useState({ registros: [] });
  const [filtroStatus, setFiltroStatus] = useState("");

  async function carregarTudo() {
    setCarregando(true);
    setErro("");
    try {
      const [rResumo, rDashboard, rCheckpoints, rConsistencia, rRastreabilidade] = await Promise.all([
        api.get("/consultorio/migracao-intervencoes/integracao-resumo"),
        api.get("/consultorio/migracao-intervencoes/dashboard"),
        api.get("/consultorio/migracao-intervencoes/checkpoints", { params: { limite: 30 } }),
        api.get("/consultorio/migracao-intervencoes/consistencia"),
        api.get("/consultorio/migracao-intervencoes/rastreabilidade", { params: { limite: 100 } }),
      ]);
      setResumo(rResumo.data || null);
      setDashboard(rDashboard.data || null);
      setCheckpoints(rCheckpoints.data || { checkpoints: [] });
      setConsistencia(rConsistencia.data || { problemas: [], resumo: {} });
      setRastreabilidade(rRastreabilidade.data || { registros: [] });
    } catch (error) {
      setErro(error.response?.data?.detail || "Não foi possível carregar o painel de integração.");
    } finally {
      setCarregando(false);
    }
  }

  useEffect(() => {
    carregarTudo();
  }, []);

  async function carregarRastreabilidadePorStatus(status) {
    setFiltroStatus(status);
    setCarregando(true);
    try {
      const params = { limite: 100 };
      if (status) params.status = status;
      const resp = await api.get("/consultorio/migracao-intervencoes/rastreabilidade", { params });
      setRastreabilidade(resp.data || { registros: [] });
    } catch (error) {
      setErro(error.response?.data?.detail || "Não foi possível filtrar a rastreabilidade.");
    } finally {
      setCarregando(false);
    }
  }

  const statusResumo = useMemo(() => dashboard?.staging_por_status || resumo?.staging_por_status || {}, [dashboard, resumo]);
  const problemas = consistencia?.problemas || [];

  function renderResumo() {
    return (
      <>
        <div className="integracao-grid">
          <Card titulo="Staging" valor={resumo?.total_staging ?? 0} detalhe="Registros carregados para validação" />
          <Card titulo="Importadas" valor={resumo?.total_importado_final ?? 0} detalhe="Registros consolidados no sistema" />
          <Card titulo="Ativas importadas" valor={resumo?.total_importado_ativo ?? 0} detalhe="Registros ativos oriundos do App" />
          <Card titulo="Problemas" valor={consistencia?.resumo?.registros_afetados ?? 0} detalhe="Achados de consistência" />
        </div>

        <section className="integracao-section">
          <h3>Status do staging</h3>
          <div className="integracao-status-lista">
            {Object.entries(statusResumo).length === 0 ? <p>Nenhum registro em staging.</p> : null}
            {Object.entries(statusResumo).map(([status, total]) => (
              <button key={status} type="button" onClick={() => { setAba("rastreabilidade"); carregarRastreabilidadePorStatus(status); }}>
                <Badge tipo={status.toLowerCase()}>{status}</Badge>
                <strong>{total}</strong>
              </button>
            ))}
          </div>
        </section>

        <section className="integracao-section">
          <h3>Fluxo recomendado durante a convivência dos sistemas</h3>
          <ol>
            {(resumo?.fluxo_recomendado || []).map((item) => <li key={item}>{item}</li>)}
          </ol>
        </section>
      </>
    );
  }

  function renderSincronizacao() {
    return (
      <section className="integracao-section">
        <h3>Sincronização segura</h3>
        <p>
          Durante a transição, o App de Intervenções permanece como sistema mestre. Este painel acompanha staging,
          consistência, checkpoints e rastreabilidade antes de qualquer consolidação definitiva.
        </p>
        <div className="integracao-grid compacta">
          <Card titulo="Último batch" valor={resumo?.ultimo_batch?.batch_id || "-"} detalhe={resumo?.ultimo_batch?.status || "Sem lote"} />
          <Card titulo="Último checkpoint" valor={resumo?.ultimo_checkpoint?.etapa || "-"} detalhe={formatarData(resumo?.ultimo_checkpoint?.criado_em)} />
          <Card titulo="Duplicados" valor={statusResumo.DUPLICADO || 0} detalhe="Detectados por origem" />
          <Card titulo="Rejeitados" valor={statusResumo.REJEITADO || 0} detalhe="Exigem revisão" />
        </div>
        <div className="integracao-actions">
          <button type="button" onClick={carregarTudo} disabled={carregando}>Atualizar painel</button>
          <span>Importação de novos JSONs e consolidação continuam disponíveis via endpoints administrativos/Swagger.</span>
        </div>
      </section>
    );
  }

  function renderCheckpoints() {
    return (
      <section className="integracao-section">
        <h3>Checkpoints</h3>
        <div className="table-scroll">
          <table className="integracao-table">
            <thead>
              <tr>
                <th>ID</th><th>Etapa</th><th>Descrição</th><th>Staging</th><th>Importadas</th><th>Usuário</th><th>Data</th>
              </tr>
            </thead>
            <tbody>
              {(checkpoints.checkpoints || []).map((c) => (
                <tr key={c.checkpoint_id}>
                  <td>{c.checkpoint_id}</td>
                  <td>{c.etapa}</td>
                  <td>{c.descricao || "-"}</td>
                  <td>{c.total_staging}</td>
                  <td>{c.total_importadas}</td>
                  <td>{c.criado_por || "-"}</td>
                  <td>{formatarData(c.criado_em)}</td>
                </tr>
              ))}
              {(checkpoints.checkpoints || []).length === 0 ? <tr><td colSpan="7">Nenhum checkpoint encontrado.</td></tr> : null}
            </tbody>
          </table>
        </div>
      </section>
    );
  }

  function renderConsistencia() {
    return (
      <section className="integracao-section">
        <h3>Consistência</h3>
        <div className="integracao-grid compacta">
          <Card titulo="Críticas" valor={consistencia?.resumo?.criticos || 0} />
          <Card titulo="Moderadas" valor={consistencia?.resumo?.moderados || 0} />
          <Card titulo="Informativas" valor={consistencia?.resumo?.informativos || 0} />
          <Card titulo="Registros afetados" valor={consistencia?.resumo?.registros_afetados || 0} />
        </div>
        <div className="table-scroll">
          <table className="integracao-table">
            <thead><tr><th>Regra</th><th>Criticidade</th><th>Total</th><th>Ação sugerida</th></tr></thead>
            <tbody>
              {problemas.map((p) => (
                <tr key={p.codigo}>
                  <td><strong>{p.codigo}</strong><br /><span>{p.descricao}</span></td>
                  <td><Badge tipo={p.criticidade.toLowerCase()}>{p.criticidade}</Badge></td>
                  <td>{p.total}</td>
                  <td>{p.acao_sugerida}</td>
                </tr>
              ))}
              {problemas.length === 0 ? <tr><td colSpan="4">Nenhum problema de consistência identificado.</td></tr> : null}
            </tbody>
          </table>
        </div>
      </section>
    );
  }

  function renderRastreabilidade() {
    return (
      <section className="integracao-section">
        <h3>Rastreabilidade</h3>
        <div className="integracao-filtros">
          <button className={!filtroStatus ? "active" : ""} onClick={() => carregarRastreabilidadePorStatus("")}>Todos</button>
          {Object.keys(statusResumo).map((status) => (
            <button key={status} className={filtroStatus === status ? "active" : ""} onClick={() => carregarRastreabilidadePorStatus(status)}>{status}</button>
          ))}
        </div>
        <div className="table-scroll">
          <table className="integracao-table">
            <thead>
              <tr><th>Origem</th><th>Paciente</th><th>Data</th><th>Intervenção</th><th>Status</th><th>Destino</th><th>Batch</th></tr>
            </thead>
            <tbody>
              {(rastreabilidade.registros || []).map((r) => (
                <tr key={`${r.origem_sistema}-${r.origem_id}-${r.id}`}>
                  <td>{r.origem_sistema}<br /><small>ID {r.origem_id}</small></td>
                  <td>{r.paciente_nome || "-"}</td>
                  <td>{r.data_atendimento || "-"}</td>
                  <td>{r.tipos_intervencao || r.motivo_atendimento || "-"}</td>
                  <td><Badge tipo={(r.status || "").toLowerCase()}>{r.status}</Badge></td>
                  <td>{r.intervencao_id_destino ? `#${r.intervencao_id_destino}` : "-"}</td>
                  <td>{r.batch_id}<br /><small>{r.batch_importacao || "não consolidado"}</small></td>
                </tr>
              ))}
              {(rastreabilidade.registros || []).length === 0 ? <tr><td colSpan="7">Nenhum registro encontrado.</td></tr> : null}
            </tbody>
          </table>
        </div>
      </section>
    );
  }

  return (
    <div className="integracao-intervencoes-page">
      <section className="integracao-hero">
        <div>
          <p className="workspace-eyebrow">Transição segura</p>
          <h2>Integração das Intervenções</h2>
          <p>
            Painel administrativo para acompanhar a convivência entre o App de Intervenções em produção e o Sistema Farmácia Escola.
          </p>
        </div>
        <div className="integracao-hero-status">
          <Badge tipo={consistencia?.ok ? "validado" : "moderada"}>{consistencia?.ok ? "Consistente" : "Revisar"}</Badge>
          <span>{resumo?.origem_sistema || "APP_INTERVENCOES"}</span>
        </div>
      </section>

      {erro ? <div className="integracao-alerta">{erro}</div> : null}

      <section className="workspace-tabs integracao-tabs" aria-label="Painel de integração">
        {ABAS.map((item) => (
          <button key={item.key} type="button" className={aba === item.key ? "active" : ""} onClick={() => setAba(item.key)}>
            {item.label}
          </button>
        ))}
      </section>

      {carregando ? <p className="integracao-loading">Carregando dados da integração...</p> : null}

      {aba === "resumo" && renderResumo()}
      {aba === "sincronizacao" && renderSincronizacao()}
      {aba === "checkpoints" && renderCheckpoints()}
      {aba === "consistencia" && renderConsistencia()}
      {aba === "rastreabilidade" && renderRastreabilidade()}
    </div>
  );
}
