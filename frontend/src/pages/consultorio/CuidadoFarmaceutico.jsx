import { useEffect, useMemo, useState } from "react";
import { api } from "../../api/api";
import "./CuidadoFarmaceutico.css";

const CRITICIDADE_LABEL = {
  CRITICA: "Crítica",
  MODERADA: "Moderada",
  INFORMATIVA: "Informativa",
};

const CATEGORIA_LABEL = {
  ASSISTENCIAL: "Assistencial",
  CEAF: "CEAF",
  DOCUMENTAL: "Documental",
  FARMACOTERAPEUTICA: "Farmacoterapêutica",
};

function Badge({ children, tipo = "neutral" }) {
  return <span className={`cuidado-badge ${tipo}`}>{children}</span>;
}

function criticidadeClasse(valor) {
  const v = String(valor || "").toLowerCase();
  if (v === "critica") return "critica";
  if (v === "moderada") return "moderada";
  if (v === "informativa") return "informativa";
  return "neutral";
}

export default function CuidadoFarmaceutico() {
  const [opcoes, setOpcoes] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [pendencias, setPendencias] = useState([]);
  const [filtroCriticidade, setFiltroCriticidade] = useState("");
  const [filtroCategoria, setFiltroCategoria] = useState("");
  const [erro, setErro] = useState("");
  const [loading, setLoading] = useState(true);

  async function carregar() {
    setLoading(true);
    setErro("");
    try {
      const [opcoesResp, dashboardResp, pendenciasResp] = await Promise.allSettled([
        api.get("/consultorio/atencao-farmaceutica/opcoes"),
        api.get("/consultorio/atencao-farmaceutica/dashboard"),
        api.get("/consultorio/atencao-farmaceutica/pendencias", {
          params: {
            criticidade: filtroCriticidade || undefined,
            categoria: filtroCategoria || undefined,
            limite: 80,
            limite_pacientes: 80,
          },
        }),
      ]);

      if (opcoesResp.status === "fulfilled") setOpcoes(opcoesResp.value.data);
      if (dashboardResp.status === "fulfilled") setDashboard(dashboardResp.value.data);
      if (pendenciasResp.status === "fulfilled") setPendencias(pendenciasResp.value.data?.pendencias || []);

      const falhas = [opcoesResp, dashboardResp, pendenciasResp].filter((item) => item.status === "rejected");
      if (falhas.length) {
        console.warn("Centro de Atenção Farmacêutica carregado parcialmente.", falhas);
        setErro("Alguns indicadores não puderam ser carregados agora. O restante do consultório permanece disponível.");
      }
    } catch (e) {
      console.error(e);
      setErro("Não foi possível carregar o Centro de Atenção Farmacêutica.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    carregar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const pendenciasPorCategoria = useMemo(() => {
    const grupos = { ASSISTENCIAL: [], CEAF: [], DOCUMENTAL: [], FARMACOTERAPEUTICA: [] };
    for (const p of pendencias) {
      if (!grupos[p.categoria]) grupos[p.categoria] = [];
      grupos[p.categoria].push(p);
    }
    return grupos;
  }, [pendencias]);

  return (
    <div className="cuidado-page">
      <div className="cuidado-header">
        <div>
          <p className="eyebrow">Consultório Farmacêutico</p>
          <h1>Centro de Atenção Farmacêutica</h1>
          <p>
            Motor de pendências assistenciais, CEAF, documentais e farmacoterapêuticas.
            O sistema identifica prioridades, mas nenhuma ação é executada automaticamente.
          </p>
        </div>
        <button onClick={carregar} disabled={loading}>Atualizar</button>
      </div>

      {erro && <div className="alerta-erro">{erro}</div>}
      {loading && <div className="card">Carregando...</div>}

      {dashboard && (
        <div className="cuidado-grid">
          <div className="card indicador"><span>Pendências totais</span><strong>{dashboard.total_pendencias ?? 0}</strong></div>
          <div className="card indicador critica"><span>Críticas</span><strong>{dashboard.pendencias_criticas ?? 0}</strong></div>
          <div className="card indicador moderada"><span>Moderadas</span><strong>{dashboard.pendencias_moderadas ?? 0}</strong></div>
          <div className="card indicador informativa"><span>Informativas</span><strong>{dashboard.pendencias_informativas ?? 0}</strong></div>
          <div className="card indicador"><span>Pacientes impactados</span><strong>{dashboard.pacientes_impactados ?? 0}</strong></div>
        </div>
      )}

      <div className="card filtros-cuidado">
        <div>
          <label>Criticidade</label>
          <select value={filtroCriticidade} onChange={(e) => setFiltroCriticidade(e.target.value)}>
            <option value="">Todas</option>
            {(opcoes?.criticidades || []).map((c) => <option key={c} value={c}>{CRITICIDADE_LABEL[c] || c}</option>)}
          </select>
        </div>
        <div>
          <label>Categoria</label>
          <select value={filtroCategoria} onChange={(e) => setFiltroCategoria(e.target.value)}>
            <option value="">Todas</option>
            {(opcoes?.categorias || []).map((c) => <option key={c} value={c}>{CATEGORIA_LABEL[c] || c}</option>)}
          </select>
        </div>
        <button onClick={carregar} disabled={loading}>Aplicar filtros</button>
      </div>

      {dashboard?.fila_priorizada?.length > 0 && (
        <div className="card">
          <h2>Fila priorizada</h2>
          <p className="muted">Principais pacientes que exigem ação farmacêutica.</p>
          <div className="pendencias-lista compacta">
            {dashboard.fila_priorizada.slice(0, 8).map((p) => (
              <div key={p.id} className="pendencia-item">
                <div>
                  <strong>{p.paciente_nome}</strong>
                  <p>{p.titulo}</p>
                </div>
                <Badge tipo={criticidadeClasse(p.criticidade)}>{CRITICIDADE_LABEL[p.criticidade] || p.criticidade}</Badge>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="cuidado-sections">
        {Object.entries(pendenciasPorCategoria).map(([categoria, itens]) => (
          <div className="card" key={categoria}>
            <h2>{CATEGORIA_LABEL[categoria] || categoria}</h2>
            <p className="muted">{itens.length} pendência(s)</p>
            <div className="pendencias-lista">
              {itens.length === 0 && <p className="muted">Nenhuma pendência identificada nesta categoria.</p>}
              {itens.slice(0, 20).map((p) => (
                <div key={p.id} className="pendencia-card">
                  <div className="pendencia-topo">
                    <strong>{p.paciente_nome}</strong>
                    <Badge tipo={criticidadeClasse(p.criticidade)}>{CRITICIDADE_LABEL[p.criticidade] || p.criticidade}</Badge>
                  </div>
                  <h3>{p.titulo}</h3>
                  <p>{p.descricao}</p>
                  <p className="muted"><strong>Ação sugerida:</strong> {p.acao_sugerida}</p>
                  <div className="pendencia-meta">
                    <span>{p.tipo}</span>
                    {p.dias !== null && p.dias !== undefined && <span>{p.dias} dia(s)</span>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {opcoes && (
        <div className="card">
          <h2>Matriz de regras</h2>
          <p className="muted">Limites iniciais configuráveis no backend.</p>
          <div className="regras-grid">
            {Object.entries(opcoes.regras || {}).map(([chave, valor]) => (
              <div key={chave}><span>{chave}</span><strong>{valor}</strong></div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
