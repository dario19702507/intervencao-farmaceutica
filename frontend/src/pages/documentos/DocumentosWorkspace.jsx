import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../../api/api";
import DocumentosPaciente from "./DocumentosPaciente";
import ProcessosDocumentais from "./ProcessosDocumentais";
import OCRDocumental from "./OCRDocumental";
import Relatorios from "../relatorios/Relatorios.jsx";
import "./DocumentosWorkspace.css";

const ABAS = [
  { key: "visao-geral", label: "Visão Geral", descricao: "Indicadores e atalhos do fluxo documental" },
  { key: "processos", label: "Pacotes", descricao: "Inclusões, renovações, adequações e encerramentos" },
  { key: "gestao", label: "Documentos", descricao: "Upload, validade, vigência e histórico documental" },
  { key: "ocr", label: "OCR", descricao: "Extração, classificação e revisão de campos" },
  { key: "vigencias", label: "Vigências", descricao: "Laudos, receitas, exames e vencimentos" },
  { key: "pendencias", label: "Pendências", descricao: "Pendências documentais priorizadas" },
  { key: "impressao", label: "Impressões", descricao: "Central de impressão de prontuários, laudos e relatórios" },
];

function normalizarCriticidade(valor) {
  const v = String(valor || "").toUpperCase();
  if (v.includes("CRIT")) return "critica";
  if (v.includes("MOD")) return "moderada";
  if (v.includes("INFO")) return "informativa";
  return "neutra";
}

function numero(valor) {
  return Number(valor || 0).toLocaleString("pt-BR");
}

function CardIndicador({ titulo, valor, detalhe, tipo = "neutra" }) {
  return (
    <div className={`docws-card ${tipo}`}>
      <span>{titulo}</span>
      <strong>{numero(valor)}</strong>
      {detalhe && <small>{detalhe}</small>}
    </div>
  );
}

export default function DocumentosWorkspace() {
  const [searchParams, setSearchParams] = useSearchParams();
  const abaInicial = searchParams.get("aba") || "visao-geral";
  const [aba, setAba] = useState(ABAS.some((a) => a.key === abaInicial) ? abaInicial : "visao-geral");
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState("");
  const [dados, setDados] = useState({
    validade: null,
    vencimentos: [],
    processos: null,
    status: null,
    pendencias: [],
  });

  useEffect(() => {
    setSearchParams(aba === "visao-geral" ? {} : { aba }, { replace: true });
  }, [aba, setSearchParams]);

  useEffect(() => {
    async function carregarResumo() {
      setLoading(true);
      setErro("");
      try {
        const [validade, vencimentos, processos, status, pendencias] = await Promise.allSettled([
          api.get("/consultorio/documentos/validade-dashboard"),
          api.get("/consultorio/documentos/vencimentos"),
          api.get("/consultorio/processos-documentais/dashboard"),
          api.get("/consultorio/documentos/status-dashboard"),
          api.get("/consultorio/atencao-farmaceutica/pendencias"),
        ]);

        setDados({
          validade: validade.status === "fulfilled" ? validade.value.data : null,
          vencimentos: vencimentos.status === "fulfilled" ? vencimentos.value.data : [],
          processos: processos.status === "fulfilled" ? processos.value.data : null,
          status: status.status === "fulfilled" ? status.value.data : null,
          pendencias: pendencias.status === "fulfilled" ? pendencias.value.data : [],
        });
      } catch (error) {
        console.error("Erro ao carregar resumo documental", error);
        setErro("Não foi possível carregar o resumo documental.");
      } finally {
        setLoading(false);
      }
    }

    carregarResumo();
  }, []);

  const pendenciasDocumentais = useMemo(() => {
    const lista = Array.isArray(dados.pendencias) ? dados.pendencias : dados.pendencias?.itens || [];
    return lista.filter((item) => {
      const texto = `${item.categoria || ""} ${item.tipo || ""} ${item.titulo || ""}`.toUpperCase();
      return texto.includes("DOCUMENT") || texto.includes("LAUDO") || texto.includes("RECEITA") || texto.includes("OCR") || texto.includes("PACOTE");
    });
  }, [dados.pendencias]);

  const vencimentosLista = Array.isArray(dados.vencimentos) ? dados.vencimentos : dados.vencimentos?.itens || [];

  const resumo = {
    processosAtivos: dados.processos?.total_processos || dados.processos?.total || 0,
    processosIncompletos: dados.processos?.incompletos || dados.processos?.total_incompletos || 0,
    documentosVencidos: dados.validade?.vencidos || dados.validade?.total_vencidos || 0,
    documentosAVencer: dados.validade?.a_vencer || dados.validade?.total_a_vencer || vencimentosLista.length || 0,
    documentosRejeitados: dados.status?.REJEITADO || dados.status?.rejeitados || dados.status?.total_rejeitados || 0,
    pendencias: pendenciasDocumentais.length,
  };

  return (
    <div className="documentos-workspace">
      <section className="docws-hero">
        <div>
          <p className="eyebrow">Workspace</p>
          <h2>Documentos</h2>
          <p>
            Gestão documental, pacotes, OCR, vigências e pendências em uma única área de trabalho.
          </p>
        </div>
        <div className="docws-hero-actions">
          <button className="secondary-button" onClick={() => setAba("processos")}>Abrir pacotes</button>
          <button className="primary-button" onClick={() => setAba("ocr")}>Revisar OCR</button>
        </div>
      </section>

      <nav className="docws-tabs" aria-label="Abas do workspace de documentos">
        {ABAS.map((item) => (
          <button
            key={item.key}
            type="button"
            className={aba === item.key ? "active" : ""}
            onClick={() => setAba(item.key)}
            title={item.descricao}
          >
            {item.label}
          </button>
        ))}
      </nav>

      {aba === "visao-geral" && (
        <section className="docws-panel">
          <div className="docws-panel-header">
            <div>
              <h3>Visão Geral Documental</h3>
              <p>Resumo operacional para priorizar conferência, OCR e regularização de documentos.</p>
            </div>
            {loading && <span className="badge">Carregando...</span>}
          </div>

          {erro && <div className="alerta warning">{erro}</div>}

          <div className="docws-grid">
            <CardIndicador titulo="Processos ativos" valor={resumo.processosAtivos} detalhe="Pacotes documentais" />
            <CardIndicador titulo="Processos incompletos" valor={resumo.processosIncompletos} detalhe="Exigem revisão" tipo="moderada" />
            <CardIndicador titulo="Documentos vencidos" valor={resumo.documentosVencidos} detalhe="Prioridade alta" tipo="critica" />
            <CardIndicador titulo="Documentos a vencer" valor={resumo.documentosAVencer} detalhe="Próximos vencimentos" tipo="moderada" />
            <CardIndicador titulo="Rejeitados" valor={resumo.documentosRejeitados} detalhe="Correção manual" tipo="moderada" />
            <CardIndicador titulo="Pendências" valor={resumo.pendencias} detalhe="Centro de Atenção" tipo="informativa" />
          </div>

          <div className="docws-shortcuts">
            <button onClick={() => setAba("processos")}>Pacotes Documentais</button>
            <button onClick={() => setAba("gestao")}>Documentos do Paciente</button>
            <button onClick={() => setAba("ocr")}>OCR Documental</button>
            <button onClick={() => setAba("vigencias")}>Vigências</button>
            <button onClick={() => setAba("pendencias")}>Pendências</button>
            <button onClick={() => setAba("impressao")}>Central de Impressões</button>
          </div>
        </section>
      )}

      {aba === "processos" && (
        <section className="docws-panel docws-embedded">
          <ProcessosDocumentais />
        </section>
      )}

      {aba === "gestao" && (
        <section className="docws-panel docws-embedded">
          <DocumentosPaciente />
        </section>
      )}

      {aba === "ocr" && (
        <section className="docws-panel docws-embedded">
          <OCRDocumental />
        </section>
      )}

      {aba === "vigencias" && (
        <section className="docws-panel">
          <div className="docws-panel-header">
            <div>
              <h3>Vigências e Vencimentos</h3>
              <p>Resumo de documentos vencidos ou próximos do vencimento. Para editar, use a aba Documentos.</p>
            </div>
            <button className="secondary-button" onClick={() => setAba("gestao")}>Editar documentos</button>
          </div>

          {vencimentosLista.length === 0 ? (
            <div className="empty-state">Nenhum vencimento retornado pelo dashboard documental.</div>
          ) : (
            <div className="docws-table-wrap">
              <table className="docws-table">
                <thead>
                  <tr>
                    <th>Paciente</th>
                    <th>Documento</th>
                    <th>Vencimento</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {vencimentosLista.slice(0, 100).map((item, idx) => (
                    <tr key={item.id || idx}>
                      <td>{item.paciente_nome || item.paciente || "-"}</td>
                      <td>{item.tipo_documento || item.documento || item.titulo || "-"}</td>
                      <td>{item.data_vencimento || item.validade_fim || item.vencimento || "-"}</td>
                      <td><span className="badge">{item.status || item.situacao || "Acompanhar"}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}

      {aba === "impressao" && (
        <section className="docws-panel docws-embedded">
          <Relatorios />
        </section>
      )}

      {aba === "pendencias" && (
        <section className="docws-panel">
          <div className="docws-panel-header">
            <div>
              <h3>Pendências Documentais</h3>
              <p>Itens documentais captados pelo Centro de Atenção Farmacêutica.</p>
            </div>
          </div>

          {pendenciasDocumentais.length === 0 ? (
            <div className="empty-state">Nenhuma pendência documental identificada no momento.</div>
          ) : (
            <div className="docws-pendencias">
              {pendenciasDocumentais.map((item, idx) => (
                <article key={item.id || idx} className={`docws-pendencia ${normalizarCriticidade(item.criticidade)}`}>
                  <div>
                    <strong>{item.paciente_nome || item.paciente || "Paciente não informado"}</strong>
                    <p>{item.titulo || item.tipo || item.descricao || "Pendência documental"}</p>
                    {item.acao_sugerida && <small>Ação sugerida: {item.acao_sugerida}</small>}
                  </div>
                  <span>{item.criticidade || "INFORMATIVA"}</span>
                </article>
              ))}
            </div>
          )}
        </section>
      )}
    </div>
  );
}
