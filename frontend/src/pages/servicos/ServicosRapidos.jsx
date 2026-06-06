import { useEffect, useState } from "react";
import { api } from "../../api/api";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer
} from "recharts";

export default function ServicosRapidos({ setActivePage }) {
  const [abaAtiva, setAbaAtiva] = useState("cadastro");

  const [paciente, setPaciente] = useState({
    nome: "",
    data_nascimento: "",
    sexo: "",
    telefone: "",
    endereco: "",
    observacoes: "",
  });

  const [pacienteCriado, setPacienteCriado] = useState(null);
  const [pacienteClinicoCriado, setPacienteClinicoCriado] = useState(null);
  const [atendimentoCriado, setAtendimentoCriado] = useState(null);
  const [tipoServico, setTipoServico] = useState("pa");
  const [convertendo, setConvertendo] = useState(false);

  const [pacientesSimplificados, setPacientesSimplificados] = useState([]);
  const [buscaPaciente, setBuscaPaciente] = useState("");
  const [carregandoPacientes, setCarregandoPacientes] = useState(false);

  const [pa, setPa] = useState({
    pressao_sistolica: "",
    pressao_diastolica: "",
    frequencia_cardiaca: "",
    posicao_paciente: "sentado",
    braco_medido: "direito",
    observacoes: "",
  });

  const [glicemia, setGlicemia] = useState({
    valor_glicemia: "",
    tipo_jejum: "casual",
    observacoes: "",
  });

  const [picoFluxo, setPicoFluxo] = useState({
    valor_medido: "",
    valor_previsto: "",
    observacoes: "",
  });

  const [bioimpedancia, setBioimpedancia] = useState({
    peso: "",
    altura: "",
    percentual_gordura: "",
    percentual_massa_muscular: "",
    gordura_visceral: "",
    metabolismo_basal: "",
    fator_atividade: "",
    idade_corporal: "",
    observacoes: "",
  });

  const [historicoAtendimentos, setHistoricoAtendimentos] = useState([]);
  const [carregandoHistorico, setCarregandoHistorico] = useState(false);

  const [comparativoBio, setComparativoBio] = useState(null);
  const [historicoPicoFluxo, setHistoricoPicoFluxo] = useState([]);
  const [historicoBio, setHistoricoBio] = useState([]);

  useEffect(() => {
    carregarPacientesSimplificados();
  }, []);

  async function carregarPacientesSimplificados() {
    try {
      setCarregandoPacientes(true);
      const response = await api.get("/consultorio/pacientes-simplificados");
      setPacientesSimplificados(response.data || []);
    } catch (error) {
      console.error("Erro ao carregar pacientes simplificados:", error);
    } finally {
      setCarregandoPacientes(false);
    }
  }

async function carregarHistoricoPaciente(pacienteId) {
  try {
    setCarregandoHistorico(true);

    const response = await api.get(
      `/consultorio/paciente-simplificado/${pacienteId}/historico`
    );

    const bioResponse = await api.get(
      `/consultorio/paciente-simplificado/${pacienteId}/bioimpedancia-historico`
    );

    const picoResponse = await api.get(
      `/consultorio/paciente-simplificado/${pacienteId}/pico-fluxo-historico`
    );

    setHistoricoAtendimentos(response.data.historico || []);
    setHistoricoBio(bioResponse.data.historico || []);
    setHistoricoPicoFluxo(picoResponse.data.historico || []);

    try {
      const comparativoResponse = await api.get(
        `/consultorio/paciente-simplificado/${pacienteId}/bioimpedancia-comparativo`
      );

      setComparativoBio(comparativoResponse.data || null);
    } catch {
      setComparativoBio(null);
      setHistoricoPicoFluxo([]);
    }

  } catch (error) {
    console.error("Erro ao carregar histórico:", error);
    setHistoricoAtendimentos([]);
    setHistoricoBio([]);
    setComparativoBio(null);    
  } finally {
    setCarregandoHistorico(false);
  }
}
  function usarPacienteExistente(p) {
    setPacienteCriado(p);
    setPaciente({
      nome: p.nome || "",
      data_nascimento: p.data_nascimento || "",
      sexo: p.sexo || "",
      telefone: p.telefone || "",
      endereco: p.endereco || "",
      observacoes: p.observacoes || "",
    });

    setAtendimentoCriado(null);
    setPacienteClinicoCriado(null);
    carregarHistoricoPaciente(p.id);
    setAbaAtiva("atendimento");
    alert(`Paciente selecionado: ${p.nome}`);
  }

  async function criarPaciente() {
    try {
      const dados = {
        ...paciente,
        data_nascimento: paciente.data_nascimento || null,
      };

      const response = await api.post(
        "/consultorio/paciente-simplificado",
        dados
      );

      setPacienteCriado(response.data);
      carregarPacientesSimplificados();
      alert("Paciente simplificado criado com sucesso.");
      setAbaAtiva("atendimento");
    } catch (error) {
      console.error("Erro ao criar paciente:", error.response?.data || error);
      alert("Erro ao criar paciente.");
    }
  }

  async function criarAtendimento() {
    if (!pacienteCriado?.id) {
      alert("Crie ou selecione o paciente primeiro.");
      return;
    }

    try {
      const response = await api.post("/consultorio/atendimento-rapido", {
        paciente_simplificado_id: pacienteCriado.id,
        tipo_servico: tipoServico,
        observacoes: `Atendimento rápido - ${tipoServico}`,
      });

      setAtendimentoCriado(response.data);
      alert(`Atendimento rápido criado com sucesso. ID: ${response.data.id}`);
    } catch (error) {
      console.error("Erro ao criar atendimento:", error.response?.data || error);
      alert("Erro ao criar atendimento rápido.");
    }
  }

  async function registrarPA() {
    if (!atendimentoCriado?.id) {
      alert("Crie o atendimento primeiro.");
      return;
    }

    if (!pa.pressao_sistolica || !pa.pressao_diastolica) {
      alert("Informe PAS e PAD.");
      return;
    }

    if (!pa.braco_medido) {
  alert("Informe o braço aferido.");
  return;
}

    try {
      await api.post("/consultorio/afericao-pa", {
        atendimento_rapido_id: atendimentoCriado.id,
        pressao_sistolica: Number(pa.pressao_sistolica),
        pressao_diastolica: Number(pa.pressao_diastolica),
        frequencia_cardiaca: pa.frequencia_cardiaca
          ? Number(pa.frequencia_cardiaca)
          : null,
        posicao_paciente: pa.posicao_paciente || null,
        braco_medido: pa.braco_medido || null,
        observacoes: pa.observacoes || "",
      });

      alert("Aferição de PA registrada.");
      carregarHistoricoPaciente(pacienteCriado.id);
      setAtendimentoCriado(null);
      setPa({
        pressao_sistolica: "",
        pressao_diastolica: "",
        frequencia_cardiaca: "",
        posicao_paciente: "sentado",
        braco_medido: "direito",
        observacoes: "",
      });
    } catch (error) {
      console.error("Erro ao registrar PA:", error.response?.data || error);
      alert(
        `Erro ao registrar PA: ${
          error.response?.data?.detail || "verifique o console"
        }`
      );
    }
  }

  async function registrarGlicemia() {
    if (!atendimentoCriado?.id) {
      alert("Crie o atendimento primeiro.");
      return;
    }

    if (!glicemia.valor_glicemia) {
      alert("Informe o valor da glicemia.");
      return;
    }

    try {
      await api.post("/consultorio/glicemia", {
        atendimento_rapido_id: atendimentoCriado.id,
        valor_glicemia: Number(glicemia.valor_glicemia),
        tipo_jejum: glicemia.tipo_jejum,
        observacoes: glicemia.observacoes,
      });

      alert("Glicemia registrada.");
      carregarHistoricoPaciente(pacienteCriado.id);
      setAtendimentoCriado(null);
      setGlicemia({
        valor_glicemia: "",
        tipo_jejum: "casual",
        observacoes: "",
      });
    } catch (error) {
      console.error("Erro ao registrar glicemia:", error.response?.data || error);
      alert("Erro ao registrar glicemia.");
    }
  }

  async function registrarPicoFluxo() {
  if (!atendimentoCriado?.id) {
    alert("Crie o atendimento primeiro.");
    return;
  }

  if (!picoFluxo.valor_medido) {
    alert("Informe o valor medido do pico de fluxo.");
    return;
  }

  try {
    await api.post("/consultorio/pico-fluxo", {
      atendimento_rapido_id: atendimentoCriado.id,
      valor_medido: Number(picoFluxo.valor_medido),
      valor_previsto: picoFluxo.valor_previsto
        ? Number(picoFluxo.valor_previsto)
        : null,
      observacoes: picoFluxo.observacoes || "",
    });

    alert("Pico de fluxo expiratório registrado.");
    carregarHistoricoPaciente(pacienteCriado.id);
  } catch (error) {
    console.error("Erro ao registrar pico de fluxo:", error.response?.data || error);
    alert("Erro ao registrar pico de fluxo.");
  }
}

  async function converterParaClinico() {
    if (!pacienteCriado?.id) {
      alert("Paciente não localizado.");
      return;
    }

    try {
      setConvertendo(true);

      const response = await api.post(
        `/consultorio/converter-para-clinico/${pacienteCriado.id}`,
        {
          aceite_verbal: true,
          motivo_conversao:
            "Paciente convertido para acompanhamento clínico após serviço rápido.",
          endereco: paciente.endereco || "",
          cpf: "",
          cns: "",
          nome_mae: "",
          observacoes_prontuario:
            "Prontuário aberto automaticamente a partir dos serviços rápidos.",
        }
      );

      const pacienteClinico = response.data.paciente_clinico || response.data;
      setPacienteClinicoCriado(pacienteClinico);
      alert("Paciente convertido para acompanhamento clínico.");
    } catch (error) {
      console.error("Erro ao converter paciente:", error.response?.data || error);
      alert(
        `Erro ao converter paciente: ${
          error.response?.data?.detail || "verifique o console"
        }`
      );
    } finally {
      setConvertendo(false);
    }
  }

  async function abrirPdfAutenticado(url) {
  try {
    const response = await api.get(url, {
      responseType: "blob",
    });

    const fileURL = window.URL.createObjectURL(
      new Blob([response.data], { type: "application/pdf" })
    );

    window.open(fileURL, "_blank");
  } catch (error) {
    console.error("Erro ao abrir PDF:", error.response?.data || error);
    alert("Erro ao abrir PDF autenticado.");
  }
}

  async function registrarBioimpedancia() {
  if (!atendimentoCriado?.id) {
    alert("Crie o atendimento primeiro.");
    return;
  }

  if (!bioimpedancia.peso || !bioimpedancia.altura) {
    alert("Informe peso e altura.");
    return;
  }

  try {
await api.post("/consultorio/bioimpedancia", {
  atendimento_rapido_id: atendimentoCriado.id,
  peso: bioimpedancia.peso ? Number(bioimpedancia.peso) : null,
  altura: bioimpedancia.altura ? Number(bioimpedancia.altura) : null,
  percentual_gordura: bioimpedancia.percentual_gordura
    ? Number(bioimpedancia.percentual_gordura)
    : null,
  percentual_massa_muscular: bioimpedancia.percentual_massa_muscular
    ? Number(bioimpedancia.percentual_massa_muscular)
    : null,
  gordura_visceral: bioimpedancia.gordura_visceral
    ? Number(bioimpedancia.gordura_visceral)
    : null,
  metabolismo_basal: bioimpedancia.metabolismo_basal
    ? Number(bioimpedancia.metabolismo_basal)
    : null,
  fator_atividade: bioimpedancia.fator_atividade
    ? Number(bioimpedancia.fator_atividade)
    : null,
  idade_corporal: bioimpedancia.idade_corporal
    ? Number(bioimpedancia.idade_corporal)
    : null,
  observacoes: bioimpedancia.observacoes || "",
});
    alert("Bioimpedância registrada.");

    carregarHistoricoPaciente(pacienteCriado.id);

  } catch (error) {
    console.error(
      "Erro ao registrar bioimpedância:",
      error.response?.data || error
    );

    alert("Erro ao registrar bioimpedância.");
  }
}

  function obterCorPA(paItem) {
    if (!paItem) return "#64748b";

    const sistolica = Number(paItem.pressao_sistolica);
    const diastolica = Number(paItem.pressao_diastolica);

    if (sistolica >= 180 || diastolica >= 110) return "#dc2626";
    if (sistolica >= 130 || diastolica >= 90) return "#ea580c";
    if (sistolica >= 120 || diastolica >= 80) return "#ca8a04";
    return "#16a34a";
  }

  function classificarRisco(item) {
    if (item.pa) {
      const s = Number(item.pa.pressao_sistolica);
      const d = Number(item.pa.pressao_diastolica);

      if (s >= 180 || d >= 110) {
        return { nivel: "RISCO MUITO ALTO", cor: "#dc2626" };
      }

      if (s >= 130 || d >= 90) {
        return { nivel: "RISCO ALTO", cor: "#ea580c" };
      }

      if (s >= 120 || d >= 80) {
        return { nivel: "RISCO MODERADO", cor: "#ca8a04" };
      }

      return { nivel: "CONTROLADO", cor: "#16a34a" };
    }

    if (item.glicemia) {
      const g = Number(item.glicemia.valor_glicemia);

      if (g >= 126) return { nivel: "GLICEMIA CRÍTICA", cor: "#dc2626" };
      if (g >= 100) return { nivel: "GLICEMIA ELEVADA", cor: "#ea580c" };
      return { nivel: "GLICEMIA CONTROLADA", cor: "#16a34a" };
    }

    return { nivel: "SEM CLASSIFICAÇÃO", cor: "#64748b" };
  }

const dadosPA = historicoAtendimentos
  .filter((item) => item.procedimentos?.pressao_arterial)
  .map((item) => {
    const pa = item.procedimentos.pressao_arterial;

    return {
      data: item.data_atendimento
        ? new Date(item.data_atendimento).toLocaleDateString("pt-BR")
        : "—",
      sistolica: Number(pa.pressao_sistolica),
      diastolica: Number(pa.pressao_diastolica),
    };
  })
  .reverse();

const dadosGlicemia = historicoAtendimentos
  .filter((item) => item.procedimentos?.glicemia)
  .map((item) => {
    const glicemia = item.procedimentos.glicemia;

    return {
      data: item.data_atendimento
        ? new Date(item.data_atendimento).toLocaleDateString("pt-BR")
        : "—",
      glicemia: Number(glicemia.valor_glicemia),
    };
  })
  .reverse();

const dadosPicoFluxo = historicoPicoFluxo.map((item) => ({
  data: item.data
    ? new Date(item.data).toLocaleDateString("pt-BR")
    : "—",
  valor: item.valor_medido,
  previsto: item.valor_previsto,
  percentual: item.percentual_previsto,
}));

const prioridadePaciente = calcularPrioridadePaciente();  

function calcularPrioridadePaciente() {
  if (!historicoAtendimentos.length) {
    return {
      nivel: "SEM HISTÓRICO",
      cor: "#64748b",
      orientacao: "Sem dados suficientes para priorização.",
    };
  }

  const riscos = historicoAtendimentos.map((item) => classificarRisco(item));

  if (riscos.some((r) => r.nivel.includes("MUITO ALTO") || r.nivel.includes("CRÍTICA"))) {
    return {
      nivel: "PRIORIDADE MÁXIMA",
      cor: "#dc2626",
      orientacao: "Avaliar imediatamente e considerar encaminhamento.",
    };
  }

  if (riscos.some((r) => r.nivel.includes("ALTO") || r.nivel.includes("ELEVADA"))) {
    return {
      nivel: "PRIORIDADE ALTA",
      cor: "#ea580c",
      orientacao: "Acompanhamento farmacêutico prioritário.",
    };
  }

  if (riscos.some((r) => r.nivel.includes("MODERADO"))) {
    return {
      nivel: "PRIORIDADE MODERADA",
      cor: "#ca8a04",
      orientacao: "Monitorar e programar retorno.",
    };
  }

  return {
    nivel: "ROTINA",
    cor: "#16a34a",
    orientacao: "Acompanhamento de rotina.",
  };
}
function calcularIMC(peso, altura) {
  if (!peso || !altura) return "";

  const alturaMetros = Number(altura);

  if (alturaMetros <= 0) return "";

  const imc = Number(peso) / (alturaMetros * alturaMetros);

  return imc.toFixed(1);
}

const dadosBio = historicoBio.map((item) => ({
  data: item.data
    ? new Date(item.data).toLocaleDateString("pt-BR")
    : "—",

  peso: item.peso,
  imc: item.imc,
  gordura: item.percentual_gordura,
  massa: item.percentual_massa_muscular,
  visceral: item.gordura_visceral,

  massaGorduraKg: item.massa_gordura_kg,
  massaMuscularKg: item.massa_muscular_kg,
  massaMagraKg: item.massa_magra_kg,
  fmi: item.fmi,
  ffmi: item.ffmi,
  get: item.gasto_energetico_total,
  risco: item.risco_cardiometabolico,
}));

const pesoBio = Number(bioimpedancia.peso);
const alturaBio = Number(bioimpedancia.altura);
const gorduraPercentual = Number(bioimpedancia.percentual_gordura);
const musculoPercentual = Number(bioimpedancia.percentual_massa_muscular);
const metabolismoBasal = Number(bioimpedancia.metabolismo_basal);
const fatorAtividade = Number(bioimpedancia.fator_atividade);

const alturaMetros =
  alturaBio > 3 ? alturaBio / 100 : alturaBio;

const imcCalculado =
  pesoBio > 0 && alturaMetros > 0
    ? (pesoBio / (alturaMetros * alturaMetros)).toFixed(2)
    : "";

const massaGorduraKg =
  pesoBio > 0 && gorduraPercentual > 0
    ? ((pesoBio * gorduraPercentual) / 100).toFixed(2)
    : "";

const massaMuscularKg =
  pesoBio > 0 && musculoPercentual > 0
    ? ((pesoBio * musculoPercentual) / 100).toFixed(2)
    : "";

const massaMagraKg =
  pesoBio > 0 && massaGorduraKg
    ? (pesoBio - Number(massaGorduraKg)).toFixed(2)
    : "";

const gastoEnergeticoTotal =
  metabolismoBasal > 0 && fatorAtividade > 0
    ? (metabolismoBasal * fatorAtividade).toFixed(2)
    : "";

function classificarImcFrontend(imc) {
  const valor = Number(imc);

  if (!valor) return "—";
  if (valor < 18.5) return "Baixo peso";
  if (valor < 25) return "Eutrofia";
  if (valor < 30) return "Sobrepeso";
  if (valor < 35) return "Obesidade grau I";
  if (valor < 40) return "Obesidade grau II";
  return "Obesidade grau III";
}

function classificarGorduraVisceralFrontend(valor) {
  const v = Number(valor);

  if (!v) return "—";
  if (v <= 9) return "Normal";
  if (v <= 14) return "Elevada";
  return "Muito elevada";
}

const ultimoPA = dadosPA.length > 0 ? dadosPA[dadosPA.length - 1] : null;
const ultimaGlicemia = dadosGlicemia.length > 0 ? dadosGlicemia[dadosGlicemia.length - 1] : null;
const ultimoBio = dadosBio.length > 0 ? dadosBio[dadosBio.length - 1] : null;
const ultimoPico = dadosPicoFluxo.length > 0 ? dadosPicoFluxo[dadosPicoFluxo.length - 1] : null;

function obterRiscoBioimpedancia() {
  const imc = Number(imcCalculado);
  const gv = Number(bioimpedancia.gordura_visceral);
  const gordura = Number(bioimpedancia.percentual_gordura);

  let risco = "baixo";
  let cor = "#22c55e";
  let mensagens = [];

  if (imc >= 25) {
    mensagens.push("Excesso de peso");
    risco = "moderado";
    cor = "#f59e0b";
  }

  if (imc >= 30) {
    mensagens.push("Obesidade");
    risco = "alto";
    cor = "#ef4444";
  }

  if (gv >= 10) {
    mensagens.push("Gordura visceral elevada");
    risco = "alto";
    cor = "#dc2626";
  }

  if (gordura >= 30) {
    mensagens.push("Percentual de gordura elevado");
  }

  if (
    Number(bioimpedancia.percentual_massa_muscular) < 30 &&
    gordura >= 30
  ) {
    mensagens.push("Possível obesidade sarcopênica");
    risco = "alto";
    cor = "#991b1b";
  }

  return {
    risco,
    cor,
    mensagens,
  };
}

const avaliacaoBio = obterRiscoBioimpedancia();


  return (
    <div className="servicos-rapidos-page">
      <div className="page-header">
        <div>
          <h2>Serviços rápidos</h2>
          <p className="muted">
            Cadastro simplificado, registro de atendimentos rápidos e acompanhamento longitudinal.
          </p>
        </div>

        {setActivePage && (
          <button
            className="secondary-button"
            onClick={() => setActivePage("dashboard")}
          >
            Voltar ao painel
          </button>
        )}
      </div>

      <div className="tabs">
        <button
          className={abaAtiva === "cadastro" ? "tab active" : "tab"}
          onClick={() => setAbaAtiva("cadastro")}
        >
          Cadastro
        </button>

        <button
          className={abaAtiva === "atendimento" ? "tab active" : "tab"}
          onClick={() => setAbaAtiva("atendimento")}
        >
          Atendimento
        </button>

        <button
          className={abaAtiva === "historico" ? "tab active" : "tab"}
          onClick={() => setAbaAtiva("historico")}
          disabled={!pacienteCriado}
        >
          Histórico
        </button>
      </div>

      {abaAtiva === "cadastro" && (
        <div className="content-grid">
          <div className="form-card">
            <h3>Novo paciente simplificado</h3>

            <div className="grid-2">
              <input
                className="input"
                placeholder="Nome"
                value={paciente.nome}
                onChange={(e) =>
                  setPaciente({ ...paciente, nome: e.target.value })
                }
              />

              <input
                className="input"
                type="date"
                placeholder="Data de nascimento"
                value={paciente.data_nascimento}
                onChange={(e) =>
                  setPaciente({
                    ...paciente,
                    data_nascimento: e.target.value,
                  })
                }
              />
            </div>

            <div className="grid-2">
              <select
                className="input"
                value={paciente.sexo}
                onChange={(e) =>
                  setPaciente({ ...paciente, sexo: e.target.value })
                }
              >
                <option value="">Sexo</option>
                <option value="F">Feminino</option>
                <option value="M">Masculino</option>
                <option value="Outro">Outro</option>
              </select>

              <input
                className="input"
                placeholder="Telefone"
                value={paciente.telefone}
                onChange={(e) =>
                  setPaciente({ ...paciente, telefone: e.target.value })
                }
              />
            </div>

            <input
              className="input"
              placeholder="Endereço"
              value={paciente.endereco}
              onChange={(e) =>
                setPaciente({ ...paciente, endereco: e.target.value })
              }
            />

            <textarea
              className="textarea"
              placeholder="Observações"
              value={paciente.observacoes}
              onChange={(e) =>
                setPaciente({ ...paciente, observacoes: e.target.value })
              }
            />

            <button className="primary-button" onClick={criarPaciente}>
              Criar paciente
            </button>
          </div>

          <div className="form-card">
            <h3>Pacientes cadastrados</h3>

            <input
              className="input"
              placeholder="Buscar paciente"
              value={buscaPaciente}
              onChange={(e) => setBuscaPaciente(e.target.value)}
            />

            {carregandoPacientes ? (
              <p className="muted">Carregando pacientes...</p>
            ) : (
              <div className="list-card">
                {pacientesSimplificados
                  .filter((p) =>
                    (p.nome || "")
                      .toLowerCase()
                      .includes(buscaPaciente.toLowerCase())
                  )
                  .map((p) => (
                    <div className="patient-row" key={p.id}>
                      <div>
                        <strong>{p.nome}</strong>
                        <p className="muted">
                          {p.idade ? `${p.idade} anos` : "Idade não informada"} ·{" "}
                          {p.sexo || "Sexo não informado"}
                        </p>
                      </div>

                      <button
                        className="mini-action-button"
                        onClick={() => usarPacienteExistente(p)}
                      >
                        Selecionar
                      </button>
                    </div>
                  ))}

                {pacientesSimplificados.length === 0 && (
                  <p className="muted">Nenhum paciente cadastrado.</p>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {abaAtiva === "atendimento" && (
        <div className="form-card">
          <div className="section-header-row">
            <div>
              <h3>Atendimento rápido</h3>
              <p className="muted">
                Paciente: {pacienteCriado?.nome || "nenhum paciente selecionado"}
              </p>
            </div>

            {pacienteCriado && (
              <button
                className="secondary-button"
                onClick={() => setAbaAtiva("historico")}
              >
                Ver histórico
              </button>
            )}
          </div>

          <div className="grid-2">
            <select
              className="input"
              value={tipoServico}
              onChange={(e) => {
                setTipoServico(e.target.value);
                setAtendimentoCriado(null);
              }}
            >
              <option value="pa">Pressão arterial</option>
              <option value="glicemia">Glicemia capilar</option>
              <option value="bioimpedancia">Bioimpedância</option>
              <option value="pico_fluxo">Pico de fluxo</option>
            </select>

            <button
              className="primary-button"
              onClick={criarAtendimento}
              disabled={!pacienteCriado}
            >
              Criar atendimento
            </button>
          </div>

          {atendimentoCriado && (
            <p className="success-message">
              Atendimento criado: #{atendimentoCriado.id}
            </p>
          )}

          {tipoServico === "pa" && (
            <div className="nested-form">
              <div className="grid-2">
                <input
                  className="input"
                  placeholder="PAS"
                  type="number"
                  value={pa.pressao_sistolica}
                  onChange={(e) =>
                    setPa({ ...pa, pressao_sistolica: e.target.value })
                  }
                />

                <input
                  className="input"
                  placeholder="PAD"
                  type="number"
                  value={pa.pressao_diastolica}
                  onChange={(e) =>
                    setPa({ ...pa, pressao_diastolica: e.target.value })
                  }
                />
              </div>

              <input
                className="input"
                placeholder="Frequência cardíaca"
                type="number"
                value={pa.frequencia_cardiaca}
                onChange={(e) =>
                  setPa({ ...pa, frequencia_cardiaca: e.target.value })
                }
              />

              <div className="grid-2">
                <select
                  className="input"
                  value={pa.posicao_paciente}
                  onChange={(e) =>
                    setPa({ ...pa, posicao_paciente: e.target.value })
                  }
                >
                  <option value="sentado">Sentado</option>
                  <option value="em_pe">Em pé</option>
                  <option value="deitado">Deitado</option>
                </select>

                <select
                  className="input"
                  value={pa.braco_medido}
                  onChange={(e) =>
                    setPa({ ...pa, braco_medido: e.target.value })
                  }
                >
                  <option value="direito">Braço direito</option>
                  <option value="esquerdo">Braço esquerdo</option>
                </select>
              </div>

              <textarea
                className="textarea"
                placeholder="Observações"
                value={pa.observacoes}
                onChange={(e) => setPa({ ...pa, observacoes: e.target.value })}
              />

              <button className="primary-button" onClick={registrarPA}>
                Registrar PA
              </button>
            </div>
          )}

          {tipoServico === "glicemia" && (
            <div className="nested-form">
              <input
                className="input"
                placeholder="Valor da glicemia"
                type="number"
                value={glicemia.valor_glicemia}
                onChange={(e) =>
                  setGlicemia({ ...glicemia, valor_glicemia: e.target.value })
                }
              />

              <select
                className="input"
                value={glicemia.tipo_jejum}
                onChange={(e) =>
                  setGlicemia({ ...glicemia, tipo_jejum: e.target.value })
                }
              >
                <option value="casual">Casual</option>
                <option value="jejum">Jejum</option>
                <option value="pos_prandial">Pós-prandial</option>
              </select>

              <textarea
                className="textarea"
                placeholder="Observações"
                value={glicemia.observacoes}
                onChange={(e) =>
                  setGlicemia({ ...glicemia, observacoes: e.target.value })
                }
              />

              <button className="primary-button" onClick={registrarGlicemia}>
                Registrar glicemia
              </button>
            </div>
          )}

          {tipoServico === "pico_fluxo" && (
            <div className="nested-form">
              <div className="grid-2">
                <input
                  className="input"
                  placeholder="PFE medido"
                  type="number"
                  value={picoFluxo.valor_medido}
                  onChange={(e) =>
                    setPicoFluxo({ ...picoFluxo, valor_medido: e.target.value })
                  }
                />

                <input
                  className="input"
                  placeholder="PFE previsto"
                  type="number"
                  value={picoFluxo.valor_previsto}
                  onChange={(e) =>
                    setPicoFluxo({ ...picoFluxo, valor_previsto: e.target.value })
                  }
                />
              </div>

              <textarea
                className="textarea"
                placeholder="Observações"
                value={picoFluxo.observacoes}
                onChange={(e) =>
                  setPicoFluxo({ ...picoFluxo, observacoes: e.target.value })
                }
              />

              <button className="primary-button" onClick={registrarPicoFluxo}>
                Registrar pico de fluxo
              </button>
            </div>
          )}

          {tipoServico === "bioimpedancia" && (
            <>
              <div className="nested-form">
                <div className="grid-2">
                  <input
                    className="input"
                    placeholder="Peso (kg)"
                    type="number"
                    step="0.1"
                    value={bioimpedancia.peso}
                    onChange={(e) => {
                      const peso = e.target.value;

                      setBioimpedancia({
                        ...bioimpedancia,
                        peso,
                      });
                    }}
                  />

                  <input
                    className="input"
                    placeholder="Altura (m)"
                    type="number"
                    step="0.01"
                    value={bioimpedancia.altura}
                    onChange={(e) => {
                      const altura = e.target.value;

                      setBioimpedancia({
                        ...bioimpedancia,
                        altura,
                      });
                    }}
                  />
                </div>

                <input
                  className="input"
                  placeholder="IMC"
                  value={imcCalculado}
                  readOnly
                />

                <div className="grid-2">
                  <input
                    className="input"
                    placeholder="% Gordura corporal"
                    type="number"
                    step="0.1"
                    value={bioimpedancia.percentual_gordura}
                    onChange={(e) =>
                      setBioimpedancia({
                        ...bioimpedancia,
                        percentual_gordura: e.target.value,
                      })
                    }
                  />

                  <input
                    className="input"
                    placeholder="Gordura corporal (kg)"
                    value={massaGorduraKg}
                    readOnly
                  />
                </div>

                <div className="grid-2">
                  <input
                    className="input"
                    placeholder="% Massa muscular"
                    type="number"
                    step="0.1"
                    value={bioimpedancia.percentual_massa_muscular}
                    onChange={(e) =>
                      setBioimpedancia({
                        ...bioimpedancia,
                        percentual_massa_muscular: e.target.value,
                      })
                    }
                  />

                  <input
                    className="input"
                    placeholder="Massa muscular (kg)"
                    value={massaMuscularKg}
                    readOnly
                  />
                </div>

                <div className="grid-2">
                  <input
                    className="input"
                    placeholder="Gordura visceral"
                    type="number"
                    value={bioimpedancia.gordura_visceral}
                    onChange={(e) =>
                      setBioimpedancia({
                        ...bioimpedancia,
                        gordura_visceral: e.target.value,
                      })
                    }
                  />

                  <input
                    className="input"
                    placeholder="Idade corporal"
                    type="number"
                    value={bioimpedancia.idade_corporal}
                    onChange={(e) =>
                      setBioimpedancia({
                        ...bioimpedancia,
                        idade_corporal: e.target.value,
                      })
                    }
                  />
                </div>

                <div className="grid-2">
                  <input
                    className="input"
                    placeholder="Metabolismo basal (kcal)"
                    type="number"
                    value={bioimpedancia.metabolismo_basal}
                    onChange={(e) =>
                      setBioimpedancia({
                        ...bioimpedancia,
                        metabolismo_basal: e.target.value,
                      })
                    }
                  />

                  <input
                    className="input"
                    placeholder="Gasto energético total (kcal)"
                    value={gastoEnergeticoTotal}
                    readOnly
                  />
                </div>

                <select
                  className="input"
                  value={bioimpedancia.fator_atividade}
                  onChange={(e) =>
                    setBioimpedancia({
                      ...bioimpedancia,
                      fator_atividade: e.target.value,
                    })
                  }
                >
                  <option value="">Fator de atividade física</option>
                  <option value="1.2">Sedentário — 1,2</option>
                  <option value="1.375">Leve — 1,375</option>
                  <option value="1.55">Moderado — 1,55</option>
                  <option value="1.725">Intenso — 1,725</option>
                  <option value="1.9">Muito intenso — 1,9</option>
                </select>

                <textarea
                  className="textarea"
                  placeholder="Observações"
                  value={bioimpedancia.observacoes}
                  onChange={(e) =>
                    setBioimpedancia({
                      ...bioimpedancia,
                      observacoes: e.target.value,
                    })
                  }
                />

                <div className="bio-preview-card">
                  <h4>Resumo automático</h4>

                  <div
                    className="bio-risk-banner"
                    style={{
                      background: avaliacaoBio.cor,
                    }}
                  >
                    Risco cardiometabólico: {avaliacaoBio.risco.toUpperCase()}
                  </div>

                  <p>
                    <strong>IMC:</strong>{" "}
                    {imcCalculado || "—"}{" "}
                    {imcCalculado && `(${classificarImcFrontend(imcCalculado)})`}
                  </p>

                  <p>
                    <strong>Gordura corporal:</strong>{" "}
                    {massaGorduraKg || "—"} kg
                  </p>

                  <p>
                    <strong>Massa muscular:</strong>{" "}
                    {massaMuscularKg || "—"} kg
                  </p>

                  <p>
                    <strong>Massa magra:</strong>{" "}
                    {massaMagraKg || "—"} kg
                  </p>

                  <p>
                    <strong>Gordura visceral:</strong>{" "}
                    {bioimpedancia.gordura_visceral || "—"}{" "}
                    {bioimpedancia.gordura_visceral &&
                      `(${classificarGorduraVisceralFrontend(
                        bioimpedancia.gordura_visceral
                      )})`}
                  </p>

                  <p>
                    <strong>GET estimado:</strong>{" "}
                    {gastoEnergeticoTotal || "—"} kcal/dia
                  </p>

                  {avaliacaoBio.mensagens.length > 0 && (
                    <div className="bio-alert-list">
                      {avaliacaoBio.mensagens.map((msg, index) => (
                        <div
                          key={`bio-alert-${index}`}
                          className="bio-alert-item"
                        >
                          • {msg}
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <button
                  className="primary-button"
                  onClick={registrarBioimpedancia}
                >
                  Registrar bioimpedância
                </button>
              </div>
            </>
          )}

          {pacienteCriado && (
            <div className="form-actions">
              <button
                className="secondary-button"
                onClick={() =>
                  abrirPdfAutenticado(
                    `/consultorio/paciente-simplificado/${pacienteCriado.id}/prontuario-longitudinal-pdf`
                  )
                }
              >
                Imprimir prontuário longitudinal
              </button>

              <button
                className="secondary-button"
                onClick={converterParaClinico}
                disabled={convertendo}
              >
                {convertendo ? "Convertendo..." : "Converter para acompanhamento clínico"}
              </button>
            </div>
          )}
        </div>
      )}

      {abaAtiva === "historico" && (
        <div className="form-card">
          <div className="section-header-row">
            <div>
              <h3>Histórico longitudinal</h3>
              <p className="muted">
                Paciente: {pacienteCriado?.nome || "não selecionado"}
              </p>
            </div>

            <button
              className="secondary-button"
              onClick={() => setAbaAtiva("atendimento")}
            >
              Novo atendimento
            </button>
          </div>

          <div
            className="priority-card"
            style={{ borderLeft: `8px solid ${prioridadePaciente.cor}` }}
          >
            <strong>{prioridadePaciente.nivel}</strong>
            <p>{prioridadePaciente.orientacao}</p>
          </div>

          {(dadosPA.length > 0 ||
            dadosGlicemia.length > 0 ||
            dadosBio.length > 0 ||
            dadosPicoFluxo.length > 0) && (
            <div className="charts-compact-grid">
              {dadosPA.length > 0 && (
                <div className="mini-chart-card">
                  <h4>Evolução da pressão arterial</h4>

                  <ResponsiveContainer width="100%" height={220}>
                    <LineChart data={dadosPA}>
                      <XAxis dataKey="data" />
                      <YAxis />
                      <Tooltip />
                      <Line type="monotone" dataKey="sistolica" name="PAS" />
                      <Line type="monotone" dataKey="diastolica" name="PAD" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}

              {dadosGlicemia.length > 0 && (
                <div className="mini-chart-card">
                  <h4>Evolução da glicemia</h4>

                  <ResponsiveContainer width="100%" height={220}>
                    <LineChart data={dadosGlicemia}>
                      <XAxis dataKey="data" />
                      <YAxis />
                      <Tooltip />
                      <Line type="monotone" dataKey="glicemia" name="Glicemia" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}

              {dadosBio.length > 0 && (
                <div className="mini-chart-card">
                  <h4>Evolução da bioimpedância</h4>

                  <ResponsiveContainer width="100%" height={260}>
                    <LineChart data={dadosBio}>
                      <XAxis dataKey="data" />
                      <YAxis />
                      <Tooltip />

                      <Line type="monotone" dataKey="peso" name="Peso" />
                      <Line type="monotone" dataKey="imc" name="IMC" />
                      <Line type="monotone" dataKey="gordura" name="% Gordura" />
                      <Line type="monotone" dataKey="massa" name="% Massa muscular" />
                      <Line type="monotone" dataKey="visceral" name="Gordura visceral" />
                      <Line type="monotone" dataKey="massaGorduraKg" name="Gordura kg" />
                      <Line type="monotone" dataKey="massaMuscularKg" name="Músculo kg" />
                      <Line type="monotone" dataKey="massaMagraKg" name="Massa magra kg" />
                      <Line type="monotone" dataKey="fmi" name="FMI" />
                      <Line type="monotone" dataKey="ffmi" name="FFMI" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}

              <div className="mini-chart-card">
                <h4>Pico de fluxo expiratório</h4>

                {dadosPicoFluxo.length === 0 ? (
                  <p className="muted">
                    Nenhum registro de pico de fluxo encontrado.
                  </p>
                ) : (
                  <ResponsiveContainer width="100%" height={260}>
                    <LineChart data={dadosPicoFluxo}>
                      <XAxis dataKey="data" />
                      <YAxis />
                      <Tooltip />
                      <Line type="monotone" dataKey="valor" name="PFE medido" />
                      <Line type="monotone" dataKey="previsto" name="PFE previsto" />
                      <Line type="monotone" dataKey="percentual" name="% previsto" />
                    </LineChart>
                  </ResponsiveContainer>
                )}
              </div>
            </div>
          )}

          <div className="cards-grid four">
            <div className="metric-card">
              <span>Última PA</span>
              <strong>
                {ultimoPA ? `${ultimoPA.sistolica}/${ultimoPA.diastolica}` : "—"}
              </strong>
              <p>mmHg</p>
            </div>

            <div className="metric-card">
              <span>Última glicemia</span>
              <strong>
                {ultimaGlicemia ? ultimaGlicemia.glicemia : "—"}
              </strong>
              <p>mg/dL</p>
            </div>

            <div className="metric-card">
              <span>Último IMC</span>
              <strong>
                {ultimoBio ? ultimoBio.imc : "—"}
              </strong>
              <p>kg/m²</p>
            </div>

            <div className="metric-card">
              <span>Último PFE</span>
              <strong>
                {ultimoPico ? ultimoPico.valor : "—"}
              </strong>
              <p>L/min</p>
            </div>
          </div>

          {comparativoBio && (
            <div className="bio-comparison-card">
              <h4>Comparativo longitudinal da bioimpedância</h4>

              {!comparativoBio.comparativo_disponivel ? (
                <p className="muted">
                  {comparativoBio.mensagem ||
                    "Ainda não há avaliações suficientes para comparação."}
                </p>
              ) : (
                <>
                  <div className="bio-comparison-summary">
                    <strong>{comparativoBio.resumo}</strong>

                    <span>
                      Favoráveis: {comparativoBio.favoraveis || 0} ·
                      Desfavoráveis: {comparativoBio.desfavoraveis || 0}
                    </span>
                  </div>

                  <div className="bio-comparison-list">
                    {comparativoBio.comparacoes?.map((item, index) => (
                      <div
                        className={`bio-comparison-item ${item.avaliacao}`}
                        key={`${item.indicador}-${index}`}
                      >
                        <strong>{item.indicador}</strong>
                        <span>{item.valor_inicial} → {item.valor_final}</span>
                        <span>Diferença: {item.diferenca}</span>
                        <span>Tendência: {item.tendencia}</span>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
          )}

          {carregandoHistorico ? (
            <p className="muted">Carregando histórico...</p>
          ) : historicoAtendimentos.length === 0 ? (
            <p className="muted">Nenhum atendimento anterior encontrado.</p>
          ) : (
            <div className="timeline">
              {historicoAtendimentos.map((item, index) => {
                const pa = item.procedimentos?.pressao_arterial;
                const glicemia = item.procedimentos?.glicemia;
                const picoFluxo = item.procedimentos?.pico_fluxo;
                const bioimpedanciaItem = item.procedimentos?.bioimpedancia;

                const risco = classificarRisco({
                  ...item,
                  pa,
                  glicemia,
                  pico_fluxo: picoFluxo,
                  bioimpedancia: bioimpedanciaItem,
                });

                return (
                  <div
                    key={`${item.atendimento_id || item.id || "atendimento"}-${index}`}
                    className="timeline-item"
                  >
                    <div className="timeline-row">
                      <div className="timeline-col data">
                        {item.data_atendimento
                          ? new Date(item.data_atendimento).toLocaleDateString("pt-BR")
                          : "—"}
                      </div>

                      <div className="timeline-col servico">
                        {item.tipo_servico?.toUpperCase() || "ATENDIMENTO"}
                      </div>

                      <div className="timeline-col resultado">
                        <span
                          className="risk-badge"
                          style={{ background: risco.cor }}
                        >
                          {risco.nivel}
                        </span>

                        {pa && (
                          <span
                            className="timeline-badge"
                            style={{
                              borderLeft: `6px solid ${obterCorPA(pa)}`,
                            }}
                          >
                            PA: {pa.pressao_sistolica}/{pa.pressao_diastolica}
                          </span>
                        )}

                        {glicemia && (
                          <span className="timeline-badge glicemia">
                            Glicemia: {glicemia.valor_glicemia}
                          </span>
                        )}

                        {picoFluxo && (
                          <span className="timeline-badge respiratory">
                            PFE: {picoFluxo.valor_medido} L/min
                            {picoFluxo.percentual_previsto
                              ? ` (${picoFluxo.percentual_previsto}%)`
                              : ""}
                          </span>
                        )}

                        {bioimpedanciaItem && (
                          <span className="timeline-badge bio">
                            Bio: IMC {bioimpedanciaItem.imc || "—"}
                            {bioimpedanciaItem.classificacao_imc
                              ? ` (${bioimpedanciaItem.classificacao_imc})`
                              : ""}
                            {bioimpedanciaItem.percentual_gordura
                              ? ` · GC ${bioimpedanciaItem.percentual_gordura}%`
                              : ""}
                            {bioimpedanciaItem.massa_gordura_kg
                              ? ` · Gordura ${bioimpedanciaItem.massa_gordura_kg} kg`
                              : ""}
                            {bioimpedanciaItem.percentual_massa_muscular
                              ? ` · MM ${bioimpedanciaItem.percentual_massa_muscular}%`
                              : ""}
                            {bioimpedanciaItem.massa_muscular_kg
                              ? ` · Músculo ${bioimpedanciaItem.massa_muscular_kg} kg`
                              : ""}
                            {bioimpedanciaItem.gordura_visceral
                              ? ` · GV ${bioimpedanciaItem.gordura_visceral}`
                              : ""}
                            {bioimpedanciaItem.classificacao_gordura_visceral
                              ? ` (${bioimpedanciaItem.classificacao_gordura_visceral})`
                              : ""}
                            {bioimpedanciaItem.risco_cardiometabolico
                              ? ` · Risco ${bioimpedanciaItem.risco_cardiometabolico}`
                              : ""}
                          </span>
                        )}

                        <div className="timeline-actions">
                          <button
                            className="mini-action-button"
                            onClick={() =>
                              abrirPdfAutenticado(
                                `/consultorio/atendimento-rapido/${item.atendimento_id}/declaracao-pdf`
                              )
                            }
                          >
                            Emitir declaração
                          </button>

                          {bioimpedanciaItem?.id && (
                            <button
                              className="mini-action-button bio"
                              onClick={() =>
                                abrirPdfAutenticado(
                                  `/consultorio/bioimpedancia/${bioimpedanciaItem.id}/laudo-pdf`
                                )
                              }
                            >
                              Laudo bioimpedância
                            </button>
                          )}
                        </div>

                        {!pa && !glicemia && !picoFluxo && !bioimpedanciaItem && (
                          <span className="muted">Sem procedimento</span>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
