import { useEffect, useMemo, useState } from "react";
import { api } from "../../api/api";
import "./AnalyticsWorkspace.css";

function BarList({ title, items = [], labelKey = "rotulo", valueKey = "total", empty = "Sem dados." }) {
  const max = Math.max(...items.map((item) => Number(item?.[valueKey] || 0)), 0);

  return (
    <div className="chart-card analytics-card">
      <h3>{title}</h3>
      {items.length === 0 ? (
        <p className="muted">{empty}</p>
      ) : (
        <div className="analytics-bar-list">
          {items.map((item, index) => {
            const value = Number(item?.[valueKey] || 0);
            const width = max > 0 ? Math.max((value / max) * 100, 6) : 0;
            const label = item?.[labelKey] || item?.codigo || item?.grupo || "Não informado";
            return (
              <div className="analytics-bar-row" key={`${label}-${index}`}>
                <div className="analytics-bar-label">
                  <span>{label}</span>
                  <strong>{value}</strong>
                </div>
                <div className="analytics-bar-track">
                  <div className="analytics-bar-fill" style={{ width: `${width}%` }} />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function valueFromResumo(resumo, key, fallback = 0) {
  const value = resumo?.[key];
  return value === null || value === undefined ? fallback : value;
}

export default function IntervencoesPadronizadasIndicadores() {
  const [dados, setDados] = useState(null);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState("");

  useEffect(() => {
    carregarIndicadores();
  }, []);

  async function carregarIndicadores() {
    try {
      setCarregando(true);
      setErro("");
      const response = await api.get("/consultorio/intervencoes-padronizadas/dashboard");
      setDados(response.data || {});
    } catch (error) {
      console.error("Erro ao carregar indicadores de intervenções padronizadas:", error.response?.data || error);
      setErro("Não foi possível carregar os indicadores de intervenções padronizadas.");
    } finally {
      setCarregando(false);
    }
  }

  const resumo = dados?.resumo || {};
  const porGrupo = useMemo(() => dados?.por_grupo || [], [dados]);
  const porTipo = useMemo(() => dados?.por_tipo_padronizado || [], [dados]);
  const naoMapeados = useMemo(() => dados?.nao_mapeados_prioritarios || [], [dados]);

  if (carregando) {
    return <p className="muted">Carregando indicadores de intervenções...</p>;
  }

  if (erro) {
    return (
      <div className="prontuario-tab-content">
        <p className="error-message">{erro}</p>
        <button className="secondary-button" onClick={carregarIndicadores}>Tentar novamente</button>
      </div>
    );
  }

  return (
    <div className="prontuario-tab-content analytics-workspace">
      <div className="analytics-header compact">
        <div>
          <h3>Intervenções padronizadas</h3>
          <p className="muted">
            Mapeamento dos tipos de intervenção do App de Intervenções e do Consultório para o catálogo clínico versionado.
          </p>
        </div>
        <button className="secondary-button" onClick={carregarIndicadores}>Atualizar</button>
      </div>

      <div className="kpi-grid">
        <div className="kpi-card general">
          <span>Ocorrências legadas</span>
          <strong>{valueFromResumo(resumo, "total_ocorrencias_legadas")}</strong>
        </div>
        <div className="kpi-card general">
          <span>Textos distintos</span>
          <strong>{valueFromResumo(resumo, "textos_distintos")}</strong>
        </div>
        <div className="kpi-card success">
          <span>Textos mapeados</span>
          <strong>{valueFromResumo(resumo, "textos_mapeados")}</strong>
        </div>
        <div className="kpi-card warning">
          <span>Não mapeados</span>
          <strong>{valueFromResumo(resumo, "textos_nao_mapeados")}</strong>
        </div>
        <div className="kpi-card moderate">
          <span>Taxa de mapeamento</span>
          <strong>{valueFromResumo(resumo, "taxa_mapeamento")}%</strong>
        </div>
      </div>

      <div className="dashboard-grid">
        <BarList title="Intervenções por tipo padronizado" items={porTipo} labelKey="rotulo" />
        <BarList title="Intervenções por grupo" items={porGrupo} labelKey="grupo" />
      </div>

      <div className="chart-card analytics-card">
        <h3>Textos legados não mapeados</h3>
        <p className="muted">
          Estes itens devem ser revisados antes da consolidação definitiva para evitar perda de qualidade nos indicadores.
        </p>
        {naoMapeados.length === 0 ? (
          <p className="muted">Nenhum texto legado pendente de mapeamento.</p>
        ) : (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Texto legado</th>
                  <th>Ocorrências</th>
                  <th>Fontes</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {naoMapeados.map((item, index) => (
                  <tr key={`${item.texto_legado}-${index}`}>
                    <td>{item.texto_legado || "Não informado"}</td>
                    <td>{item.total_ocorrencias || 0}</td>
                    <td>{(item.fontes || []).join(", ") || "-"}</td>
                    <td><span className="badge warning">Revisar</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {dados?.proxima_acao_recomendada && (
        <div className="info-card">
          <strong>Próxima ação recomendada:</strong> {dados.proxima_acao_recomendada}
        </div>
      )}
    </div>
  );
}
