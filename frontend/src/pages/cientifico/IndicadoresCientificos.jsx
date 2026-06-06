import { useEffect, useMemo, useState } from "react";
import { api } from "../../api/api";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
} from "recharts";

const CORES = ["#0f766e", "#2563eb", "#9333ea", "#f59e0b", "#dc2626", "#64748b"];

function objetoParaGrafico(obj = {}) {
  return Object.entries(obj || {}).map(([name, value]) => ({
    name,
    value: Number(value || 0),
  }));
}

function baixarBlob(blob, nomeArquivo) {
  const url = window.URL.createObjectURL(new Blob([blob]));
  const link = document.createElement("a");

  link.href = url;
  link.setAttribute("download", nomeArquivo);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

export default function IndicadoresCientificos() {
  const [indicadores, setIndicadores] = useState(null);
  const [serieTemporal, setSerieTemporal] = useState([]);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState("");

  useEffect(() => {
    carregarDados();
  }, []);

  async function carregarDados() {
    try {
      setCarregando(true);
      setErro("");

      const [indicadoresResp, serieResp] = await Promise.all([
        api.get("/consultorio/indicadores-cientificos"),
        api.get("/consultorio/serie-temporal-cientifica"),
      ]);

      setIndicadores(indicadoresResp.data || {});
      setSerieTemporal(Array.isArray(serieResp.data) ? serieResp.data : []);
    } catch (error) {
      console.error("Erro ao carregar indicadores científicos:", error);
      setErro("Não foi possível carregar os indicadores científicos.");
      setIndicadores(null);
      setSerieTemporal([]);
    } finally {
      setCarregando(false);
    }
  }

  async function exportarExcelCientifico() {
    try {
      const response = await api.get("/consultorio/exportacao-cientifica-excel", {
        responseType: "blob",
      });

      baixarBlob(response.data, "exportacao_cientifica.xlsx");
    } catch (error) {
      console.error("Erro ao exportar Excel científico:", error);
      alert("Erro ao exportar Excel científico.");
    }
  }

  async function exportarPesquisaAnonimizada() {
    try {
      const response = await api.get("/consultorio/exportacao-pesquisa-anonimizada", {
        responseType: "blob",
      });

      baixarBlob(response.data, "pesquisa_anonimizada_completa.xlsx");
    } catch (error) {
      console.error("Erro ao exportar pesquisa anonimizada:", error);
      alert("Erro ao exportar pesquisa anonimizada.");
    }
  }

  async function abrirRelatorioPdf() {
    try {
      const response = await api.get("/consultorio/relatorio-cientifico-pdf", {
        responseType: "blob",
      });

      const url = window.URL.createObjectURL(new Blob([response.data], { type: "application/pdf" }));
      window.open(url, "_blank");
    } catch (error) {
      console.error("Erro ao abrir relatório científico PDF:", error);
      alert("Erro ao abrir relatório científico em PDF.");
    }
  }

  const assistencial = indicadores?.assistencial || {};
  const perfilPacientes = indicadores?.perfil_pacientes || {};
  const cardiovascular = indicadores?.cardiovascular || {};
  const glicemico = indicadores?.glicemico || {};
  const antropometrico = indicadores?.antropometrico || {};
  const intervencoes = indicadores?.intervencoes_farmaceuticas || {};

  const sexoGrafico = useMemo(
    () => objetoParaGrafico(perfilPacientes.sexo || {}),
    [perfilPacientes]
  );

  if (carregando && !indicadores) {
    return (
      <div className="page-container">
        <p className="muted">Carregando indicadores científicos...</p>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="section-header-row">
        <div>
          <h1>Painel Científico</h1>
          <p className="muted">
            Indicadores assistenciais, epidemiológicos e científicos consolidados.
          </p>
        </div>

        <div className="header-actions">
          <button className="secondary-button" onClick={carregarDados}>
            Atualizar
          </button>

          <button className="secondary-button" onClick={abrirRelatorioPdf}>
            PDF científico
          </button>

          <button className="secondary-button" onClick={exportarExcelCientifico}>
            Excel científico
          </button>

          <button className="primary-button" onClick={exportarPesquisaAnonimizada}>
            Pesquisa anonimizada
          </button>
        </div>
      </div>

      {erro && <div className="alert-card danger">{erro}</div>}

      <div className="cards-grid four">
        <MetricCard titulo="Pacientes clínicos" valor={assistencial.total_pacientes_clinicos || 0} />
        <MetricCard titulo="Aferições de PA" valor={assistencial.total_afericoes_pa || 0} />
        <MetricCard titulo="Glicemias" valor={assistencial.total_glicemias || 0} />
        <MetricCard titulo="Intervenções" valor={assistencial.total_intervencoes || 0} />
      </div>

      <div className="cards-grid four">
        <MetricCard titulo="Bioimpedâncias" valor={assistencial.total_bioimpedancias || 0} />
        <MetricCard titulo="PAS média" valor={cardiovascular.media_pas || 0} sufixo="mmHg" />
        <MetricCard titulo="Glicemia média" valor={glicemico.media_glicemia || 0} sufixo="mg/dL" />
        <MetricCard titulo="IMC médio" valor={antropometrico.media_imc || 0} />
      </div>

      <div className="cards-grid two">
        <div className="form-card">
          <h3>Série temporal científica</h3>

          {serieTemporal.length === 0 ? (
            <p className="muted">Sem dados temporais disponíveis.</p>
          ) : (
            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={serieTemporal}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="mes" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="afericoes_pa" name="PA" stroke="#0f766e" />
                <Line type="monotone" dataKey="glicemias" name="Glicemias" stroke="#2563eb" />
                <Line type="monotone" dataKey="bioimpedancias" name="Bioimpedâncias" stroke="#9333ea" />
                <Line type="monotone" dataKey="intervencoes" name="Intervenções" stroke="#f59e0b" />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="form-card">
          <h3>Perfil dos pacientes por sexo</h3>

          {sexoGrafico.length === 0 ? (
            <p className="muted">Sem dados de perfil disponíveis.</p>
          ) : (
            <ResponsiveContainer width="100%" height={320}>
              <PieChart>
                <Pie
                  data={sexoGrafico}
                  dataKey="value"
                  nameKey="name"
                  outerRadius={110}
                  label
                >
                  {sexoGrafico.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={CORES[index % CORES.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      <div className="cards-grid two">
        <div className="form-card">
          <h3>Produção assistencial por mês</h3>

          {serieTemporal.length === 0 ? (
            <p className="muted">Sem produção mensal disponível.</p>
          ) : (
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={serieTemporal}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="mes" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="afericoes_pa" name="PA" fill="#0f766e" />
                <Bar dataKey="glicemias" name="Glicemias" fill="#2563eb" />
                <Bar dataKey="bioimpedancias" name="Bioimpedâncias" fill="#9333ea" />
                <Bar dataKey="intervencoes" name="Intervenções" fill="#f59e0b" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="form-card">
          <h3>Indicadores de intervenção farmacêutica</h3>

          <div className="info-list">
            <Linha nome="Intervenções aceitas" valor={intervencoes.intervencoes_aceitas || 0} />
            <Linha nome="Encaminhamentos" valor={intervencoes.encaminhamentos || 0} />
            <Linha nome="Taxa de aceitação" valor={`${intervencoes.taxa_aceitacao || 0}%`} />
            <Linha nome="Taxa de encaminhamento" valor={`${intervencoes.taxa_encaminhamento || 0}%`} />
          </div>
        </div>
      </div>

      <div className="form-card">
        <h3>Observação metodológica</h3>
        <p className="muted">
          Estes indicadores dependem da qualidade e completude dos registros no sistema. A exportação
          anonimizada deve ser preferida para análise estatística e pesquisa, preservando dados pessoais
          identificáveis.
        </p>
      </div>
    </div>
  );
}

function MetricCard({ titulo, valor, sufixo = "" }) {
  return (
    <div className="metric-card">
      <span>{titulo}</span>
      <strong>{valor}</strong>
      {sufixo && <p>{sufixo}</p>}
    </div>
  );
}

function Linha({ nome, valor }) {
  return (
    <div className="info-row">
      <span>{nome}</span>
      <strong>{valor}</strong>
    </div>
  );
}
