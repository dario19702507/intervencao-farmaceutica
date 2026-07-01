import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../../api/api";
import BuscaPacienteClinico from "../../components/BuscaPacienteClinico";

function abrirPdfAutenticado(url, nomeArquivo = "documento.pdf") {
  return api.get(url, { responseType: "blob" }).then((resp) => {
    const blobUrl = window.URL.createObjectURL(new Blob([resp.data], { type: "application/pdf" }));
    const janela = window.open(blobUrl, "_blank");

    if (!janela) {
      const link = document.createElement("a");
      link.href = blobUrl;
      link.setAttribute("download", nomeArquivo);
      document.body.appendChild(link);
      link.click();
      link.remove();
    }

    setTimeout(() => window.URL.revokeObjectURL(blobUrl), 30000);
  });
}

function normalizarNomeArquivo(texto) {
  return String(texto || "documento")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-zA-Z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .toLowerCase();
}

export default function Relatorios() {
  const navigate = useNavigate();
  const [pacienteSelecionado, setPacienteSelecionado] = useState(null);
  const [pacienteId, setPacienteId] = useState("");
  const [atendimentoRapidoId, setAtendimentoRapidoId] = useState("");
  const [bioimpedanciaId, setBioimpedanciaId] = useState("");
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState("");

  function selecionarPaciente(paciente) {
    setPacienteSelecionado(paciente || null);
    setPacienteId(paciente?.id ? String(paciente.id) : "");
  }

  async function abrir(url, nomeArquivo) {
    setErro("");
    setLoading(true);
    try {
      await abrirPdfAutenticado(url, nomeArquivo);
    } catch (error) {
      console.error("Erro ao abrir documento para impressão:", error.response?.data || error);
      setErro(error.response?.data?.detail || "Não foi possível gerar o documento solicitado.");
    } finally {
      setLoading(false);
    }
  }

  function exigirPaciente(callback) {
    if (!pacienteId) {
      setErro("Selecione um paciente clínico antes de gerar este documento.");
      return;
    }
    callback();
  }

  const nomePacienteArquivo = normalizarNomeArquivo(pacienteSelecionado?.nome || `paciente_${pacienteId}`);

  return (
    <div className="print-center-page">
      <div className="print-center-header">
        <div>
          <h2>Relatórios e Impressões</h2>
          <p className="muted">
            Central única para localizar, abrir e imprimir documentos clínicos, declarações e relatórios institucionais.
          </p>
        </div>
        <button className="secondary-button" onClick={() => navigate("/inteligencia?aba=relatorios")}>Relatórios gerenciais</button>
      </div>

      {erro && <div className="form-error">{erro}</div>}
      {loading && <p className="muted">Gerando documento...</p>}

      <section className="print-panel">
        <div className="section-header-row">
          <div>
            <h3>Impressões por paciente</h3>
            <p className="muted">Documentos assistenciais do Consultório Farmacêutico.</p>
          </div>
        </div>

        <div className="print-field-full">
          <BuscaPacienteClinico
            label="Paciente clínico"
            value={pacienteId}
            selectedPaciente={pacienteSelecionado}
            onSelect={selecionarPaciente}
          />
        </div>

        <div className="print-actions-grid">
          <div className="print-action-card">
            <strong>Prontuário clínico</strong>
            <p className="muted">Resumo cadastral e clínico do paciente.</p>
            <button
              className="secondary-button"
              disabled={loading || !pacienteId}
              onClick={() => exigirPaciente(() => abrir(`/consultorio/paciente-clinico/${pacienteId}/pdf`, `prontuario_${nomePacienteArquivo}.pdf`))}
            >
              Abrir / imprimir
            </button>
          </div>

          <div className="print-action-card">
            <strong>Prontuário longitudinal</strong>
            <p className="muted">Histórico longitudinal do cuidado farmacêutico.</p>
            <button
              className="secondary-button"
              disabled={loading || !pacienteId}
              onClick={() => exigirPaciente(() => abrir(`/consultorio/paciente-clinico/${pacienteId}/prontuario-longitudinal-pdf`, `prontuario_longitudinal_${nomePacienteArquivo}.pdf`))}
            >
              Abrir / imprimir
            </button>
          </div>

          <div className="print-action-card">
            <strong>Plano de cuidado</strong>
            <p className="muted">Plano narrativo e ações estruturadas do cuidado.</p>
            <button
              className="secondary-button"
              disabled={loading || !pacienteId}
              onClick={() => exigirPaciente(() => abrir(`/consultorio/paciente-clinico/${pacienteId}/plano-cuidado-pdf`, `plano_cuidado_${nomePacienteArquivo}.pdf`))}
            >
              Abrir / imprimir
            </button>
          </div>

          <div className="print-action-card">
            <strong>Evoluções clínicas</strong>
            <p className="muted">Evoluções e registros clínicos do prontuário.</p>
            <button
              className="secondary-button"
              disabled={loading || !pacienteId}
              onClick={() => exigirPaciente(() => abrir(`/consultorio/paciente-clinico/${pacienteId}/evolucoes-clinicas-pdf`, `evolucoes_${nomePacienteArquivo}.pdf`))}
            >
              Abrir / imprimir
            </button>
          </div>

          <div className="print-action-card">
            <strong>Orientações farmacêuticas</strong>
            <p className="muted">Orientações, farmacoterapia e plano de acompanhamento.</p>
            <button
              className="secondary-button"
              disabled={loading || !pacienteId}
              onClick={() => exigirPaciente(() => abrir(`/consultorio/paciente-clinico/${pacienteId}/orientacoes-farmaceuticas-pdf`, `orientacoes_${nomePacienteArquivo}.pdf`))}
            >
              Abrir / imprimir
            </button>
          </div>

          <div className="print-action-card">
            <strong>Editar antes de imprimir</strong>
            <p className="muted">Revise medicamentos, PRM, metas, plano e evolução antes da emissão.</p>
            <button className="secondary-button" onClick={() => navigate("/atendimento/consultorio")}>Abrir consultório</button>
          </div>
        </div>
      </section>

      <section className="print-panel">
        <div className="section-header-row">
          <div>
            <h3>Declarações e laudos de serviços rápidos</h3>
            <p className="muted">Documentos emitidos a partir de atendimentos rápidos e serviços realizados.</p>
          </div>
        </div>

        <div className="print-inline-fields">
          <label>
            ID do atendimento rápido
            <input
              className="input"
              type="number"
              min="1"
              placeholder="Ex.: 12"
              value={atendimentoRapidoId}
              onChange={(e) => setAtendimentoRapidoId(e.target.value)}
            />
          </label>
          <button
            className="secondary-button"
            disabled={loading || !atendimentoRapidoId}
            onClick={() => abrir(`/consultorio/atendimento-rapido/${atendimentoRapidoId}/declaracao-pdf`, `declaracao_servico_${atendimentoRapidoId}.pdf`)}
          >
            Declaração de serviço
          </button>
        </div>

        <div className="print-inline-fields">
          <label>
            ID da bioimpedância
            <input
              className="input"
              type="number"
              min="1"
              placeholder="Ex.: 5"
              value={bioimpedanciaId}
              onChange={(e) => setBioimpedanciaId(e.target.value)}
            />
          </label>
          <button
            className="secondary-button"
            disabled={loading || !bioimpedanciaId}
            onClick={() => abrir(`/consultorio/bioimpedancia/${bioimpedanciaId}/laudo-pdf`, `laudo_bioimpedancia_${bioimpedanciaId}.pdf`)}
          >
            Laudo de bioimpedância
          </button>
        </div>

        <div className="care-next-actions">
          <button className="secondary-button" onClick={() => navigate("/atendimento/servicos")}>Abrir serviços rápidos</button>
        </div>
      </section>

      <section className="print-panel">
        <div className="section-header-row">
          <div>
            <h3>Relatórios institucionais</h3>
            <p className="muted">Relatórios, indicadores e documentos de gestão já padronizados com identidade institucional.</p>
          </div>
        </div>

        <div className="print-actions-grid">
          <div className="print-action-card">
            <strong>Relatórios gerenciais</strong>
            <p className="muted">Operacional, vigências e documental, com PDF, Excel e CSV.</p>
            <button className="secondary-button" onClick={() => navigate("/inteligencia?aba=relatorios")}>Abrir</button>
          </div>

          <div className="print-action-card">
            <strong>Resolução de alertas</strong>
            <p className="muted">PDF de acompanhamento da resolução dos alertas clínicos.</p>
            <button
              className="secondary-button"
              disabled={loading}
              onClick={() => abrir("/consultorio/relatorio-resolucao-alertas-pdf", "relatorio_resolucao_alertas.pdf")}
            >
              Abrir / imprimir
            </button>
          </div>

          <div className="print-action-card">
            <strong>Analytics</strong>
            <p className="muted">Indicadores assistenciais, epidemiológicos, científicos e farmacoterapêuticos.</p>
            <button className="secondary-button" onClick={() => navigate("/inteligencia")}>Abrir Analytics</button>
          </div>

          <div className="print-action-card">
            <strong>Documentos</strong>
            <p className="muted">Pacotes documentais, vigências, OCR, pendências e histórico.</p>
            <button className="secondary-button" onClick={() => navigate("/documentos")}>Abrir Documentos</button>
          </div>
        </div>
      </section>
    </div>
  );
}
