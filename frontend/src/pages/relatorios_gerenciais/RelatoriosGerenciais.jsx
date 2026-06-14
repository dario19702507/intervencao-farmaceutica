import { useEffect, useMemo, useState } from "react";
import { api } from "../../api/api";
import "./RelatoriosGerenciais.css";

const TIPOS = [
  { key: "operacional", label: "Operacional" },
  { key: "vigencias", label: "Vigências" },
  { key: "documental", label: "Documental" },
];

function hojeISO() {
  return new Date().toISOString().slice(0, 10);
}

function baixarArquivo(url, nome) {
  return api.get(url, { responseType: "blob" }).then((resp) => {
    const blobUrl = window.URL.createObjectURL(new Blob([resp.data]));
    const link = document.createElement("a");
    link.href = blobUrl;
    link.setAttribute("download", nome);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(blobUrl);
  });
}

function abrirArquivo(url) {
  return api.get(url, { responseType: "blob" }).then((resp) => {
    const blobUrl = window.URL.createObjectURL(new Blob([resp.data], { type: "application/pdf" }));
    window.open(blobUrl, "_blank");
  });
}

function Indicadores({ indicadores }) {
  const entries = Object.entries(indicadores || {});
  if (!entries.length) return <p className="rg-muted">Sem indicadores para exibir.</p>;
  return (
    <div className="rg-grid">
      {entries.map(([key, value]) => (
        <div className="rg-card" key={key}>
          <span>{key.replaceAll("_", " ")}</span>
          <strong>{value}</strong>
        </div>
      ))}
    </div>
  );
}

function Tabela({ titulo, dados }) {
  if (!dados || !dados.length) return null;
  const colunas = Object.keys(dados[0]).slice(0, 8);
  return (
    <section className="rg-section">
      <h3>{titulo}</h3>
      <div className="rg-table-wrap">
        <table className="rg-table">
          <thead>
            <tr>{colunas.map((c) => <th key={c}>{c.replaceAll("_", " ")}</th>)}</tr>
          </thead>
          <tbody>
            {dados.map((row, idx) => (
              <tr key={idx}>{colunas.map((c) => <td key={c}>{row[c] ?? "-"}</td>)}</tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default function RelatoriosGerenciais() {
  const [tipo, setTipo] = useState("operacional");
  const [dataInicio, setDataInicio] = useState(hojeISO());
  const [dataFim, setDataFim] = useState(hojeISO());
  const [dataReferencia, setDataReferencia] = useState(hojeISO());
  const [relatorio, setRelatorio] = useState(null);
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState("");

  const queryParams = useMemo(() => {
    if (tipo === "vigencias") {
      return { data_referencia: dataReferencia || undefined };
    }
    return { data_inicio: dataInicio || undefined, data_fim: dataFim || undefined };
  }, [tipo, dataInicio, dataFim, dataReferencia]);

  async function carregar() {
    setLoading(true);
    setErro("");
    try {
      const resp = await api.get(`/consultorio/relatorios-gerenciais/${tipo}`, { params: queryParams });
      setRelatorio(resp.data);
    } catch (e) {
      console.error(e);
      setErro("Não foi possível carregar o relatório gerencial.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    carregar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tipo]);

  async function exportar(formato) {
    const params = new URLSearchParams();
    Object.entries(queryParams).forEach(([k, v]) => {
      if (v) params.append(k, v);
    });
    const suffix = params.toString() ? `?${params.toString()}` : "";
    const ext = formato === "pdf" ? "pdf" : formato === "xlsx" ? "xlsx" : "csv";
    await baixarArquivo(`/consultorio/relatorios-gerenciais/${tipo}/${formato}${suffix}`, `relatorio_${tipo}.${ext}`);
  }

  async function imprimirPdf() {
    const params = new URLSearchParams();
    Object.entries(queryParams).forEach(([k, v]) => {
      if (v) params.append(k, v);
    });
    const suffix = params.toString() ? `?${params.toString()}` : "";
    await abrirArquivo(`/consultorio/relatorios-gerenciais/${tipo}/pdf${suffix}`);
  }

  return (
    <div className="rg-page">
      <div className="rg-header">
        <div>
          <h1>Relatórios Gerenciais</h1>
          <p>Exportações operacionais para acompanhamento da Farmácia Escola.</p>
        </div>
        <div className="rg-actions">
          <button onClick={() => exportar("xlsx")}>Exportar Excel</button>
          <button onClick={() => exportar("csv")}>Exportar CSV</button>
          <button onClick={() => exportar("pdf")}>Baixar PDF</button>
          <button onClick={imprimirPdf}>Abrir / imprimir PDF</button>
        </div>
      </div>

      <div className="rg-filters">
        <label>
          Tipo de relatório
          <select value={tipo} onChange={(e) => setTipo(e.target.value)}>
            {TIPOS.map((t) => <option key={t.key} value={t.key}>{t.label}</option>)}
          </select>
        </label>

        {tipo === "vigencias" ? (
          <label>
            Data de referência
            <input type="date" value={dataReferencia} onChange={(e) => setDataReferencia(e.target.value)} />
          </label>
        ) : (
          <>
            <label>
              Data início
              <input type="date" value={dataInicio} onChange={(e) => setDataInicio(e.target.value)} />
            </label>
            <label>
              Data fim
              <input type="date" value={dataFim} onChange={(e) => setDataFim(e.target.value)} />
            </label>
          </>
        )}

        <button className="rg-primary" onClick={carregar} disabled={loading}>{loading ? "Carregando..." : "Atualizar"}</button>
      </div>

      {erro && <div className="rg-error">{erro}</div>}

      {relatorio && (
        <>
          <section className="rg-section">
            <h2>{relatorio.tipo}</h2>
            {relatorio.periodo && <p className="rg-muted">Período: {relatorio.periodo.inicio} a {relatorio.periodo.fim}</p>}
            {relatorio.data_referencia && <p className="rg-muted">Data de referência: {relatorio.data_referencia}</p>}
            <Indicadores indicadores={relatorio.indicadores} />
          </section>

          <Tabela titulo="Eventos" dados={relatorio.eventos} />
          <Tabela titulo="Processos vencendo" dados={relatorio.processos_vencendo} />
          <Tabela titulo="Processos vencidos" dados={relatorio.processos_vencidos} />
          <Tabela titulo="Processos incompletos" dados={relatorio.processos_incompletos} />
          <Tabela titulo="Documentos rejeitados" dados={relatorio.documentos_rejeitados} />
        </>
      )}
    </div>
  );
}
