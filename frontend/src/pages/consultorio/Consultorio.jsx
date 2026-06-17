import { useEffect, useState } from "react";
import { api } from "../../api/api";
import { ArrowLeft, UserRound } from "lucide-react";
import CuidadoFarmaceutico from "./CuidadoFarmaceutico.jsx";

export default function Consultorio({ usuario }) {
  const [pacientes, setPacientes] = useState([]);
  const [pacienteSelecionado, setPacienteSelecionado] = useState(null);
  const [detalhe, setDetalhe] = useState(null);
  const [resumoCuidado, setResumoCuidado] = useState(null);

  const [loading, setLoading] = useState(false);
  const [loadingProntuario, setLoadingProntuario] = useState(false);
  const [buscaPacienteProntuario, setBuscaPacienteProntuario] = useState("");
  const [buscaPacientesRealizada, setBuscaPacientesRealizada] = useState(false);

  const [linhaTempoClinica, setLinhaTempoClinica] = useState([]);
  const [medicamentos, setMedicamentos] = useState([]);
  const [intervencoesFarmacoterapia, setIntervencoesFarmacoterapia] = useState([]);

  const [mostrarEdicaoIdentificacao, setMostrarEdicaoIdentificacao] = useState(false);
  const [salvandoIdentificacao, setSalvandoIdentificacao] = useState(false);

  const [mostrarPerfilClinico, setMostrarPerfilClinico] = useState(false);
  const [salvandoPerfilClinico, setSalvandoPerfilClinico] = useState(false);

  const [mostrarFormularioMedicamento, setMostrarFormularioMedicamento] = useState(false);
  const [salvandoMedicamento, setSalvandoMedicamento] = useState(false);

  const [mostrarFormularioEvolucao, setMostrarFormularioEvolucao] = useState(false);
  const [salvandoEvolucao, setSalvandoEvolucao] = useState(false);

  const [evolucaoParaDesfecho, setEvolucaoParaDesfecho] = useState(null);
  const [salvandoDesfecho, setSalvandoDesfecho] = useState(false);

  const [mostrarFormularioIntervencao, setMostrarFormularioIntervencao] = useState(false);
  const [salvandoIntervencao, setSalvandoIntervencao] = useState(false);

  const [intervencaoParaDesfecho, setIntervencaoParaDesfecho] = useState(null);
  const [salvandoDesfechoIntervencao, setSalvandoDesfechoIntervencao] = useState(false);

  const [identificacaoPaciente, setIdentificacaoPaciente] = useState({
    cpf: "",
    cns: "",
    nome_mae: "",
    telefone: "",
    endereco: "",
    bairro: "",
  });

  const [perfilClinico, setPerfilClinico] = useState({
    cid_principal: "",
    cid_secundario: "",
    comorbidades: "",
    alergias: "",
    tabagismo: "",
    etilismo: "",
    atividade_fisica: "",
    historico_familiar: "",
    pessoa_com_deficiencia: false,
    tipo_deficiencia: "",
    vacinacao_influenza: false,
    vacinacao_covid: false,
    adesao_terapeutica: "",
    meta_pressao_arterial: "",
    meta_glicemica: "",
    meta_peso: "",
    observacoes_clinicas: "",
  });

  const [novoMedicamento, setNovoMedicamento] = useState({
    catalogo_medicamento_id: "",
    nome_medicamento: "",
    dose: "",
    via: "",
    frequencia: "",
    frequencia_uso: "",
    horarios_uso: "",
    uso_se_necessario: false,
    indicacao: "",
    uso_continuo: true,
    adesao_referida: "",
    observacoes: "",
  });


  const [opcoesCicloVidaMedicamento, setOpcoesCicloVidaMedicamento] = useState({
    status_farmacoterapia: ["EM_USO", "TROCADO", "SUSPENSO", "ENCERRADO"],
    motivos_troca: [],
    motivos_suspensao: [],
    motivos_encerramento: [],
    tipos_suspensao: ["TEMPORARIA", "DEFINITIVA"],
  });
  const [medicamentoCicloVida, setMedicamentoCicloVida] = useState(null);
  const [acaoCicloVidaMedicamento, setAcaoCicloVidaMedicamento] = useState(null);
  const [salvandoCicloVidaMedicamento, setSalvandoCicloVidaMedicamento] = useState(false);
  const [medicamentoSubstituto, setMedicamentoSubstituto] = useState({
    catalogo_medicamento_id: "",
    nome_medicamento: "",
    dose: "",
    via: "",
    frequencia: "",
    frequencia_uso: "",
    horarios_uso: "",
    uso_se_necessario: false,
    indicacao: "",
    uso_continuo: true,
    adesao_referida: "",
    observacoes: "",
  });
  const [formCicloVidaMedicamento, setFormCicloVidaMedicamento] = useState({
    data_evento: "",
    motivo: "",
    tipo_suspensao: "DEFINITIVA",
    prm_relacionado_id: "",
    intervencao_relacionada_id: "",
    observacao: "",
  });

  const [novaEvolucao, setNovaEvolucao] = useState({
    tipo_atendimento: "Consulta farmacêutica",
    queixa_principal: "",
    historia_breve: "",
    avaliacao_farmaceutica: "",
    problemas_identificados: "",
    conduta: "",
    orientacoes_realizadas: "",
    plano_acompanhamento: "",
    necessidade_retorno: false,
    data_retorno_sugerida: "",
    observacoes: "",
  });

  const [novoDesfecho, setNovoDesfecho] = useState({
    melhora_clinica: "parcial",
    adesao_tratamento: "regular",
    resolucao_problema: false,
    necessidade_encaminhamento: false,
    encaminhamento_realizado: "",
    resultado_observado: "",
    observacoes: "",
  });

  const [novaIntervencao, setNovaIntervencao] = useState({
    medicamento_uso_id: "",
    tipo_intervencao: "",
    descricao: "",
    conduta: "",
    aceita_pelo_paciente: false,
    necessidade_encaminhamento: false,
    observacoes: "",
  });

  const [novoDesfechoIntervencao, setNovoDesfechoIntervencao] = useState({
    status_desfecho: "parcial",
    resultado_observado: "",
    necessidade_nova_intervencao: false,
    observacoes: "",
  });

  const [avaliacaoPolifarmacia, setAvaliacaoPolifarmacia] = useState(null);
  const [evolucaoFarmacoterapeutica, setEvolucaoFarmacoterapeutica] = useState(null);
  const [abaProntuario, setAbaProntuario] = useState("resumo");
  const [abaConsultorio, setAbaConsultorio] = useState("centro");

  const [planosCuidado, setPlanosCuidado] = useState([]);
  const [mostrarFormularioPlano, setMostrarFormularioPlano] = useState(false);
  const [planoEditando, setPlanoEditando] = useState(null);

  const [novoPlano, setNovoPlano] = useState({
    problema_identificado: "",
    objetivo_terapeutico: "",
    intervencoes_planejadas: "",
    prazo_reavaliacao: "",
    observacoes: "",
  });

  const [sugestoesPlano, setSugestoesPlano] = useState(null);
  const [opcoesFarmacoterapia, setOpcoesFarmacoterapia] = useState({
    vias_administracao: [],
    horarios_padrao: [],
    frequencias_uso: [],
  });

  const [opcoesMetas, setOpcoesMetas] = useState({
    categorias: [],
    subcategorias: {},
    unidades: [],
    status: [],
    origens: [],
  });
  const [mostrarFormularioMeta, setMostrarFormularioMeta] = useState(false);
  const [salvandoMeta, setSalvandoMeta] = useState(false);
  const [metaEditandoId, setMetaEditandoId] = useState(null);
  const [novaMeta, setNovaMeta] = useState({
    prm_id: "",
    intervencao_farmacoterapia_id: "",
    categoria: "CONTROLE_CLINICO",
    subcategoria: "PRESSAO_ARTERIAL",
    descricao: "",
    valor_atual: "",
    valor_alvo: "",
    unidade: "",
    data_inicial: "",
    data_prevista: "",
    data_conclusao: "",
    status: "EM_ANDAMENTO",
    origem: "CONSULTA",
  });

  const [opcoesPlanoCuidado, setOpcoesPlanoCuidado] = useState({
    tipos_acao: [],
    status_acao: [],
    responsaveis: ["FARMACEUTICO", "PACIENTE", "CUIDADOR", "EQUIPE_APS", "MEDICO", "OUTRO"],
    prioridades: ["NORMAL", "IMPORTANTE", "URGENTE"],
  });
  const [mostrarFormularioAcao, setMostrarFormularioAcao] = useState(false);
  const [salvandoAcao, setSalvandoAcao] = useState(false);
  const [acaoEditandoId, setAcaoEditandoId] = useState(null);
  const [novaAcaoPlano, setNovaAcaoPlano] = useState({
    problema_id: "",
    meta_id: "",
    intervencao_farmacoterapia_id: "",
    tipo_acao: "ORIENTACAO",
    descricao: "",
    responsavel: "FARMACEUTICO",
    prazo: "",
    prioridade: "NORMAL",
    status: "PENDENTE",
    resultado: "",
  });

  const [catalogoMedicamentos, setCatalogoMedicamentos] = useState([]);
  const [buscaCatalogoMedicamento, setBuscaCatalogoMedicamento] = useState("");
  const [buscaCatalogoMedicamentoSubstituto, setBuscaCatalogoMedicamentoSubstituto] = useState("");

  useEffect(() => {
    carregarOpcoesFarmacoterapia();
    carregarOpcoesMetas();
    carregarOpcoesPlanoCuidado();
    carregarOpcoesCicloVidaMedicamento();
  }, []);

  useEffect(() => {
    if (abaConsultorio !== "pacientes") return;

    const termo = buscaPacienteProntuario.trim();
    if (termo.length < 3) {
      setPacientes([]);
      setBuscaPacientesRealizada(false);
      return;
    }

    const timer = setTimeout(() => {
      buscarPacientesProntuario(termo);
    }, 450);

    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [buscaPacienteProntuario, abaConsultorio]);

  useEffect(() => {
    if (mostrarFormularioMedicamento) {
      carregarCatalogoMedicamentos(buscaCatalogoMedicamento);
    }
  }, [mostrarFormularioMedicamento]);

  useEffect(() => {
    if (medicamentoCicloVida && acaoCicloVidaMedicamento === "TROCAR") {
      carregarCatalogoMedicamentos(buscaCatalogoMedicamentoSubstituto);
    }
  }, [medicamentoCicloVida, acaoCicloVidaMedicamento, buscaCatalogoMedicamentoSubstituto]);

  function podeRegistrarClinico() {
    if (!usuario) return false;

    const normalizar = (valor) =>
      String(valor || "")
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase()
        .trim();

    const perfil = normalizar(usuario.perfil || usuario.role || usuario.tipo_usuario);
    const categoria = normalizar(usuario.categoria_profissional || usuario.profissao || usuario.funcao);

    if ([perfil, categoria].some((v) => v.includes("leitura") || v.includes("visualizador"))) {
      return false;
    }

    if ([perfil, categoria].some((v) =>
      v.includes("admin") ||
      v.includes("farmaceut") ||
      v.includes("docente") ||
      v.includes("preceptor") ||
      v.includes("residente") ||
      v.includes("estagi")
    )) {
      return true;
    }

    // Mantém a usabilidade do ambiente de desenvolvimento: usuário autenticado pode registrar,
    // exceto quando explicitamente marcado como leitura/visualizador.
    return true;
  }

  function traduzirTipoEvento(tipo) {
    const chave = String(tipo || "").toLowerCase();
    const mapa = {
      ceaf: "CEAF",
      agenda: "Agenda",
      documentos: "Documentos",
      ocr: "OCR documental",
      consultorio: "Consultório",
      farmacoterapia: "Farmacoterapia",
      prm: "PRM",
      intervencao: "Intervenção",
      meta: "Meta terapêutica",
      plano: "Plano de cuidado",
      desfecho: "Desfecho",
      evolucao_clinica: "Evolução clínica",
      intervencao_farmacoterapeutica: "Intervenção farmacoterapêutica",
      desfecho_clinico: "Desfecho clínico",
      desfecho_intervencao: "Desfecho da intervenção",
      medicamento_registrado: "Medicamento registrado",
      prm_identificado: "PRM identificado",
      meta_terapeutica: "Meta terapêutica",
      acao_plano_cuidado: "Ação do plano de cuidado",
      ocr_executado: "OCR executado",
      documento_anexado: "Documento anexado",
      status_documental: "Status documental",
      processo_documental: "Processo documental",
      retirada: "Retirada",
      inclusao: "Inclusão",
      renovacao: "Renovação",
      adequacao: "Adequação",
      encerramento: "Encerramento",
    };

    return mapa[chave] || String(tipo || "Evento").replaceAll("_", " ").toLowerCase();
  }

  function iconeTimeline(evento) {
    const categoria = String(evento?.categoria || evento?.tipo || "").toUpperCase();
    const tipo = String(evento?.tipo || "").toUpperCase();
    if (categoria === "CEAF" || ["RETIRADA", "INCLUSAO", "RENOVACAO", "ADEQUACAO", "ENCERRAMENTO"].includes(tipo)) return "🏥";
    if (categoria === "AGENDA") return "📅";
    if (categoria === "DOCUMENTOS") return "📄";
    if (categoria === "OCR") return "🔎";
    if (categoria === "CONSULTORIO") return "🩺";
    if (categoria === "FARMACOTERAPIA") return "💊";
    if (categoria === "PRM") return "⚠️";
    if (categoria === "INTERVENCAO") return "🧭";
    if (categoria === "META") return "🎯";
    if (categoria === "PLANO") return "📌";
    if (categoria === "DESFECHO") return "📈";
    return "•";
  }

  function traduzirStatus(valor) {
    if (!valor) return "—";
    return String(valor).replaceAll("_", " ").toLowerCase();
  }

  function ehStatusAberto(status) {
    return ["ABERTO", "EM_ACOMPANHAMENTO", "PENDENTE", "EM_ANDAMENTO", "ATIVA"].includes(
      String(status || "").toUpperCase()
    );
  }

  async function carregarResumoCuidado(pacienteId) {
    try {
      const response = await api.get(`/consultorio/paciente-clinico/${pacienteId}/resumo-cuidado`);
      const resumo = response.data || null;
      setResumoCuidado(resumo);
      setMedicamentos(resumo?.farmacoterapia?.medicamentos || []);
      setIntervencoesFarmacoterapia(resumo?.intervencoes_farmacoterapia || []);
      setLinhaTempoClinica(resumo?.timeline || []);
      setAvaliacaoPolifarmacia(resumo?.farmacoterapia?.complexidade || null);
      return resumo;
    } catch (error) {
      console.warn("Resumo de cuidado indisponível; mantendo carregamento legado.", error.response?.data || error);
      setResumoCuidado(null);
      return null;
    }
  }

  async function carregarOpcoesFarmacoterapia() {
    try {
      const response = await api.get("/consultorio/farmacoterapia/opcoes");
      setOpcoesFarmacoterapia(response.data || { vias_administracao: [], horarios_padrao: [], frequencias_uso: [] });
    } catch (error) {
      console.warn("Opções de farmacoterapia indisponíveis.", error.response?.data || error);
    }
  }


  async function carregarOpcoesCicloVidaMedicamento() {
    try {
      const response = await api.get("/consultorio/farmacoterapia/opcoes");
      setOpcoesCicloVidaMedicamento((atual) => ({ ...atual, ...(response.data || {}) }));
    } catch (error) {
      console.warn("Opções do ciclo de vida da farmacoterapia indisponíveis.", error.response?.data || error);
    }
  }

  function abrirAcaoMedicamento(medicamento, acao) {
    setMedicamentoCicloVida(medicamento);
    setAcaoCicloVidaMedicamento(acao);
    setFormCicloVidaMedicamento({
      data_evento: new Date().toISOString().slice(0, 10),
      motivo: "",
      tipo_suspensao: "DEFINITIVA",
      prm_relacionado_id: "",
      intervencao_relacionada_id: "",
      observacao: "",
    });
    setMedicamentoSubstituto({
      catalogo_medicamento_id: "",
      nome_medicamento: "",
      dose: "",
      via: medicamento?.via || "",
      frequencia: "",
      frequencia_uso: "",
      horarios_uso: "",
      uso_se_necessario: false,
      indicacao: medicamento?.indicacao || "",
      uso_continuo: true,
      adesao_referida: "",
      observacoes: "",
    });
    setBuscaCatalogoMedicamentoSubstituto("");
  }

  function fecharAcaoMedicamento() {
    setMedicamentoCicloVida(null);
    setAcaoCicloVidaMedicamento(null);
  }

  async function salvarCicloVidaMedicamento() {
    if (!medicamentoCicloVida?.id || !acaoCicloVidaMedicamento) return;
    if (!formCicloVidaMedicamento.motivo) {
      alert("Informe o motivo da alteração da farmacoterapia.");
      return;
    }

    try {
      setSalvandoCicloVidaMedicamento(true);
      const prmId = formCicloVidaMedicamento.prm_relacionado_id ? Number(formCicloVidaMedicamento.prm_relacionado_id) : null;
      const intervencaoId = formCicloVidaMedicamento.intervencao_relacionada_id ? Number(formCicloVidaMedicamento.intervencao_relacionada_id) : null;

      if (acaoCicloVidaMedicamento === "TROCAR") {
        if (!medicamentoSubstituto.catalogo_medicamento_id && !medicamentoSubstituto.nome_medicamento.trim()) {
          alert("Informe o medicamento substituto.");
          return;
        }
        await api.post(`/consultorio/medicamentos/${medicamentoCicloVida.id}/trocar`, {
          novo_medicamento: {
            ...medicamentoSubstituto,
            catalogo_medicamento_id: medicamentoSubstituto.catalogo_medicamento_id ? Number(medicamentoSubstituto.catalogo_medicamento_id) : null,
          },
          data_troca: formCicloVidaMedicamento.data_evento || null,
          motivo_troca: formCicloVidaMedicamento.motivo,
          prm_relacionado_id: prmId,
          intervencao_relacionada_id: intervencaoId,
          observacao: formCicloVidaMedicamento.observacao,
        });
      } else if (acaoCicloVidaMedicamento === "SUSPENDER") {
        await api.post(`/consultorio/medicamentos/${medicamentoCicloVida.id}/suspender`, {
          data_suspensao: formCicloVidaMedicamento.data_evento || null,
          motivo_suspensao: formCicloVidaMedicamento.motivo,
          tipo_suspensao: formCicloVidaMedicamento.tipo_suspensao,
          prm_relacionado_id: prmId,
          intervencao_relacionada_id: intervencaoId,
          observacao: formCicloVidaMedicamento.observacao,
        });
      } else if (acaoCicloVidaMedicamento === "ENCERRAR") {
        await api.post(`/consultorio/medicamentos/${medicamentoCicloVida.id}/encerrar`, {
          data_encerramento: formCicloVidaMedicamento.data_evento || null,
          motivo_encerramento: formCicloVidaMedicamento.motivo,
          prm_relacionado_id: prmId,
          intervencao_relacionada_id: intervencaoId,
          observacao: formCicloVidaMedicamento.observacao,
        });
      }

      fecharAcaoMedicamento();
      await atualizarProntuario(pacienteSelecionado.id);
      alert("Evolução da farmacoterapia registrada com sucesso.");
    } catch (error) {
      console.error("Erro ao registrar ciclo de vida do medicamento:", error.response?.data || error);
      alert("Erro ao registrar evolução da farmacoterapia.");
    } finally {
      setSalvandoCicloVidaMedicamento(false);
    }
  }

  async function carregarOpcoesMetas() {
    try {
      const response = await api.get("/consultorio/metas/opcoes");
      const data = response.data || {};
      setOpcoesMetas({
        categorias: data.categorias || [],
        subcategorias: data.subcategorias || {},
        unidades: data.unidades || [],
        status: data.status || [],
        origens: data.origens || [],
      });
    } catch (error) {
      console.warn("Opções de metas terapêuticas indisponíveis.", error.response?.data || error);
    }
  }

  function resetarFormularioMeta() {
    setMetaEditandoId(null);
    setNovaMeta({
      prm_id: "",
      intervencao_farmacoterapia_id: "",
      categoria: "CONTROLE_CLINICO",
      subcategoria: "PRESSAO_ARTERIAL",
      descricao: "",
      valor_atual: "",
      valor_alvo: "",
      unidade: "",
      data_inicial: "",
      data_prevista: "",
      data_conclusao: "",
      status: "EM_ANDAMENTO",
      origem: "CONSULTA",
    });
  }

  function abrirNovaMeta() {
    resetarFormularioMeta();
    setMostrarFormularioMeta(true);
  }

  function iniciarEdicaoMeta(meta) {
    const categoria = meta.categoria || "CONTROLE_CLINICO";
    const subcategorias = opcoesMetas.subcategorias?.[categoria] || [];
    setMetaEditandoId(meta.id);
    setNovaMeta({
      prm_id: meta.prm_id || "",
      intervencao_farmacoterapia_id: meta.intervencao_farmacoterapia_id || "",
      categoria,
      subcategoria: meta.subcategoria || subcategorias[0] || "OUTRA",
      descricao: meta.descricao || "",
      valor_atual: meta.valor_atual || "",
      valor_alvo: meta.valor_alvo || "",
      unidade: meta.unidade || "",
      data_inicial: String(meta.data_inicial || "").slice(0, 10),
      data_prevista: String(meta.data_prevista || meta.prazo || "").slice(0, 10),
      data_conclusao: String(meta.data_conclusao || "").slice(0, 10),
      status: meta.status || "EM_ANDAMENTO",
      origem: meta.origem || "CONSULTA",
    });
    setMostrarFormularioMeta(true);
  }

  async function salvarMetaTerapeutica() {
    if (!pacienteSelecionado?.id) {
      alert("Selecione um paciente antes de registrar a meta.");
      return;
    }
    if (!novaMeta.descricao.trim()) {
      alert("Informe a descrição da meta terapêutica.");
      return;
    }
    setSalvandoMeta(true);
    try {
      const payload = {
        paciente_id: pacienteSelecionado.id,
        prm_id: novaMeta.prm_id || null,
        intervencao_farmacoterapia_id: novaMeta.intervencao_farmacoterapia_id || null,
        categoria: novaMeta.categoria,
        subcategoria: novaMeta.subcategoria,
        descricao: novaMeta.descricao,
        valor_atual: novaMeta.valor_atual || null,
        valor_alvo: novaMeta.valor_alvo || null,
        unidade: novaMeta.unidade || null,
        data_inicial: novaMeta.data_inicial || null,
        data_prevista: novaMeta.data_prevista || null,
        data_conclusao: novaMeta.data_conclusao || null,
        status: novaMeta.status || "EM_ANDAMENTO",
        origem: novaMeta.origem || "CONSULTA",
      };

      if (metaEditandoId) {
        await api.put(`/consultorio/metas/${metaEditandoId}`, payload);
      } else {
        await api.post("/consultorio/metas", payload);
      }

      resetarFormularioMeta();
      setMostrarFormularioMeta(false);
      await carregarResumoCuidado(pacienteSelecionado.id);
    } catch (error) {
      console.error(error);
      alert(error.response?.data?.detail || "Não foi possível salvar a meta terapêutica.");
    } finally {
      setSalvandoMeta(false);
    }
  }


  async function carregarOpcoesPlanoCuidado() {
    try {
      const response = await api.get("/consultorio/cuidado/opcoes");
      const data = response.data || {};
      setOpcoesPlanoCuidado({
        tipos_acao: data.tipos_acao || ["ORIENTACAO", "MONITORAMENTO", "ENCAMINHAMENTO", "CONTATO", "EDUCACAO_SAUDE", "OUTRO"],
        status_acao: data.status_acao || ["PENDENTE", "EM_ANDAMENTO", "CONCLUIDA", "CANCELADA"],
        responsaveis: data.responsaveis || ["FARMACEUTICO", "PACIENTE", "CUIDADOR", "EQUIPE_APS", "MEDICO", "OUTRO"],
        prioridades: data.prioridades || ["NORMAL", "IMPORTANTE", "URGENTE"],
      });
    } catch (error) {
      console.warn("Opções do plano de cuidado indisponíveis.", error.response?.data || error);
    }
  }

  function resetarFormularioAcaoPlano() {
    setAcaoEditandoId(null);
    setNovaAcaoPlano({
      problema_id: "",
      meta_id: "",
      intervencao_farmacoterapia_id: "",
      tipo_acao: "ORIENTACAO",
      descricao: "",
      responsavel: "FARMACEUTICO",
      prazo: "",
      prioridade: "NORMAL",
      status: "PENDENTE",
      resultado: "",
    });
  }

  function abrirNovaAcaoPlano() {
    resetarFormularioAcaoPlano();
    setMostrarFormularioAcao(true);
  }

  function iniciarEdicaoAcaoPlano(acao) {
    setAcaoEditandoId(acao.id);
    setNovaAcaoPlano({
      problema_id: acao.problema_id || "",
      meta_id: acao.meta_id || "",
      intervencao_farmacoterapia_id: acao.intervencao_farmacoterapia_id || "",
      tipo_acao: acao.tipo_acao || "ORIENTACAO",
      descricao: acao.descricao || "",
      responsavel: acao.responsavel || "FARMACEUTICO",
      prazo: String(acao.prazo || "").slice(0, 10),
      prioridade: acao.prioridade || "NORMAL",
      status: acao.status || "PENDENTE",
      resultado: acao.resultado || "",
    });
    setMostrarFormularioAcao(true);
  }

  async function salvarAcaoPlanoCuidado() {
    if (!pacienteSelecionado?.id) {
      alert("Selecione um paciente antes de registrar a ação do plano.");
      return;
    }
    if (!novaAcaoPlano.descricao.trim()) {
      alert("Informe a descrição da ação do plano de cuidado.");
      return;
    }
    setSalvandoAcao(true);
    try {
      const payload = {
        problema_id: novaAcaoPlano.problema_id || null,
        meta_id: novaAcaoPlano.meta_id || null,
        intervencao_farmacoterapia_id: novaAcaoPlano.intervencao_farmacoterapia_id || null,
        tipo_acao: novaAcaoPlano.tipo_acao || "OUTRO",
        descricao: novaAcaoPlano.descricao,
        responsavel: novaAcaoPlano.responsavel || null,
        prazo: novaAcaoPlano.prazo || null,
        prioridade: novaAcaoPlano.prioridade || "NORMAL",
        status: novaAcaoPlano.status || "PENDENTE",
        resultado: novaAcaoPlano.resultado || null,
      };

      if (acaoEditandoId) {
        await api.put(`/consultorio/acoes-plano-cuidado/${acaoEditandoId}/status`, {
          status: payload.status,
          resultado: payload.resultado,
        });
      } else {
        await api.post(`/consultorio/paciente-clinico/${pacienteSelecionado.id}/acoes-plano-cuidado`, payload);
      }

      resetarFormularioAcaoPlano();
      setMostrarFormularioAcao(false);
      await carregarResumoCuidado(pacienteSelecionado.id);
    } catch (error) {
      console.error(error);
      alert(error.response?.data?.detail || "Não foi possível salvar a ação do plano de cuidado.");
    } finally {
      setSalvandoAcao(false);
    }
  }

  async function carregarCatalogoMedicamentos(busca = "") {
    try {
      const response = await api.get("/consultorio/catalogo-medicamentos", {
        params: { busca: busca || undefined, ativo: true, limite: 80 },
      });
      setCatalogoMedicamentos(response.data?.medicamentos || []);
    } catch (error) {
      console.warn("Catálogo de medicamentos indisponível.", error.response?.data || error);
      setCatalogoMedicamentos([]);
    }
  }

  function aplicarMedicamentoCatalogo(catalogoId) {
    const selecionado = catalogoMedicamentos.find((m) => String(m.id) === String(catalogoId));
    setNovoMedicamento((atual) => ({
      ...atual,
      catalogo_medicamento_id: catalogoId,
      nome_medicamento: selecionado?.descricao_completa || atual.nome_medicamento,
      dose: atual.dose || selecionado?.concentracao || "",
      via: atual.via || inferirViaPorFormaFarmaceutica(selecionado?.forma_farmaceutica),
    }));
  }

  function aplicarMedicamentoSubstitutoCatalogo(catalogoId) {
    const selecionado = catalogoMedicamentos.find((m) => String(m.id) === String(catalogoId));
    setMedicamentoSubstituto((atual) => ({
      ...atual,
      catalogo_medicamento_id: catalogoId,
      nome_medicamento: selecionado?.descricao_completa || atual.nome_medicamento,
      dose: atual.dose || selecionado?.concentracao || "",
      via: atual.via || inferirViaPorFormaFarmaceutica(selecionado?.forma_farmaceutica),
    }));
  }

  function inferirViaPorFormaFarmaceutica(forma) {
    const texto = String(forma || "").toLowerCase();
    if (texto.includes("inal")) return "inalatória";
    if (texto.includes("injet")) return "subcutânea";
    if (texto.includes("comprim") || texto.includes("cápsula") || texto.includes("capsula")) return "oral";
    return "";
  }

  async function buscarPacientesProntuario(termoBusca = buscaPacienteProntuario) {
    const termo = String(termoBusca || "").trim();

    if (termo.length < 3) {
      setPacientes([]);
      setBuscaPacientesRealizada(false);
      return;
    }

    try {
      setLoading(true);
      setBuscaPacientesRealizada(true);
      const response = await api.get("/consultorio/pacientes-clinicos/buscar", {
        params: { termo, limit: 30 },
      });
      setPacientes(response.data.pacientes || []);
    } catch (error) {
      console.error("Erro ao buscar pacientes:", error.response?.data || error);
      alert("Erro ao buscar pacientes.");
      setPacientes([]);
    } finally {
      setLoading(false);
    }
  }

  async function carregarMedicamentos(pacienteId) {
    const response = await api.get(`/consultorio/paciente-clinico/${pacienteId}/medicamentos`);
    setMedicamentos(response.data || []);
  }


  async function carregarAvaliacaoPolifarmacia(pacienteId) {
    try {
      const response = await api.get(
        `/consultorio/paciente-clinico/${pacienteId}/avaliacao-polifarmacia`
      );
      setAvaliacaoPolifarmacia(response.data);
    } catch (error) {
      console.error("Erro ao carregar avaliação farmacoterapêutica:", error.response?.data || error);
      setAvaliacaoPolifarmacia(null);
    }
  }

  async function carregarEvolucaoFarmacoterapeutica(pacienteId) {
    try {
      const response = await api.get(
        `/consultorio/paciente-clinico/${pacienteId}/evolucao-farmacoterapeutica`
      );
      setEvolucaoFarmacoterapeutica(response.data);
    } catch (error) {
      console.error("Erro ao carregar evolução farmacoterapêutica:", error.response?.data || error);
      setEvolucaoFarmacoterapeutica(null);
    }
  }

  async function carregarIntervencoes(pacienteId) {
    const response = await api.get(
      `/consultorio/paciente-clinico/${pacienteId}/intervencoes-farmacoterapia`
    );
    setIntervencoesFarmacoterapia(response.data || []);
  }

  async function carregarLinhaTempo(pacienteId) {
    const response = await api.get(`/consultorio/paciente-clinico/${pacienteId}/linha-tempo`);
    setLinhaTempoClinica(response.data.eventos || []);
  }

  async function atualizarProntuario(pacienteId) {
    const resumo = await carregarResumoCuidado(pacienteId);
    if (resumo) {
      await carregarEvolucaoFarmacoterapeutica(pacienteId);
      return;
    }

    await carregarMedicamentos(pacienteId);
    await carregarIntervencoes(pacienteId);
    await carregarLinhaTempo(pacienteId);
    await carregarAvaliacaoPolifarmacia(pacienteId);
    await carregarEvolucaoFarmacoterapeutica(pacienteId);
  }

  async function abrirProntuario(paciente) {
    try {
      setLoadingProntuario(true);
      setPacienteSelecionado(paciente);
      setMostrarFormularioEvolucao(false);
      setMostrarFormularioMedicamento(false);
      setMostrarFormularioIntervencao(false);
      setEvolucaoParaDesfecho(null);
      setIntervencaoParaDesfecho(null);
      setAbaProntuario("resumo");

      const detalheResponse = await api.get(`/consultorio/paciente-clinico/${paciente.id}`);
      setDetalhe(detalheResponse.data);

      setIdentificacaoPaciente({
        cpf: paciente.cpf || "",
        cns: paciente.cns || "",
        nome_mae: paciente.nome_mae || "",
        telefone: paciente.telefone || "",
        endereco: paciente.endereco || "",
        bairro: paciente.bairro || "",
      });

      setPerfilClinico({
        cid_principal: paciente.cid_principal || "",
        cid_secundario: paciente.cid_secundario || "",
        comorbidades: paciente.comorbidades || "",
        alergias: paciente.alergias || "",
        tabagismo: paciente.tabagismo || "",
        etilismo: paciente.etilismo || "",
        atividade_fisica: paciente.atividade_fisica || "",
        historico_familiar: paciente.historico_familiar || "",
        pessoa_com_deficiencia: paciente.pessoa_com_deficiencia || false,
        tipo_deficiencia: paciente.tipo_deficiencia || "",
        vacinacao_influenza: paciente.vacinacao_influenza || false,
        vacinacao_covid: paciente.vacinacao_covid || false,
        adesao_terapeutica: paciente.adesao_terapeutica || "",
        meta_pressao_arterial: paciente.meta_pressao_arterial || "",
        meta_glicemica: paciente.meta_glicemica || "",
        meta_peso: paciente.meta_peso || "",
        observacoes_clinicas: paciente.observacoes_clinicas || "",
      });

      await atualizarProntuario(paciente.id);
      await carregarPlanosCuidado(paciente.id);
      await carregarSugestoesPlano(paciente.id);
    } catch (error) {
      console.error("Erro ao abrir prontuário:", error.response?.data || error);
      alert("Erro ao abrir prontuário.");
    } finally {
      setLoadingProntuario(false);
    }
  }

  function voltarLista() {
    setPacienteSelecionado(null);
    setDetalhe(null);
    setResumoCuidado(null);
    setLinhaTempoClinica([]);
    setMedicamentos([]);
    setIntervencoesFarmacoterapia([]);
    setMostrarFormularioEvolucao(false);
    setMostrarFormularioMedicamento(false);
    setMostrarFormularioIntervencao(false);
    setEvolucaoParaDesfecho(null);
    setIntervencaoParaDesfecho(null);
    setAvaliacaoPolifarmacia(null);
    setEvolucaoFarmacoterapeutica(null);
    setAbaProntuario("resumo");
    setPlanosCuidado([]);
    setMostrarFormularioPlano(false);
    setPlanoEditando(null);
    setSugestoesPlano(null);
  }

  async function abrirPdfAutenticado(url) {
    try {
      const response = await api.get(url, { responseType: "blob" });
      const fileURL = window.URL.createObjectURL(
        new Blob([response.data], { type: "application/pdf" })
      );
      window.open(fileURL, "_blank");
    } catch (error) {
      console.error("Erro ao abrir PDF:", error.response?.data || error);
      alert("Erro ao abrir PDF autenticado.");
    }
  }

  async function salvarIdentificacaoPaciente() {
    if (!pacienteSelecionado?.id) {
      alert("Paciente não selecionado.");
      return;
    }

    try {
      setSalvandoIdentificacao(true);

      const response = await api.put(
        `/consultorio/paciente-clinico/${pacienteSelecionado.id}/identificacao`,
        identificacaoPaciente
      );

      setPacienteSelecionado(response.data.paciente);
      setMostrarEdicaoIdentificacao(false);
      alert("Identificação atualizada com sucesso.");
    } catch (error) {
      console.error("Erro ao atualizar identificação:", error.response?.data || error);
      alert("Erro ao atualizar identificação.");
    } finally {
      setSalvandoIdentificacao(false);
    }
  }

  async function salvarPerfilClinico() {
    if (!pacienteSelecionado?.id) {
      alert("Paciente não selecionado.");
      return;
    }

    try {
      setSalvandoPerfilClinico(true);

      const response = await api.put(
        `/consultorio/paciente-clinico/${pacienteSelecionado.id}/dados-clinicos`,
        perfilClinico
      );

      setPacienteSelecionado(response.data.paciente);
      setMostrarPerfilClinico(false);
      alert("Perfil clínico atualizado com sucesso.");
    } catch (error) {
      console.error("Erro ao salvar perfil clínico:", error.response?.data || error);
      alert("Erro ao salvar perfil clínico.");
    } finally {
      setSalvandoPerfilClinico(false);
    }
  }

  async function salvarMedicamento() {
    if (!pacienteSelecionado?.id) {
      alert("Paciente não selecionado.");
      return;
    }

    if (!novoMedicamento.catalogo_medicamento_id && !novoMedicamento.nome_medicamento.trim()) {
      alert("Selecione um medicamento do catálogo ou informe o nome manualmente.");
      return;
    }

    try {
      setSalvandoMedicamento(true);

      const payload = {
        ...novoMedicamento,
        catalogo_medicamento_id: novoMedicamento.catalogo_medicamento_id
          ? Number(novoMedicamento.catalogo_medicamento_id)
          : null,
      };

      await api.post(
        `/consultorio/paciente-clinico/${pacienteSelecionado.id}/medicamento`,
        payload
      );

      setNovoMedicamento({
        catalogo_medicamento_id: "",
        nome_medicamento: "",
        dose: "",
        via: "",
        frequencia: "",
        frequencia_uso: "",
        horarios_uso: "",
        uso_se_necessario: false,
        indicacao: "",
        uso_continuo: true,
        adesao_referida: "",
        observacoes: "",
      });

      setMostrarFormularioMedicamento(false);
      await atualizarProntuario(pacienteSelecionado.id);

      alert("Medicamento registrado com sucesso.");
    } catch (error) {
      console.error("Erro ao salvar medicamento:", error.response?.data || error);
      alert("Erro ao salvar medicamento.");
    } finally {
      setSalvandoMedicamento(false);
    }
  }

  async function salvarEvolucao() {
    if (!detalhe?.prontuario?.id) {
      alert("Prontuário não localizado.");
      return;
    }

    try {
      setSalvandoEvolucao(true);

      await api.post(`/consultorio/prontuario/${detalhe.prontuario.id}/evolucao`, {
        ...novaEvolucao,
        data_retorno_sugerida: novaEvolucao.data_retorno_sugerida || null,
      });

      setNovaEvolucao({
        tipo_atendimento: "Consulta farmacêutica",
        queixa_principal: "",
        historia_breve: "",
        avaliacao_farmaceutica: "",
        problemas_identificados: "",
        conduta: "",
        orientacoes_realizadas: "",
        plano_acompanhamento: "",
        necessidade_retorno: false,
        data_retorno_sugerida: "",
        observacoes: "",
      });

      setMostrarFormularioEvolucao(false);
      await atualizarProntuario(pacienteSelecionado.id);

      alert("Evolução clínica registrada com sucesso.");
    } catch (error) {
      console.error("Erro ao salvar evolução:", error.response?.data || error);
      alert("Erro ao salvar evolução clínica.");
    } finally {
      setSalvandoEvolucao(false);
    }
  }

  async function salvarDesfecho() {
    if (!evolucaoParaDesfecho?.evolucao_id) {
      alert("Evolução não localizada.");
      return;
    }

    try {
      setSalvandoDesfecho(true);

      await api.post(
        `/consultorio/evolucao/${evolucaoParaDesfecho.evolucao_id}/desfecho`,
        novoDesfecho
      );

      setNovoDesfecho({
        melhora_clinica: "parcial",
        adesao_tratamento: "regular",
        resolucao_problema: false,
        necessidade_encaminhamento: false,
        encaminhamento_realizado: "",
        resultado_observado: "",
        observacoes: "",
      });

      setEvolucaoParaDesfecho(null);
      await atualizarProntuario(pacienteSelecionado.id);

      alert("Desfecho registrado com sucesso.");
    } catch (error) {
      console.error("Erro ao salvar desfecho:", error.response?.data || error);
      alert("Erro ao salvar desfecho.");
    } finally {
      setSalvandoDesfecho(false);
    }
  }

  async function salvarIntervencaoFarmacoterapia() {
    if (!pacienteSelecionado?.id) {
      alert("Paciente não selecionado.");
      return;
    }

    if (!novaIntervencao.tipo_intervencao) {
      alert("Informe o tipo de intervenção.");
      return;
    }

    try {
      setSalvandoIntervencao(true);

      await api.post(
        `/consultorio/paciente-clinico/${pacienteSelecionado.id}/intervencao-farmacoterapia`,
        {
          ...novaIntervencao,
          medicamento_uso_id: novaIntervencao.medicamento_uso_id
            ? Number(novaIntervencao.medicamento_uso_id)
            : null,
        }
      );

      setNovaIntervencao({
        medicamento_uso_id: "",
        tipo_intervencao: "",
        descricao: "",
        conduta: "",
        aceita_pelo_paciente: false,
        necessidade_encaminhamento: false,
        observacoes: "",
      });

      setMostrarFormularioIntervencao(false);
      await atualizarProntuario(pacienteSelecionado.id);

      alert("Intervenção farmacêutica registrada com sucesso.");
    } catch (error) {
      console.error("Erro ao salvar intervenção:", error.response?.data || error);
      alert("Erro ao salvar intervenção farmacêutica.");
    } finally {
      setSalvandoIntervencao(false);
    }
  }

  async function carregarPlanosCuidado(pacienteId) {
    try {
      const response = await api.get(
        `/consultorio/paciente-clinico/${pacienteId}/planos-cuidado`
      );

      setPlanosCuidado(response.data.planos || []);
    } catch (error) {
      console.error("Erro ao carregar planos de cuidado:", error);
      setPlanosCuidado([]);
    }
  }

  function limparFormularioPlano() {
  setNovoPlano({
    problema_identificado: "",
    objetivo_terapeutico: "",
    intervencoes_planejadas: "",
    prazo_reavaliacao: "",
    observacoes: "",
  });

  setPlanoEditando(null);
  setMostrarFormularioPlano(false);
}

async function salvarPlanoCuidado() {
  try {
    if (!pacienteSelecionado) return;

    const payload = {
      problema_identificado: novoPlano.problema_identificado,
      objetivo_terapeutico: novoPlano.objetivo_terapeutico,
      intervencoes_planejadas: novoPlano.intervencoes_planejadas,
      prazo_reavaliacao: novoPlano.prazo_reavaliacao || null,
      observacoes: novoPlano.observacoes,
    };

    if (planoEditando) {
      await api.put(
        `/consultorio/plano-cuidado/${planoEditando.id}`,
        payload
      );
    } else {
      await api.post("/consultorio/plano-cuidado", {
        paciente_id: pacienteSelecionado.id,
        ...payload,
      });
    }

    await carregarPlanosCuidado(pacienteSelecionado.id);

    limparFormularioPlano();
  } catch (error) {
    console.error("Erro ao salvar plano de cuidado:", error);
    alert("Erro ao salvar plano de cuidado.");
  }
}

function editarPlanoCuidado(plano) {
  setPlanoEditando(plano);

  setNovoPlano({
    problema_identificado: plano.problema_identificado || "",
    objetivo_terapeutico: plano.objetivo_terapeutico || "",
    intervencoes_planejadas: plano.intervencoes_planejadas || "",
    prazo_reavaliacao: plano.prazo_reavaliacao || "",
    observacoes: plano.observacoes || "",
  });

  setMostrarFormularioPlano(true);
}

async function concluirPlanoCuidado(plano) {
  const resultado = window.prompt(
    "Descreva o resultado alcançado:"
  );

  if (!resultado) return;

  const classificacao = window.prompt(
    "Classificação: atingido | parcialmente_atingido | nao_atingido | cancelado"
  );

  if (!classificacao) return;

  try {
    await api.post(
      `/consultorio/plano-cuidado/${plano.id}/concluir`,
      {
        resultado,
        resultado_classificacao: classificacao,
      }
    );

    await carregarPlanosCuidado(
      pacienteSelecionado.id
    );
  } catch (error) {
    console.error(error);

    alert(
      "Erro ao concluir plano."
    );
  }
}

  async function carregarSugestoesPlano(pacienteId) {
    try {
      const response = await api.get(
        `/consultorio/paciente-clinico/${pacienteId}/sugestoes-plano-cuidado`
      );

      setSugestoesPlano(response.data);
    } catch (error) {
      console.error(
        "Erro ao carregar sugestões do plano:",
        error
      );

      setSugestoesPlano(null);
    }
  }

  async function salvarDesfechoIntervencao() {
    if (!intervencaoParaDesfecho?.id) {
      alert("Intervenção não selecionada.");
      return;
    }

    try {
      setSalvandoDesfechoIntervencao(true);

      await api.post(
        `/consultorio/intervencao-farmacoterapia/${intervencaoParaDesfecho.id}/desfecho`,
        novoDesfechoIntervencao
      );

      setNovoDesfechoIntervencao({
        status_desfecho: "parcial",
        resultado_observado: "",
        necessidade_nova_intervencao: false,
        observacoes: "",
      });

      setIntervencaoParaDesfecho(null);
      await atualizarProntuario(pacienteSelecionado.id);

      alert("Desfecho da intervenção registrado com sucesso.");
    } catch (error) {
      console.error("Erro ao salvar desfecho da intervenção:", error.response?.data || error);
      alert("Erro ao salvar desfecho da intervenção.");
    } finally {
      setSalvandoDesfechoIntervencao(false);
    }
  }

  const problemasFarmacoterapeuticos = resumoCuidado?.problemas_farmacoterapeuticos || [];
  const metasTerapeuticas = resumoCuidado?.metas_terapeuticas || [];
  const subcategoriasMetaAtual = opcoesMetas.subcategorias?.[novaMeta.categoria] || [];
  const acoesPlanoCuidado = resumoCuidado?.acoes_plano_cuidado || [];
  const complexidadeCuidado = resumoCuidado?.farmacoterapia?.complexidade || avaliacaoPolifarmacia;
  const problemasAbertos = problemasFarmacoterapeuticos.filter((p) => ehStatusAberto(p.status));
  const metasAtivas = metasTerapeuticas.filter((m) => ehStatusAberto(m.status));
  const acoesPendentes = acoesPlanoCuidado.filter((a) => ehStatusAberto(a.status));
  const resumoTimelineUnificada = resumoCuidado?.timeline_unificada?.resumo_por_categoria || {};
  const categoriasTimelineUnificada = Object.entries(resumoTimelineUnificada)
    .filter(([, total]) => Number(total) > 0)
    .sort((a, b) => String(a[0]).localeCompare(String(b[0])));

  if (pacienteSelecionado) {
    return (
      <div>
        <div className="prontuario-actions">
          <button className="secondary-button" onClick={voltarLista}>
            <ArrowLeft size={18} />
            Voltar para pacientes
          </button>

          <button
            className="secondary-button"
            onClick={() =>
              abrirPdfAutenticado(
                `/consultorio/paciente-clinico/${pacienteSelecionado.id}/pdf`
              )
            }
          >
            Prontuário PDF
          </button>

          <button
            className="secondary-button"
            onClick={() => abrirPdfAutenticado(`/consultorio/paciente-clinico/${pacienteSelecionado.id}/plano-cuidado-pdf`)}
          >
            Imprimir plano
          </button>

          <button
            className="secondary-button"
            onClick={() => abrirPdfAutenticado(`/consultorio/paciente-clinico/${pacienteSelecionado.id}/evolucoes-clinicas-pdf`)}
          >
            Imprimir evoluções
          </button>

          <button
            className="secondary-button"
            onClick={() => abrirPdfAutenticado(`/consultorio/paciente-clinico/${pacienteSelecionado.id}/orientacoes-farmaceuticas-pdf`)}
          >
            Imprimir orientações
          </button>

          {podeRegistrarClinico() && (
            <button
              className="primary-button"
              onClick={() => {
                setAbaProntuario("evolucoes");
                setMostrarFormularioEvolucao(!mostrarFormularioEvolucao);
              }}
            >
              {mostrarFormularioEvolucao ? "Cancelar evolução" : "Nova evolução clínica"}
            </button>
          )}

          {pacienteSelecionado?.paciente_simplificado_origem_id && (
            <button
              className="secondary-button"
              onClick={() =>
                abrirPdfAutenticado(
                  `/consultorio/paciente-clinico/${pacienteSelecionado.id}/prontuario-longitudinal-pdf`
                )
              }
            >
              Imprimir prontuário longitudinal
            </button>
          )}
        </div>

        <div className="prontuario-header">
          <div className="avatar-circle">
            <UserRound size={28} />
          </div>

          <div>
            <h2>{pacienteSelecionado.nome}</h2>
            <p className="muted">
              {pacienteSelecionado.idade || "Idade não informada"} anos ·{" "}
              {pacienteSelecionado.sexo || "Sexo não informado"} ·{" "}
              {pacienteSelecionado.bairro || "Bairro não informado"}
            </p>
          </div>
        </div>

        {loadingProntuario ? (
          <p>Carregando prontuário...</p>
        ) : (
          <>
            <div className="care-summary-strip">
              <div className="metric-card">
                <span>Prontuário</span>
                <strong>{detalhe?.prontuario?.status || "—"}</strong>
                <p>ID: {detalhe?.prontuario?.id || "Não localizado"}</p>
              </div>

              <div className="metric-card">
                <span>Complexidade</span>
                <strong>{complexidadeCuidado?.classificacao || "—"}</strong>
                <p>Escore: {complexidadeCuidado?.escore ?? "não calculado"}</p>
              </div>

              <div className="metric-card">
                <span>PRM em aberto</span>
                <strong>{problemasAbertos.length}</strong>
                <p>{problemasFarmacoterapeuticos.length} problemas registrados</p>
              </div>

              <div className="metric-card">
                <span>Metas ativas</span>
                <strong>{metasAtivas.length}</strong>
                <p>{acoesPendentes.length} ações pendentes no plano</p>
              </div>

              <div className="metric-card">
                <span>Timeline</span>
                <strong>{linhaTempoClinica.length}</strong>
                <p>Eventos longitudinais</p>
              </div>
            </div>

            <div className="care-workflow">
              <button
                type="button"
                className={abaProntuario === "resumo" ? "active" : ""}
                onClick={() => setAbaProntuario("resumo")}
              >
                1. Resumo
              </button>

              <button
                type="button"
                className={abaProntuario === "identificacao" ? "active" : ""}
                onClick={() => setAbaProntuario("identificacao")}
              >
                2. Dados do paciente
              </button>

              <button
                type="button"
                className={abaProntuario === "perfil" ? "active" : ""}
                onClick={() => setAbaProntuario("perfil")}
              >
                3. Perfil clínico
              </button>

              <button
                type="button"
                className={abaProntuario === "farmacoterapia" ? "active" : ""}
                onClick={() => setAbaProntuario("farmacoterapia")}
              >
                4. Farmacoterapia
              </button>

              <button
                type="button"
                className={abaProntuario === "intervencoes" ? "active" : ""}
                onClick={() => setAbaProntuario("intervencoes")}
              >
                5. PRM / Intervenções
              </button>

              <button
                type="button"
                className={abaProntuario === "metas" ? "active" : ""}
                onClick={() => setAbaProntuario("metas")}
              >
                6. Metas e ações
              </button>

              <button
                type="button"
                className={abaProntuario === "plano" ? "active" : ""}
                onClick={() => setAbaProntuario("plano")}
              >
                7. Plano narrativo
              </button>

              <button
                type="button"
                className={abaProntuario === "evolucoes" ? "active" : ""}
                onClick={() => setAbaProntuario("evolucoes")}
              >
                8. Evoluções
              </button>

              <button
                type="button"
                className={abaProntuario === "timeline" ? "active" : ""}
                onClick={() => setAbaProntuario("timeline")}
              >
                9. Timeline
              </button>
            </div>

            {abaProntuario === "resumo" && (
              <div className="prontuario-tab-content">
                <div className="care-overview-grid">
                  <div className="form-card">
                    <div className="section-header-row">
                      <div>
                        <h3>Resumo do cuidado farmacêutico</h3>
                        <p className="muted">Visão única para orientar a consulta e reduzir navegação repetida.</p>
                      </div>
                    </div>

                    <div className="cards-grid two">
                      <div className="med-card">
                        <strong>Farmacoterapia</strong>
                        <p>{medicamentos.length} medicamento(s) ativo(s)</p>
                        <p className="muted">Complexidade: {complexidadeCuidado?.classificacao || "não calculada"}</p>
                      </div>

                      <div className="med-card">
                        <strong>Risco farmacoterapêutico</strong>
                        <p>{problemasAbertos.length} PRM em aberto</p>
                        <p className="muted">{complexidadeCuidado?.fatores?.join(", ") || "Sem fatores críticos registrados."}</p>
                      </div>

                      <div className="med-card">
                        <strong>Metas e plano</strong>
                        <p>{metasAtivas.length} meta(s) ativa(s)</p>
                        <p className="muted">{acoesPendentes.length} ação(ões) pendente(s)</p>
                      </div>

                      <div className="med-card">
                        <strong>Longitudinalidade</strong>
                        <p>{linhaTempoClinica.length} evento(s) na timeline</p>
                        <p className="muted">Use a linha do tempo para revisar evolução, intervenções e desfechos.</p>
                      </div>
                    </div>

                    <div className="care-next-actions">
                      <button className="secondary-button" onClick={() => setAbaProntuario("farmacoterapia")}>Revisar medicamentos</button>
                      <button className="secondary-button" onClick={() => setAbaProntuario("intervencoes")}>Registrar PRM/intervenção</button>
                      <button className="secondary-button" onClick={() => setAbaProntuario("metas")}>Metas e ações</button>
                      <button className="secondary-button" onClick={() => setAbaProntuario("plano")}>Síntese narrativa</button>
                    </div>
                  </div>

                  <div className="form-card">
                    <h3>Pontos de atenção</h3>
                    {problemasAbertos.length === 0 && metasAtivas.length === 0 && acoesPendentes.length === 0 ? (
                      <p className="muted">Nenhuma pendência clínica estruturada registrada.</p>
                    ) : (
                      <div className="med-list compact">
                        {problemasAbertos.slice(0, 4).map((p) => (
                          <div className="med-card" key={`prm-resumo-${p.id}`}>
                            <strong>{traduzirStatus(p.tipo)}</strong>
                            <p>{p.descricao || "PRM sem descrição detalhada."}</p>
                            <p className="muted">{p.categoria} · {p.gravidade} · {traduzirStatus(p.status)}</p>
                          </div>
                        ))}

                        {metasAtivas.slice(0, 3).map((m) => (
                          <div className="med-card" key={`meta-resumo-${m.id}`}>
                            <strong>{m.parametro}</strong>
                            <p>{m.descricao}</p>
                            <p className="muted">Alvo: {m.valor_alvo || "não informado"} {m.unidade || ""}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {abaProntuario === "identificacao" && (
            <div className="form-card">
              <div className="section-header-row">
                <div>
                  <h3>Identificação completa</h3>
                  <p className="muted">Dados administrativos e cadastrais do paciente.</p>
                </div>

                {podeRegistrarClinico() && (
                  <button
                    className="secondary-button"
                    onClick={() => setMostrarEdicaoIdentificacao(!mostrarEdicaoIdentificacao)}
                  >
                    {mostrarEdicaoIdentificacao ? "Cancelar" : "Editar identificação"}
                  </button>
                )}
              </div>

              {!mostrarEdicaoIdentificacao ? (
                <div className="cards-grid two">
                  <div className="med-card">
                    <strong>CPF</strong>
                    <p>{pacienteSelecionado?.cpf || "Não informado"}</p>
                  </div>

                  <div className="med-card">
                    <strong>CNS</strong>
                    <p>{pacienteSelecionado?.cns || "Não informado"}</p>
                  </div>

                  <div className="med-card">
                    <strong>Nome da mãe</strong>
                    <p>{pacienteSelecionado?.nome_mae || "Não informado"}</p>
                  </div>

                  <div className="med-card">
                    <strong>Telefone</strong>
                    <p>{pacienteSelecionado?.telefone || "Não informado"}</p>
                  </div>

                  <div className="med-card">
                    <strong>Endereço</strong>
                    <p>{pacienteSelecionado?.endereco || "Não informado"}</p>
                  </div>

                  <div className="med-card">
                    <strong>Bairro</strong>
                    <p>{pacienteSelecionado?.bairro || "Não informado"}</p>
                  </div>
                </div>
              ) : (
                <div className="nested-form">
                  <div className="form-grid">
                    <input
                      className="input"
                      placeholder="CPF"
                      value={identificacaoPaciente.cpf}
                      onChange={(e) =>
                        setIdentificacaoPaciente({
                          ...identificacaoPaciente,
                          cpf: e.target.value,
                        })
                      }
                    />

                    <input
                      className="input"
                      placeholder="CNS"
                      value={identificacaoPaciente.cns}
                      onChange={(e) =>
                        setIdentificacaoPaciente({
                          ...identificacaoPaciente,
                          cns: e.target.value,
                        })
                      }
                    />
                  </div>

                  <input
                    className="input"
                    placeholder="Nome da mãe"
                    value={identificacaoPaciente.nome_mae}
                    onChange={(e) =>
                      setIdentificacaoPaciente({
                        ...identificacaoPaciente,
                        nome_mae: e.target.value,
                      })
                    }
                  />

                  <input
                    className="input"
                    placeholder="Telefone"
                    value={identificacaoPaciente.telefone}
                    onChange={(e) =>
                      setIdentificacaoPaciente({
                        ...identificacaoPaciente,
                        telefone: e.target.value,
                      })
                    }
                  />

                  <textarea
                    className="textarea"
                    placeholder="Endereço"
                    value={identificacaoPaciente.endereco}
                    onChange={(e) =>
                      setIdentificacaoPaciente({
                        ...identificacaoPaciente,
                        endereco: e.target.value,
                      })
                    }
                  />

                  <input
                    className="input"
                    placeholder="Bairro"
                    value={identificacaoPaciente.bairro}
                    onChange={(e) =>
                      setIdentificacaoPaciente({
                        ...identificacaoPaciente,
                        bairro: e.target.value,
                      })
                    }
                  />

                  <button
                    className="primary-button"
                    onClick={salvarIdentificacaoPaciente}
                    disabled={salvandoIdentificacao}
                  >
                    {salvandoIdentificacao ? "Salvando..." : "Salvar identificação"}
                  </button>
                </div>
              )}
            </div>

            )}

            {abaProntuario === "perfil" && (
            <div className="form-card">
              <div className="section-header-row">
                <div>
                  <h3>Perfil clínico ampliado</h3>
                  <p className="muted">
                    Dados clínicos, comorbidades, hábitos, acessibilidade e metas terapêuticas.
                  </p>
                </div>

                {podeRegistrarClinico() && (
                  <button
                    className="secondary-button"
                    onClick={() => setMostrarPerfilClinico(!mostrarPerfilClinico)}
                  >
                    {mostrarPerfilClinico ? "Cancelar" : "Editar perfil clínico"}
                  </button>
                )}
              </div>

              {!mostrarPerfilClinico ? (
                <div className="med-list">
                  <div className="med-card">
                    <strong>CID principal:</strong>{" "}
                    {pacienteSelecionado.cid_principal || "Não informado"}
                    <p>
                      <strong>Comorbidades:</strong>{" "}
                      {pacienteSelecionado.comorbidades || "Não informado"}
                    </p>
                    <p>
                      <strong>Alergias:</strong>{" "}
                      {pacienteSelecionado.alergias || "Não informado"}
                    </p>
                    <p>
                      <strong>Deficiência:</strong>{" "}
                      {pacienteSelecionado.pessoa_com_deficiencia
                        ? pacienteSelecionado.tipo_deficiencia || "Sim"
                        : "Não"}
                    </p>
                    <p>
                      <strong>Adesão terapêutica:</strong>{" "}
                      {pacienteSelecionado.adesao_terapeutica || "Não informada"}
                    </p>
                  </div>
                </div>
              ) : (
                <div className="nested-form">
                  <div className="form-grid">
                    <input
                      className="input"
                      placeholder="CID principal"
                      value={perfilClinico.cid_principal}
                      onChange={(e) =>
                        setPerfilClinico({ ...perfilClinico, cid_principal: e.target.value })
                      }
                    />

                    <input
                      className="input"
                      placeholder="CID secundário"
                      value={perfilClinico.cid_secundario}
                      onChange={(e) =>
                        setPerfilClinico({ ...perfilClinico, cid_secundario: e.target.value })
                      }
                    />
                  </div>

                  <textarea
                    className="textarea"
                    placeholder="Comorbidades"
                    value={perfilClinico.comorbidades}
                    onChange={(e) =>
                      setPerfilClinico({ ...perfilClinico, comorbidades: e.target.value })
                    }
                  />

                  <textarea
                    className="textarea"
                    placeholder="Alergias"
                    value={perfilClinico.alergias}
                    onChange={(e) =>
                      setPerfilClinico({ ...perfilClinico, alergias: e.target.value })
                    }
                  />

                  <div className="form-grid">
                    <select
                      className="input"
                      value={perfilClinico.tabagismo}
                      onChange={(e) =>
                        setPerfilClinico({ ...perfilClinico, tabagismo: e.target.value })
                      }
                    >
                      <option value="">Tabagismo</option>
                      <option value="nao">Não</option>
                      <option value="sim">Sim</option>
                      <option value="ex-tabagista">Ex-tabagista</option>
                    </select>

                    <select
                      className="input"
                      value={perfilClinico.etilismo}
                      onChange={(e) =>
                        setPerfilClinico({ ...perfilClinico, etilismo: e.target.value })
                      }
                    >
                      <option value="">Etilismo</option>
                      <option value="nao">Não</option>
                      <option value="ocasional">Ocasional</option>
                      <option value="frequente">Frequente</option>
                    </select>
                  </div>

                  <select
                    className="input"
                    value={perfilClinico.atividade_fisica}
                    onChange={(e) =>
                      setPerfilClinico({ ...perfilClinico, atividade_fisica: e.target.value })
                    }
                  >
                    <option value="">Atividade física</option>
                    <option value="sedentario">Sedentário</option>
                    <option value="insuficiente">Insuficiente</option>
                    <option value="regular">Regular</option>
                    <option value="intensa">Intensa</option>
                  </select>

                  <textarea
                    className="textarea"
                    placeholder="Histórico familiar"
                    value={perfilClinico.historico_familiar}
                    onChange={(e) =>
                      setPerfilClinico({ ...perfilClinico, historico_familiar: e.target.value })
                    }
                  />

                  <label className="checkbox-line">
                    <input
                      type="checkbox"
                      checked={perfilClinico.pessoa_com_deficiencia}
                      onChange={(e) =>
                        setPerfilClinico({
                          ...perfilClinico,
                          pessoa_com_deficiencia: e.target.checked,
                        })
                      }
                    />
                    Pessoa com deficiência
                  </label>

                  {perfilClinico.pessoa_com_deficiencia && (
                    <input
                      className="input"
                      placeholder="Tipo de deficiência"
                      value={perfilClinico.tipo_deficiencia}
                      onChange={(e) =>
                        setPerfilClinico({ ...perfilClinico, tipo_deficiencia: e.target.value })
                      }
                    />
                  )}

                  <div className="form-grid">
                    <label className="checkbox-line">
                      <input
                        type="checkbox"
                        checked={perfilClinico.vacinacao_influenza}
                        onChange={(e) =>
                          setPerfilClinico({
                            ...perfilClinico,
                            vacinacao_influenza: e.target.checked,
                          })
                        }
                      />
                      Vacinação influenza
                    </label>

                    <label className="checkbox-line">
                      <input
                        type="checkbox"
                        checked={perfilClinico.vacinacao_covid}
                        onChange={(e) =>
                          setPerfilClinico({
                            ...perfilClinico,
                            vacinacao_covid: e.target.checked,
                          })
                        }
                      />
                      Vacinação COVID-19
                    </label>
                  </div>

                  <select
                    className="input"
                    value={perfilClinico.adesao_terapeutica}
                    onChange={(e) =>
                      setPerfilClinico({ ...perfilClinico, adesao_terapeutica: e.target.value })
                    }
                  >
                    <option value="">Adesão terapêutica</option>
                    <option value="boa">Boa</option>
                    <option value="regular">Regular</option>
                    <option value="ruim">Ruim</option>
                    <option value="nao_avaliada">Não avaliada</option>
                  </select>

                  <div className="form-grid">
                    <input
                      className="input"
                      placeholder="Meta pressórica"
                      value={perfilClinico.meta_pressao_arterial}
                      onChange={(e) =>
                        setPerfilClinico({
                          ...perfilClinico,
                          meta_pressao_arterial: e.target.value,
                        })
                      }
                    />

                    <input
                      className="input"
                      placeholder="Meta glicêmica"
                      value={perfilClinico.meta_glicemica}
                      onChange={(e) =>
                        setPerfilClinico({ ...perfilClinico, meta_glicemica: e.target.value })
                      }
                    />
                  </div>

                  <input
                    className="input"
                    placeholder="Meta de peso"
                    value={perfilClinico.meta_peso}
                    onChange={(e) =>
                      setPerfilClinico({ ...perfilClinico, meta_peso: e.target.value })
                    }
                  />

                  <textarea
                    className="textarea"
                    placeholder="Observações clínicas"
                    value={perfilClinico.observacoes_clinicas}
                    onChange={(e) =>
                      setPerfilClinico({
                        ...perfilClinico,
                        observacoes_clinicas: e.target.value,
                      })
                    }
                  />

                  <button
                    className="primary-button"
                    onClick={salvarPerfilClinico}
                    disabled={salvandoPerfilClinico}
                  >
                    {salvandoPerfilClinico ? "Salvando..." : "Salvar perfil clínico"}
                  </button>
                </div>
              )}
            </div>

            )}

            {abaProntuario === "farmacoterapia" && (
              <>
            <div className="form-card">
              <div className="section-header-row">
                <div>
                  <h3>Farmacoterapia em uso</h3>
                  <p className="muted">
                    Medicamentos informados pelo paciente ou registrados na consulta.
                  </p>
                </div>

                {podeRegistrarClinico() && (
                  <button
                    className="secondary-button"
                    onClick={() => setMostrarFormularioMedicamento(!mostrarFormularioMedicamento)}
                  >
                    {mostrarFormularioMedicamento ? "Cancelar" : "Adicionar medicamento"}
                  </button>
                )}
              </div>

              {medicamentos.length === 0 ? (
                <p className="muted">Nenhum medicamento registrado.</p>
              ) : (
                <div className="med-list">
                  {medicamentos.map((m) => (
                    <div className="med-card" key={m.id}>
                      <strong>{m.nome_medicamento}</strong>
                      <p>
                        {m.dose || "Dose não informada"} · {m.via || "Via não informada"} ·{" "}
                        {m.frequencia_uso || m.frequencia || "Frequência não informada"}
                      </p>
                      <p className="muted">
                        Horários: {m.horarios_uso || "não informados"} · {m.uso_se_necessario ? "Uso se necessário" : "Uso programado"}
                      </p>
                      <p className="muted">
                        Indicação: {m.indicacao || "não informada"} · Adesão:{" "}
                        {m.adesao_referida || "não informada"}
                      </p>
                      <p className="muted">
                        Situação: <strong>{m.status_farmacoterapia || (m.ativo ? "EM_USO" : "INATIVO")}</strong>
                        {m.motivo_status ? ` · Motivo: ${m.motivo_status}` : ""}
                      </p>
                      {podeRegistrarClinico() && (m.status_farmacoterapia || "EM_USO") === "EM_USO" && (
                        <div className="inline-actions">
                          <button className="secondary-button" type="button" onClick={() => abrirAcaoMedicamento(m, "TROCAR")}>Trocar</button>
                          <button className="secondary-button" type="button" onClick={() => abrirAcaoMedicamento(m, "SUSPENDER")}>Suspender</button>
                          <button className="secondary-button" type="button" onClick={() => abrirAcaoMedicamento(m, "ENCERRAR")}>Encerrar</button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {mostrarFormularioMedicamento && (

                <div className="nested-form">
                  <div className="form-grid">
                    <input
                      className="input"
                      placeholder="Buscar no catálogo"
                      value={buscaCatalogoMedicamento}
                      onChange={(e) => setBuscaCatalogoMedicamento(e.target.value)}
                      onBlur={() => carregarCatalogoMedicamentos(buscaCatalogoMedicamento)}
                    />
                    <button
                      className="secondary-button"
                      type="button"
                      onClick={() => carregarCatalogoMedicamentos(buscaCatalogoMedicamento)}
                    >
                      Buscar
                    </button>
                  </div>

                  <select
                    className="input"
                    value={novoMedicamento.catalogo_medicamento_id}
                    onChange={(e) => aplicarMedicamentoCatalogo(e.target.value)}
                  >
                    <option value="">Selecionar medicamento do catálogo</option>
                    {catalogoMedicamentos.map((m) => (
                      <option key={m.id} value={m.id}>
                        {m.descricao_completa || `${m.farmaco} ${m.concentracao || ""}`}
                      </option>
                    ))}
                  </select>

                  <input
                    className="input"
                    placeholder="Nome manual, se não encontrado no catálogo"
                    value={novoMedicamento.nome_medicamento}
                    onChange={(e) =>
                      setNovoMedicamento({
                        ...novoMedicamento,
                        nome_medicamento: e.target.value,
                      })
                    }
                  />

                  <div className="form-grid">
                    <input
                      className="input"
                      placeholder="Dose"
                      value={novoMedicamento.dose}
                      onChange={(e) =>
                        setNovoMedicamento({
                          ...novoMedicamento,
                          dose: e.target.value,
                        })
                      }
                    />

                    <select
                      className="input"
                      value={novoMedicamento.via}
                      onChange={(e) =>
                        setNovoMedicamento({
                          ...novoMedicamento,
                          via: e.target.value,
                        })
                      }
                    >
                      <option value="">Via de administração</option>
                      {(opcoesFarmacoterapia.vias_administracao || []).map((via) => (
                        <option key={via} value={via}>{via}</option>
                      ))}
                    </select>
                  </div>

                  <div className="form-grid">
                    <select
                      className="input"
                      value={novoMedicamento.frequencia_uso}
                      onChange={(e) =>
                        setNovoMedicamento({
                          ...novoMedicamento,
                          frequencia_uso: e.target.value,
                          frequencia: e.target.value || novoMedicamento.frequencia,
                        })
                      }
                    >
                      <option value="">Frequência de uso</option>
                      {(opcoesFarmacoterapia.frequencias_uso || []).map((freq) => (
                        <option key={freq} value={freq}>{freq}</option>
                      ))}
                    </select>

                    <input
                      className="input"
                      placeholder="Frequência livre, se necessário"
                      value={novoMedicamento.frequencia}
                      onChange={(e) =>
                        setNovoMedicamento({
                          ...novoMedicamento,
                          frequencia: e.target.value,
                        })
                      }
                    />
                  </div>

                  <select
                    className="input"
                    value={novoMedicamento.horarios_uso}
                    onChange={(e) =>
                      setNovoMedicamento({
                        ...novoMedicamento,
                        horarios_uso: e.target.value,
                        uso_se_necessario: e.target.value === "se necessário" ? true : novoMedicamento.uso_se_necessario,
                      })
                    }
                  >
                    <option value="">Horário principal ou orientação de uso</option>
                    {(opcoesFarmacoterapia.horarios_padrao || []).map((horario) => (
                      <option key={horario} value={horario}>{horario}</option>
                    ))}
                  </select>

                  <label className="checkbox-line">
                    <input
                      type="checkbox"
                      checked={novoMedicamento.uso_se_necessario}
                      onChange={(e) =>
                        setNovoMedicamento({
                          ...novoMedicamento,
                          uso_se_necessario: e.target.checked,
                          frequencia_uso: e.target.checked ? "se necessário" : novoMedicamento.frequencia_uso,
                        })
                      }
                    />
                    Uso se necessário
                  </label>

                  <input
                    className="input"
                    placeholder="Indicação"
                    value={novoMedicamento.indicacao}
                    onChange={(e) =>
                      setNovoMedicamento({
                        ...novoMedicamento,
                        indicacao: e.target.value,
                      })
                    }
                  />

                  <select
                    className="input"
                    value={novoMedicamento.adesao_referida}
                    onChange={(e) =>
                      setNovoMedicamento({
                        ...novoMedicamento,
                        adesao_referida: e.target.value,
                      })
                    }
                  >
                    <option value="">Adesão referida</option>
                    <option value="boa">Boa</option>
                    <option value="regular">Regular</option>
                    <option value="ruim">Ruim</option>
                    <option value="nao_avaliada">Não avaliada</option>
                  </select>

                  <textarea
                    className="textarea"
                    placeholder="Observações"
                    value={novoMedicamento.observacoes}
                    onChange={(e) =>
                      setNovoMedicamento({
                        ...novoMedicamento,
                        observacoes: e.target.value,
                      })
                    }
                  />

                  <button
                    className="primary-button"
                    onClick={salvarMedicamento}
                    disabled={salvandoMedicamento}
                  >
                    {salvandoMedicamento ? "Salvando..." : "Salvar medicamento"}
                  </button>
                </div>
              )}

              {medicamentoCicloVida && acaoCicloVidaMedicamento && (
                <div className="nested-form">
                  <div className="section-header-row">
                    <div>
                      <h4>
                        {acaoCicloVidaMedicamento === "TROCAR" ? "Trocar medicamento" : acaoCicloVidaMedicamento === "SUSPENDER" ? "Suspender medicamento" : "Encerrar medicamento"}
                      </h4>
                      <p className="muted">{medicamentoCicloVida.nome_medicamento}</p>
                    </div>
                    <button className="secondary-button" type="button" onClick={fecharAcaoMedicamento}>Cancelar</button>
                  </div>

                  {acaoCicloVidaMedicamento === "TROCAR" && (
                    <>
                      <div className="form-grid">
                        <input
                          className="input"
                          placeholder="Buscar substituto no catálogo"
                          value={buscaCatalogoMedicamentoSubstituto}
                          onChange={(e) => setBuscaCatalogoMedicamentoSubstituto(e.target.value)}
                        />
                        <select
                          className="input"
                          value={medicamentoSubstituto.catalogo_medicamento_id}
                          onChange={(e) => aplicarMedicamentoSubstitutoCatalogo(e.target.value)}
                        >
                          <option value="">Selecione o substituto no catálogo</option>
                          {catalogoMedicamentos.map((m) => (
                            <option key={m.id} value={m.id}>
                              {m.descricao_completa || `${m.farmaco || m.principio_ativo || "Medicamento"} ${m.apresentacao || ""}`}
                            </option>
                          ))}
                        </select>
                      </div>

                      <div className="form-grid">
                        <input
                          className="input"
                          placeholder="Medicamento não encontrado? Digite manualmente"
                          value={medicamentoSubstituto.nome_medicamento}
                          onChange={(e) => setMedicamentoSubstituto({ ...medicamentoSubstituto, catalogo_medicamento_id: "", nome_medicamento: e.target.value })}
                        />
                        <input className="input" placeholder="Dose" value={medicamentoSubstituto.dose} onChange={(e) => setMedicamentoSubstituto({ ...medicamentoSubstituto, dose: e.target.value })} />
                        <select className="input" value={medicamentoSubstituto.via} onChange={(e) => setMedicamentoSubstituto({ ...medicamentoSubstituto, via: e.target.value })}>
                          <option value="">Via</option>
                          {(opcoesFarmacoterapia.vias_administracao || []).map((via) => <option key={via} value={via}>{via}</option>)}
                        </select>
                        <select className="input" value={medicamentoSubstituto.frequencia_uso} onChange={(e) => setMedicamentoSubstituto({ ...medicamentoSubstituto, frequencia_uso: e.target.value, frequencia: e.target.value })}>
                          <option value="">Frequência</option>
                          {(opcoesFarmacoterapia.frequencias_uso || []).map((freq) => <option key={freq} value={freq}>{freq}</option>)}
                        </select>
                      </div>
                      <input className="input" placeholder="Horários de uso" value={medicamentoSubstituto.horarios_uso} onChange={(e) => setMedicamentoSubstituto({ ...medicamentoSubstituto, horarios_uso: e.target.value })} />
                    </>
                  )}

                  <div className="form-grid">
                    <input className="input" type="date" value={formCicloVidaMedicamento.data_evento} onChange={(e) => setFormCicloVidaMedicamento({ ...formCicloVidaMedicamento, data_evento: e.target.value })} />
                    <select className="input" value={formCicloVidaMedicamento.motivo} onChange={(e) => setFormCicloVidaMedicamento({ ...formCicloVidaMedicamento, motivo: e.target.value })}>
                      <option value="">Motivo</option>
                      {((acaoCicloVidaMedicamento === "TROCAR" ? opcoesCicloVidaMedicamento.motivos_troca : acaoCicloVidaMedicamento === "SUSPENDER" ? opcoesCicloVidaMedicamento.motivos_suspensao : opcoesCicloVidaMedicamento.motivos_encerramento) || []).map((motivo) => (
                        <option key={motivo} value={motivo}>{motivo}</option>
                      ))}
                    </select>
                    {acaoCicloVidaMedicamento === "SUSPENDER" && (
                      <select className="input" value={formCicloVidaMedicamento.tipo_suspensao} onChange={(e) => setFormCicloVidaMedicamento({ ...formCicloVidaMedicamento, tipo_suspensao: e.target.value })}>
                        {(opcoesCicloVidaMedicamento.tipos_suspensao || []).map((tipo) => <option key={tipo} value={tipo}>{tipo}</option>)}
                      </select>
                    )}
                  </div>

                  <div className="form-grid">
                    <select className="input" value={formCicloVidaMedicamento.prm_relacionado_id} onChange={(e) => setFormCicloVidaMedicamento({ ...formCicloVidaMedicamento, prm_relacionado_id: e.target.value })}>
                      <option value="">Associar PRM (opcional)</option>
                      {problemasFarmacoterapeuticos.map((p) => <option key={p.id} value={p.id}>{p.categoria || "PRM"} · {p.subcategoria || p.tipo || p.descricao}</option>)}
                    </select>
                    <select className="input" value={formCicloVidaMedicamento.intervencao_relacionada_id} onChange={(e) => setFormCicloVidaMedicamento({ ...formCicloVidaMedicamento, intervencao_relacionada_id: e.target.value })}>
                      <option value="">Associar intervenção (opcional)</option>
                      {intervencoesFarmacoterapia.map((i) => <option key={i.id} value={i.id}>{i.tipo_intervencao || i.tipo_padronizado || "Intervenção"}</option>)}
                    </select>
                  </div>

                  <textarea className="textarea" placeholder="Observação clínica" value={formCicloVidaMedicamento.observacao} onChange={(e) => setFormCicloVidaMedicamento({ ...formCicloVidaMedicamento, observacao: e.target.value })} />

                  <button className="primary-button" type="button" onClick={salvarCicloVidaMedicamento} disabled={salvandoCicloVidaMedicamento}>
                    {salvandoCicloVidaMedicamento ? "Salvando..." : "Registrar alteração da farmacoterapia"}
                  </button>
                </div>
              )}
            </div>



              <div className="form-card">
                <h3>Avaliação farmacoterapêutica automatizada</h3>

                {!avaliacaoPolifarmacia ? (
                  <p className="muted">Avaliação farmacoterapêutica indisponível.</p>
                ) : (
                  <>
                    <div className="cards-grid four">
                      <div className="metric-card">
                        <span>Medicamentos ativos</span>
                        <strong>{avaliacaoPolifarmacia.total_medicamentos}</strong>
                      </div>

                      <div className={`metric-card ${avaliacaoPolifarmacia.risco || ""}`}>
                        <span>Risco farmacoterapêutico</span>
                        <strong>{avaliacaoPolifarmacia.risco || "—"}</strong>
                      </div>

                      <div className="metric-card warning">
                        <span>Score</span>
                        <strong>{avaliacaoPolifarmacia.score ?? 0}</strong>
                      </div>

                      <div className={`metric-card ${avaliacaoPolifarmacia.polifarmacia ? "danger" : "success"}`}>
                        <span>Polifarmácia</span>
                        <strong>{avaliacaoPolifarmacia.polifarmacia ? "SIM" : "NÃO"}</strong>
                      </div>
                    </div>

                    <div className="clinical-summary">
                      <strong>Interpretação:</strong>
                      <p>{avaliacaoPolifarmacia.interpretacao}</p>
                    </div>

                    <div className="dashboard-grid">
                      <div className="form-card">
                        <h4>Alertas farmacoterapêuticos</h4>
                        <ul className="clinical-list">
                          {(avaliacaoPolifarmacia.alertas || []).map((alerta, index) => (
                            <li key={index}>{alerta}</li>
                          ))}
                        </ul>
                      </div>

                      <div className="form-card">
                        <h4>Recomendações farmacêuticas</h4>
                        <ul className="clinical-list">
                          {(avaliacaoPolifarmacia.recomendacoes || []).map((recomendacao, index) => (
                            <li key={index}>{recomendacao}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </>
                )}
              </div>

              <div className="form-card">
                <h3>Evolução farmacoterapêutica longitudinal</h3>

                {!evolucaoFarmacoterapeutica ? (
                  <p className="muted">Evolução farmacoterapêutica indisponível.</p>
                ) : (
                  <>
                    <div className="cards-grid four">
                      <div className="metric-card">
                        <span>Medicamentos ativos</span>
                        <strong>{evolucaoFarmacoterapeutica.total_medicamentos_ativos}</strong>
                      </div>

                      <div className="metric-card">
                        <span>Intervenções</span>
                        <strong>{evolucaoFarmacoterapeutica.total_intervencoes}</strong>
                      </div>

                      <div className={`metric-card ${evolucaoFarmacoterapeutica.risco_farmacoterapeutico_atual || ""}`}>
                        <span>Risco atual</span>
                        <strong>{evolucaoFarmacoterapeutica.risco_farmacoterapeutico_atual || "—"}</strong>
                      </div>

                      <div className="metric-card warning">
                        <span>Tendência</span>
                        <strong>{evolucaoFarmacoterapeutica.tendencia || "—"}</strong>
                      </div>
                    </div>

                    <div className="clinical-summary">
                      <strong>Interpretação:</strong>
                      <p>{evolucaoFarmacoterapeutica.interpretacao}</p>
                    </div>
                  </>
                )}
              </div>
            </>
            )}

            {abaProntuario === "intervencoes" && (
            <div className="form-card">
              <div className="section-header-row">
                <div>
                  <h3>Intervenções farmacêuticas</h3>
                  <p className="muted">
                    Registro de condutas, orientações, problemas relacionados à farmacoterapia e encaminhamentos.
                  </p>
                </div>

                {podeRegistrarClinico() && (
                  <button
                    className="secondary-button"
                    onClick={() => setMostrarFormularioIntervencao(!mostrarFormularioIntervencao)}
                  >
                    {mostrarFormularioIntervencao ? "Cancelar" : "Adicionar intervenção"}
                  </button>
                )}
              </div>

              <div className="care-subsection">
                <h4>Problemas relacionados à farmacoterapia</h4>
                {problemasFarmacoterapeuticos.length === 0 ? (
                  <p className="muted">Nenhum PRM estruturado registrado para este paciente.</p>
                ) : (
                  <div className="med-list compact">
                    {problemasFarmacoterapeuticos.map((p) => (
                      <div className="med-card" key={`prm-${p.id}`}>
                        <strong>{traduzirStatus(p.tipo)}</strong>
                        <p>{p.descricao || "Sem descrição."}</p>
                        <p className="muted">Categoria: {p.categoria} · Gravidade: {p.gravidade} · Status: {traduzirStatus(p.status)}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {intervencoesFarmacoterapia.length === 0 ? (
                <p className="muted">Nenhuma intervenção registrada.</p>
              ) : (
                <div className="med-list">
                  {intervencoesFarmacoterapia.map((i) => {
                    const medicamento = medicamentos.find((m) => m.id === i.medicamento_uso_id);

                    return (
                      <div className="med-card" key={i.id}>
                        <strong>{i.tipo_intervencao}</strong>

                        <p className="muted">
                          Medicamento: {medicamento?.nome_medicamento || "não vinculado"}
                        </p>

                        {i.descricao && <p>{i.descricao}</p>}

                        {i.conduta && (
                          <p>
                            <strong>Conduta:</strong> {i.conduta}
                          </p>
                        )}

                        <p className="muted">
                          Aceita pelo paciente: {i.aceita_pelo_paciente ? "Sim" : "Não"} ·
                          Encaminhamento: {i.necessidade_encaminhamento ? "Sim" : "Não"}
                        </p>

                        {podeRegistrarClinico() && (
                          <button
                            className="mini-action-button"
                            onClick={() => setIntervencaoParaDesfecho(i)}
                          >
                            Registrar desfecho
                          </button>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}

              {intervencaoParaDesfecho && (
                <div className="nested-form">
                  <h4>Desfecho da intervenção</h4>

                  <p className="muted">
                    Intervenção selecionada: {intervencaoParaDesfecho.tipo_intervencao}
                  </p>

                  <select
                    className="input"
                    value={novoDesfechoIntervencao.status_desfecho}
                    onChange={(e) =>
                      setNovoDesfechoIntervencao({
                        ...novoDesfechoIntervencao,
                        status_desfecho: e.target.value,
                      })
                    }
                  >
                    <option value="resolvido">Resolvido</option>
                    <option value="parcial">Parcialmente resolvido</option>
                    <option value="nao_resolvido">Não resolvido</option>
                    <option value="encaminhado">Encaminhado</option>
                  </select>

                  <textarea
                    className="textarea"
                    placeholder="Resultado observado"
                    value={novoDesfechoIntervencao.resultado_observado}
                    onChange={(e) =>
                      setNovoDesfechoIntervencao({
                        ...novoDesfechoIntervencao,
                        resultado_observado: e.target.value,
                      })
                    }
                  />

                  <label className="checkbox-line">
                    <input
                      type="checkbox"
                      checked={novoDesfechoIntervencao.necessidade_nova_intervencao}
                      onChange={(e) =>
                        setNovoDesfechoIntervencao({
                          ...novoDesfechoIntervencao,
                          necessidade_nova_intervencao: e.target.checked,
                        })
                      }
                    />
                    Necessita nova intervenção
                  </label>

                  <textarea
                    className="textarea"
                    placeholder="Observações"
                    value={novoDesfechoIntervencao.observacoes}
                    onChange={(e) =>
                      setNovoDesfechoIntervencao({
                        ...novoDesfechoIntervencao,
                        observacoes: e.target.value,
                      })
                    }
                  />

                  <div className="form-actions">
                    <button
                      className="secondary-button"
                      onClick={() => setIntervencaoParaDesfecho(null)}
                    >
                      Cancelar
                    </button>

                    <button
                      className="primary-button"
                      onClick={salvarDesfechoIntervencao}
                      disabled={salvandoDesfechoIntervencao}
                    >
                      {salvandoDesfechoIntervencao ? "Salvando..." : "Salvar desfecho"}
                    </button>
                  </div>
                </div>
              )}

              {mostrarFormularioIntervencao && (
                <div className="nested-form">
                  <select
                    className="input"
                    value={novaIntervencao.medicamento_uso_id}
                    onChange={(e) =>
                      setNovaIntervencao({
                        ...novaIntervencao,
                        medicamento_uso_id: e.target.value,
                      })
                    }
                  >
                    <option value="">Vincular a medicamento específico?</option>
                    {medicamentos.map((m) => (
                      <option key={m.id} value={m.id}>
                        {m.nome_medicamento}
                      </option>
                    ))}
                  </select>

                  <select
                    className="input"
                    value={novaIntervencao.tipo_intervencao}
                    onChange={(e) =>
                      setNovaIntervencao({
                        ...novaIntervencao,
                        tipo_intervencao: e.target.value,
                      })
                    }
                  >
                    <option value="">Tipo de intervenção</option>
                    <option value="Orientação farmacêutica">Orientação farmacêutica</option>
                    <option value="Ajuste de adesão">Ajuste de adesão</option>
                    <option value="Suspeita de RAM">Suspeita de RAM</option>
                    <option value="PRM/RNM">PRM/RNM</option>
                    <option value="Conciliação medicamentosa">Conciliação medicamentosa</option>
                    <option value="Encaminhamento">Encaminhamento</option>
                    <option value="Outro">Outro</option>
                  </select>

                  <textarea
                    className="textarea"
                    placeholder="Descrição da intervenção"
                    value={novaIntervencao.descricao}
                    onChange={(e) =>
                      setNovaIntervencao({
                        ...novaIntervencao,
                        descricao: e.target.value,
                      })
                    }
                  />

                  <textarea
                    className="textarea"
                    placeholder="Conduta adotada"
                    value={novaIntervencao.conduta}
                    onChange={(e) =>
                      setNovaIntervencao({
                        ...novaIntervencao,
                        conduta: e.target.value,
                      })
                    }
                  />

                  <label className="checkbox-line">
                    <input
                      type="checkbox"
                      checked={novaIntervencao.aceita_pelo_paciente}
                      onChange={(e) =>
                        setNovaIntervencao({
                          ...novaIntervencao,
                          aceita_pelo_paciente: e.target.checked,
                        })
                      }
                    />
                    Intervenção aceita pelo paciente
                  </label>

                  <label className="checkbox-line">
                    <input
                      type="checkbox"
                      checked={novaIntervencao.necessidade_encaminhamento}
                      onChange={(e) =>
                        setNovaIntervencao({
                          ...novaIntervencao,
                          necessidade_encaminhamento: e.target.checked,
                        })
                      }
                    />
                    Necessidade de encaminhamento
                  </label>

                  <textarea
                    className="textarea"
                    placeholder="Observações"
                    value={novaIntervencao.observacoes}
                    onChange={(e) =>
                      setNovaIntervencao({
                        ...novaIntervencao,
                        observacoes: e.target.value,
                      })
                    }
                  />

                  <button
                    className="primary-button"
                    onClick={salvarIntervencaoFarmacoterapia}
                    disabled={salvandoIntervencao}
                  >
                    {salvandoIntervencao ? "Salvando..." : "Salvar intervenção"}
                  </button>
                </div>
              )}
            </div>
            )}

            {abaProntuario === "metas" && (
              <div className="prontuario-tab-content">
                <div className="form-card">
                  <div className="section-header-row">
                    <div>
                      <h3>Metas terapêuticas e ações de acompanhamento</h3>
                      <p className="muted">Use esta aba como plano operacional: meta é o resultado esperado; ação é a tarefa com responsável, prazo e status.</p>
                    </div>
                  </div>

                  <div className="clinical-summary">
                    <strong>Fluxo recomendado:</strong>
                    <p>
                      PRM identifica o problema; intervenção registra a conduta clínica; meta define o resultado a alcançar; ação do plano define quem fará, quando fará e como será acompanhado.
                    </p>
                  </div>

                  <div className="dashboard-grid">
                    <div className="form-card">
                      <div className="section-header-row">
                        <div>
                          <h4>Metas terapêuticas</h4>
                          <p className="muted">Registre metas vinculadas a PRM, intervenções e acompanhamento clínico.</p>
                        </div>
                        {podeRegistrarClinico() && (
                          <button className="secondary-button" onClick={abrirNovaMeta}>
                            Nova meta
                          </button>
                        )}
                      </div>

                      {mostrarFormularioMeta && (
                        <div className="inline-form">
                          <div className="form-grid two">
                            <label>
                              Categoria
                              <select
                                value={novaMeta.categoria}
                                onChange={(e) => {
                                  const categoria = e.target.value;
                                  const primeiraSubcategoria = opcoesMetas.subcategorias?.[categoria]?.[0] || "OUTRA";
                                  setNovaMeta({ ...novaMeta, categoria, subcategoria: primeiraSubcategoria });
                                }}
                              >
                                {(opcoesMetas.categorias || []).map((cat) => (
                                  <option key={cat} value={cat}>{traduzirStatus(cat)}</option>
                                ))}
                              </select>
                            </label>

                            <label>
                              Subcategoria
                              <select
                                value={novaMeta.subcategoria}
                                onChange={(e) => setNovaMeta({ ...novaMeta, subcategoria: e.target.value })}
                              >
                                {subcategoriasMetaAtual.map((sub) => (
                                  <option key={sub} value={sub}>{traduzirStatus(sub)}</option>
                                ))}
                              </select>
                            </label>
                          </div>

                          <label>
                            Descrição clínica da meta
                            <textarea
                              className="textarea"
                              placeholder="Ex.: Reduzir PA para meta individualizada em até 90 dias"
                              value={novaMeta.descricao}
                              onChange={(e) => setNovaMeta({ ...novaMeta, descricao: e.target.value })}
                            />
                          </label>

                          <div className="form-grid three">
                            <label>
                              Valor atual
                              <input
                                value={novaMeta.valor_atual}
                                onChange={(e) => setNovaMeta({ ...novaMeta, valor_atual: e.target.value })}
                                placeholder="Ex.: 150/90"
                              />
                            </label>
                            <label>
                              Valor alvo
                              <input
                                value={novaMeta.valor_alvo}
                                onChange={(e) => setNovaMeta({ ...novaMeta, valor_alvo: e.target.value })}
                                placeholder="Ex.: 130/80"
                              />
                            </label>
                            <label>
                              Unidade
                              <select
                                value={novaMeta.unidade}
                                onChange={(e) => setNovaMeta({ ...novaMeta, unidade: e.target.value })}
                              >
                                <option value="">Selecionar</option>
                                {(opcoesMetas.unidades || []).map((unidade) => (
                                  <option key={unidade} value={unidade}>{unidade}</option>
                                ))}
                              </select>
                            </label>
                          </div>

                          <div className="form-grid three">
                            <label>
                              Data inicial
                              <input
                                type="date"
                                value={novaMeta.data_inicial}
                                onChange={(e) => setNovaMeta({ ...novaMeta, data_inicial: e.target.value })}
                              />
                            </label>
                            <label>
                              Prazo previsto
                              <input
                                type="date"
                                value={novaMeta.data_prevista}
                                onChange={(e) => setNovaMeta({ ...novaMeta, data_prevista: e.target.value })}
                              />
                            </label>
                            <label>
                              Data de conclusão
                              <input
                                type="date"
                                value={novaMeta.data_conclusao}
                                onChange={(e) => setNovaMeta({ ...novaMeta, data_conclusao: e.target.value })}
                              />
                            </label>
                          </div>

                          <div className="form-grid two">
                            <label>
                              Status
                              <select
                                value={novaMeta.status}
                                onChange={(e) => setNovaMeta({ ...novaMeta, status: e.target.value })}
                              >
                                {(opcoesMetas.status || []).map((status) => (
                                  <option key={status} value={status}>{traduzirStatus(status)}</option>
                                ))}
                              </select>
                            </label>

                            <label>
                              Origem
                              <select
                                value={novaMeta.origem}
                                onChange={(e) => setNovaMeta({ ...novaMeta, origem: e.target.value })}
                              >
                                {(opcoesMetas.origens || []).map((origem) => (
                                  <option key={origem} value={origem}>{traduzirStatus(origem)}</option>
                                ))}
                              </select>
                            </label>
                          </div>

                          <div className="form-grid two">
                            <label>
                              Vincular a PRM
                              <select
                                value={novaMeta.prm_id}
                                onChange={(e) => setNovaMeta({ ...novaMeta, prm_id: e.target.value })}
                              >
                                <option value="">Não vincular</option>
                                {problemasFarmacoterapeuticos.map((p) => (
                                  <option key={p.id} value={p.id}>
                                    #{p.id} · {traduzirStatus(p.categoria || p.tipo_problema || "PRM")} · {p.descricao || p.problema || "sem descrição"}
                                  </option>
                                ))}
                              </select>
                            </label>

                            <label>
                              Vincular a intervenção
                              <select
                                value={novaMeta.intervencao_farmacoterapia_id}
                                onChange={(e) => setNovaMeta({ ...novaMeta, intervencao_farmacoterapia_id: e.target.value })}
                              >
                                <option value="">Não vincular</option>
                                {intervencoesFarmacoterapia.map((i) => (
                                  <option key={i.id} value={i.id}>
                                    #{i.id} · {traduzirStatus(i.tipo_intervencao || "intervenção")} · {i.descricao || i.conduta || "sem descrição"}
                                  </option>
                                ))}
                              </select>
                            </label>
                          </div>

                          <div className="button-row">
                            <button
                              className="primary-button"
                              onClick={salvarMetaTerapeutica}
                              disabled={salvandoMeta}
                            >
                              {salvandoMeta ? "Salvando..." : metaEditandoId ? "Atualizar meta" : "Salvar meta"}
                            </button>
                            <button
                              className="secondary-button"
                              onClick={() => {
                                resetarFormularioMeta();
                                setMostrarFormularioMeta(false);
                              }}
                              disabled={salvandoMeta}
                            >
                              Cancelar
                            </button>
                          </div>
                        </div>
                      )}

                      {metasTerapeuticas.length === 0 ? (
                        <p className="muted">Nenhuma meta terapêutica estruturada registrada.</p>
                      ) : (
                        <div className="med-list compact">
                          {metasTerapeuticas.map((m) => (
                            <div className="med-card" key={`meta-${m.id}`}>
                              <div className="section-header-row">
                                <div>
                                  <strong>{traduzirStatus(m.subcategoria || m.parametro || m.categoria)}</strong>
                                  <p>{m.descricao}</p>
                                  <p className="muted">
                                    Categoria: {traduzirStatus(m.categoria)} · Alvo: {m.valor_alvo || "—"} {m.unidade || ""} · Status: {traduzirStatus(m.status)}
                                  </p>
                                  {(m.data_prevista || m.prazo) && <p className="muted">Prazo: {String(m.data_prevista || m.prazo).slice(0, 10)}</p>}
                                </div>
                                {podeRegistrarClinico() && (
                                  <button className="secondary-button" onClick={() => iniciarEdicaoMeta(m)}>Editar</button>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    <div className="form-card">
                      <div className="section-header-row">
                        <div>
                          <h4>Ações do plano</h4>
                          <p className="muted">Transforme metas e intervenções em tarefas acompanháveis, com responsável, prazo e status.</p>
                        </div>
                        {podeRegistrarClinico() && (
                          <button className="secondary-button" onClick={abrirNovaAcaoPlano}>
                            Nova ação
                          </button>
                        )}
                      </div>

                      {mostrarFormularioAcao && (
                        <div className="nested-form">
                          <div className="form-grid three">
                            <label>
                              Tipo da ação
                              <select
                                value={novaAcaoPlano.tipo_acao}
                                onChange={(e) => setNovaAcaoPlano({ ...novaAcaoPlano, tipo_acao: e.target.value })}
                              >
                                {(opcoesPlanoCuidado.tipos_acao || []).map((tipo) => (
                                  <option key={tipo} value={tipo}>{traduzirStatus(tipo)}</option>
                                ))}
                              </select>
                            </label>

                            <label>
                              Responsável
                              <select
                                value={novaAcaoPlano.responsavel}
                                onChange={(e) => setNovaAcaoPlano({ ...novaAcaoPlano, responsavel: e.target.value })}
                              >
                                {(opcoesPlanoCuidado.responsaveis || []).map((resp) => (
                                  <option key={resp} value={resp}>{traduzirStatus(resp)}</option>
                                ))}
                              </select>
                            </label>

                            <label>
                              Prazo
                              <input
                                type="date"
                                value={novaAcaoPlano.prazo}
                                onChange={(e) => setNovaAcaoPlano({ ...novaAcaoPlano, prazo: e.target.value })}
                              />
                            </label>

                            <label>
                              Prioridade
                              <select
                                value={novaAcaoPlano.prioridade}
                                onChange={(e) => setNovaAcaoPlano({ ...novaAcaoPlano, prioridade: e.target.value })}
                              >
                                {(opcoesPlanoCuidado.prioridades || []).map((p) => (
                                  <option key={p} value={p}>{traduzirStatus(p)}</option>
                                ))}
                              </select>
                            </label>

                            <label>
                              Status
                              <select
                                value={novaAcaoPlano.status}
                                onChange={(e) => setNovaAcaoPlano({ ...novaAcaoPlano, status: e.target.value })}
                              >
                                {(opcoesPlanoCuidado.status_acao || []).map((status) => (
                                  <option key={status} value={status}>{traduzirStatus(status)}</option>
                                ))}
                              </select>
                            </label>

                            <label>
                              Vincular a PRM
                              <select
                                value={novaAcaoPlano.problema_id}
                                onChange={(e) => setNovaAcaoPlano({ ...novaAcaoPlano, problema_id: e.target.value })}
                              >
                                <option value="">Não vincular</option>
                                {problemasFarmacoterapeuticos.map((p) => (
                                  <option key={p.id} value={p.id}>
                                    #{p.id} · {traduzirStatus(p.categoria)} · {traduzirStatus(p.tipo)}
                                  </option>
                                ))}
                              </select>
                            </label>

                            <label>
                              Vincular a meta
                              <select
                                value={novaAcaoPlano.meta_id}
                                onChange={(e) => setNovaAcaoPlano({ ...novaAcaoPlano, meta_id: e.target.value })}
                              >
                                <option value="">Não vincular</option>
                                {metasTerapeuticas.map((m) => (
                                  <option key={m.id} value={m.id}>
                                    #{m.id} · {traduzirStatus(m.subcategoria || m.parametro || m.categoria)}
                                  </option>
                                ))}
                              </select>
                            </label>

                            <label>
                              Vincular a intervenção
                              <select
                                value={novaAcaoPlano.intervencao_farmacoterapia_id}
                                onChange={(e) => setNovaAcaoPlano({ ...novaAcaoPlano, intervencao_farmacoterapia_id: e.target.value })}
                              >
                                <option value="">Não vincular</option>
                                {intervencoesFarmacoterapia.map((i) => (
                                  <option key={i.id} value={i.id}>
                                    #{i.id} · {traduzirStatus(i.tipo_intervencao || "intervenção")}
                                  </option>
                                ))}
                              </select>
                            </label>
                          </div>

                          <label>
                            Descrição da ação
                            <textarea
                              rows={3}
                              value={novaAcaoPlano.descricao}
                              onChange={(e) => setNovaAcaoPlano({ ...novaAcaoPlano, descricao: e.target.value })}
                              placeholder="Ex.: orientar técnica inalatória e reavaliar adesão em 30 dias"
                            />
                          </label>

                          <label>
                            Resultado/observação da ação
                            <textarea
                              rows={2}
                              value={novaAcaoPlano.resultado}
                              onChange={(e) => setNovaAcaoPlano({ ...novaAcaoPlano, resultado: e.target.value })}
                              placeholder="Preencher ao acompanhar ou concluir a ação"
                            />
                          </label>

                          <div className="button-row">
                            <button className="primary-button" onClick={salvarAcaoPlanoCuidado} disabled={salvandoAcao}>
                              {salvandoAcao ? "Salvando..." : acaoEditandoId ? "Atualizar ação" : "Salvar ação"}
                            </button>
                            <button
                              className="secondary-button"
                              onClick={() => {
                                resetarFormularioAcaoPlano();
                                setMostrarFormularioAcao(false);
                              }}
                              disabled={salvandoAcao}
                            >
                              Cancelar
                            </button>
                          </div>
                        </div>
                      )}

                      {acoesPlanoCuidado.length === 0 ? (
                        <p className="muted">Nenhuma ação estruturada registrada.</p>
                      ) : (
                        <div className="med-list compact">
                          {acoesPlanoCuidado.map((a) => (
                            <div className="med-card" key={`acao-${a.id}`}>
                              <div className="section-header-row">
                                <div>
                                  <strong>{traduzirStatus(a.tipo_acao)}</strong>
                                  <p>{a.descricao}</p>
                                  <p className="muted">Responsável: {traduzirStatus(a.responsavel || "NAO_INFORMADO")} · Prioridade: {traduzirStatus(a.prioridade || "NORMAL")} · Status: {traduzirStatus(a.status)}</p>
                                  {a.prazo && <p className="muted">Prazo: {String(a.prazo).slice(0, 10)}</p>}
                                  {a.resultado && <p className="muted">Resultado: {a.resultado}</p>}
                                </div>
                                {podeRegistrarClinico() && (
                                  <button className="secondary-button" onClick={() => iniciarEdicaoAcaoPlano(a)}>Atualizar</button>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {abaProntuario === "plano" && (
              <div className="prontuario-tab-content">
                <div className="form-card">
                  <div className="section-header">
                    <div>
                      <h3>Plano narrativo do cuidado</h3>
                      <p className="muted">
                        Use esta aba para uma síntese clínica complementar. O plano operacional estruturado deve ser registrado em “Metas e ações”.
                      </p>
                    </div>

                    <div className="clinical-summary">
                      <strong>Relação com as etapas anteriores</strong>
                      <p>
                        O plano narrativo deve sintetizar o raciocínio clínico construído nas etapas anteriores,
                        sem substituir os registros estruturados de PRM, intervenções, metas e ações.
                      </p>
                      <div className="cards-grid four">
                        <button className="metric-card" onClick={() => setAbaProntuario("intervencoes")}>
                          <span>PRM / Intervenções</span>
                          <strong>{problemasFarmacoterapeuticos.length + intervencoesFarmacoterapia.length}</strong>
                        </button>
                        <button className="metric-card" onClick={() => setAbaProntuario("metas")}>
                          <span>Metas</span>
                          <strong>{metasTerapeuticas.length}</strong>
                        </button>
                        <button className="metric-card" onClick={() => setAbaProntuario("metas")}>
                          <span>Ações</span>
                          <strong>{acoesPlanoCuidado.length}</strong>
                        </button>
                        <button className="metric-card" onClick={() => setAbaProntuario("evolucoes")}>
                          <span>Evoluções</span>
                          <strong>{linhaTempoClinica.filter((evento) => ["evolucao_clinica", "evolucao", "desfecho_clinico", "desfecho"].includes(evento.tipo)).length}</strong>
                        </button>
                      </div>
                    </div>

                    {sugestoesPlano && (
                      <div className="form-card">
                        <h3>Sugestões para o Plano de Cuidado</h3>

                        <div className="cards-grid four">
                          <div
                            className={`metric-card ${
                              sugestoesPlano.prioridade === "alta"
                                ? "danger"
                                : sugestoesPlano.prioridade === "moderada"
                                ? "warning"
                                : "success"
                            }`}
                          >
                            <span>Prioridade</span>
                            <strong>{sugestoesPlano.prioridade}</strong>
                          </div>
                        </div>

                        <div className="dashboard-grid">
                          <div className="form-card">
                            <h4>Achados relevantes</h4>

                            <ul>
                              {sugestoesPlano.achados?.map((item, index) => (
                                <li key={index}>{item}</li>
                              ))}
                            </ul>
                          </div>

                          <div className="form-card">
                            <h4>Pontos para avaliação</h4>

                            <ul>
                              {sugestoesPlano.pontos_atencao?.map((item, index) => (
                                <li key={index}>{item}</li>
                              ))}
                            </ul>
                          </div>
                        </div>

                        <div className="clinical-summary">
                          <strong>Observação:</strong>

                          <p>{sugestoesPlano.observacao}</p>
                        </div>
                      </div>
                    )}
                    <button
                      className="primary-button"
                      onClick={() => {
                        setMostrarFormularioPlano(true);
                        setPlanoEditando(null);
                      }}
                    >
                      Novo plano
                    </button>
                  </div>

                  {mostrarFormularioPlano && (
                    <div className="form-card">
                      <h4>{planoEditando ? "Editar plano" : "Novo plano de cuidado"}</h4>

                      <label>Problema identificado</label>
                      <textarea
                        value={novoPlano.problema_identificado}
                        onChange={(e) =>
                          setNovoPlano({
                            ...novoPlano,
                            problema_identificado: e.target.value,
                          })
                        }
                      />

                      <label>Objetivo terapêutico</label>
                      <textarea
                        value={novoPlano.objetivo_terapeutico}
                        onChange={(e) =>
                          setNovoPlano({
                            ...novoPlano,
                            objetivo_terapeutico: e.target.value,
                          })
                        }
                      />

                      <label>Intervenções planejadas</label>
                      <textarea
                        value={novoPlano.intervencoes_planejadas}
                        onChange={(e) =>
                          setNovoPlano({
                            ...novoPlano,
                            intervencoes_planejadas: e.target.value,
                          })
                        }
                      />

                      <label>Prazo de reavaliação</label>
                      <input
                        type="date"
                        value={novoPlano.prazo_reavaliacao}
                        onChange={(e) =>
                          setNovoPlano({
                            ...novoPlano,
                            prazo_reavaliacao: e.target.value,
                          })
                        }
                      />

                      <label>Observações</label>
                      <textarea
                        value={novoPlano.observacoes}
                        onChange={(e) =>
                          setNovoPlano({
                            ...novoPlano,
                            observacoes: e.target.value,
                          })
                        }
                      />

                      <div className="form-actions">
                        <button
                          className="primary-button"
                          onClick={salvarPlanoCuidado}
                        >
                          Salvar plano
                        </button>

                        <button
                          className="secondary-button"
                          onClick={limparFormularioPlano}
                        >
                          Cancelar
                        </button>
                      </div>
                    </div>
                  )}

                  {planosCuidado.length === 0 ? (
                    <p className="muted">Nenhum plano de cuidado registrado.</p>
                  ) : (
                    <div className="dashboard-grid">
                      {planosCuidado.map((plano) => (
                        <div key={plano.id} className="form-card">
                          <div className="timeline-top">
                            <strong>{plano.problema_identificado}</strong>

                            <span className={`timeline-tag ${plano.status}`}>
                              {plano.status}
                            </span>
                          </div>

                          <p>
                            <strong>Objetivo:</strong>{" "}
                            {plano.objetivo_terapeutico || "Não informado"}
                          </p>

                          <p>
                            <strong>Intervenções planejadas:</strong>{" "}
                            {plano.intervencoes_planejadas || "Não informado"}
                          </p>

                          <p>
                            <strong>Prazo de reavaliação:</strong>{" "}
                            {plano.prazo_reavaliacao
                              ? new Date(plano.prazo_reavaliacao).toLocaleDateString("pt-BR")
                              : "Não informado"}
                          </p>

                          {plano.observacoes && (
                            <p>
                              <strong>Observações:</strong> {plano.observacoes}
                            </p>
                          )}

                          {plano.resultado && (
                            <p>
                              <strong>Resultado:</strong> {plano.resultado}
                            </p>
                          )}

                          {plano.resultado_classificacao && (
                            <p>
                              <strong>
                                Classificação:
                              </strong>{" "}
                              {plano.resultado_classificacao}
                            </p>
                          )}

                          <div className="form-actions">
                            {plano.status !== "concluido" && (
                              <>
                                <button
                                  className="secondary-button"
                                  onClick={() => editarPlanoCuidado(plano)}
                                >
                                  Editar
                                </button>

                                <button
                                  className="primary-button"
                                  onClick={() => concluirPlanoCuidado(plano)}
                                >
                                  Concluir
                                </button>
                              </>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {abaProntuario === "evolucoes" && (
              <div className="prontuario-tab-content">
                <div className="form-card">
                  <div className="section-header-row">
                    <div>
                      <h3>Evoluções clínicas</h3>
                      <p className="muted">
                        Registros de acompanhamento, condutas, planos e desfechos clínicos.
                      </p>
                    </div>

                    {podeRegistrarClinico() && (
                      <button
                        className="secondary-button"
                        onClick={() => setMostrarFormularioEvolucao(!mostrarFormularioEvolucao)}
                      >
                        {mostrarFormularioEvolucao ? "Cancelar evolução" : "Nova evolução clínica"}
                      </button>
                    )}
                  </div>

                  {linhaTempoClinica.filter((evento) =>
                    ["evolucao_clinica", "evolucao", "desfecho_clinico", "desfecho"].includes(evento.tipo)
                  ).length === 0 ? (
                    <p className="muted">Nenhuma evolução ou desfecho clínico registrado.</p>
                  ) : (
                    <div className="med-list">
                      {linhaTempoClinica
                        .filter((evento) =>
                          ["evolucao_clinica", "evolucao", "desfecho_clinico", "desfecho"].includes(evento.tipo)
                        )
                        .map((evento, index) => (
                          <div className="med-card" key={`${evento.tipo}-${evento.data || index}-${index}`}>
                            <div className="timeline-top">
                              <strong>{evento.titulo || traduzirTipoEvento(evento.tipo)}</strong>
                              <span>
                                {evento.data
                                  ? new Date(evento.data).toLocaleString("pt-BR")
                                  : "Sem data"}
                              </span>
                            </div>

                            <span className="timeline-tag">
                              {traduzirTipoEvento(evento.tipo)}
                            </span>

                            {evento.descricao && <p>{evento.descricao}</p>}

                            {evento.detalhes && (
                              <div className="clinical-timeline-details">
                                {Object.entries(evento.detalhes).map(([chave, valor]) =>
                                  valor ? (
                                    <div key={chave}>
                                      <strong>{chave}:</strong> 
                                      {typeof valor === "boolean" ? (valor ? "Sim" : "Não") : valor}
                                    </div>
                                  ) : null
                                )}
                              </div>
                            )}

                            {podeRegistrarClinico() &&
                              ["evolucao_clinica", "evolucao"].includes(evento.tipo) &&
                              evento.evolucao_id && (
                                <button
                                  className="mini-action-button"
                                  onClick={() => setEvolucaoParaDesfecho(evento)}
                                >
                                  Registrar desfecho
                                </button>
                              )}
                          </div>
                        ))}
                    </div>
                  )}
                </div>

                {mostrarFormularioEvolucao && (
              <div className="form-card">
                <h3>Nova evolução clínica</h3>

                <input
                  className="input"
                  placeholder="Tipo de atendimento"
                  value={novaEvolucao.tipo_atendimento}
                  onChange={(e) =>
                    setNovaEvolucao({
                      ...novaEvolucao,
                      tipo_atendimento: e.target.value,
                    })
                  }
                />

                <textarea
                  className="textarea"
                  placeholder="Queixa principal"
                  value={novaEvolucao.queixa_principal}
                  onChange={(e) =>
                    setNovaEvolucao({
                      ...novaEvolucao,
                      queixa_principal: e.target.value,
                    })
                  }
                />

                <textarea
                  className="textarea"
                  placeholder="História breve"
                  value={novaEvolucao.historia_breve}
                  onChange={(e) =>
                    setNovaEvolucao({
                      ...novaEvolucao,
                      historia_breve: e.target.value,
                    })
                  }
                />

                <textarea
                  className="textarea"
                  placeholder="Avaliação farmacêutica"
                  value={novaEvolucao.avaliacao_farmaceutica}
                  onChange={(e) =>
                    setNovaEvolucao({
                      ...novaEvolucao,
                      avaliacao_farmaceutica: e.target.value,
                    })
                  }
                />

                <textarea
                  className="textarea"
                  placeholder="Problemas identificados"
                  value={novaEvolucao.problemas_identificados}
                  onChange={(e) =>
                    setNovaEvolucao({
                      ...novaEvolucao,
                      problemas_identificados: e.target.value,
                    })
                  }
                />

                <textarea
                  className="textarea"
                  placeholder="Conduta"
                  value={novaEvolucao.conduta}
                  onChange={(e) =>
                    setNovaEvolucao({
                      ...novaEvolucao,
                      conduta: e.target.value,
                    })
                  }
                />

                <textarea
                  className="textarea"
                  placeholder="Orientações realizadas"
                  value={novaEvolucao.orientacoes_realizadas}
                  onChange={(e) =>
                    setNovaEvolucao({
                      ...novaEvolucao,
                      orientacoes_realizadas: e.target.value,
                    })
                  }
                />

                <textarea
                  className="textarea"
                  placeholder="Plano de acompanhamento"
                  value={novaEvolucao.plano_acompanhamento}
                  onChange={(e) =>
                    setNovaEvolucao({
                      ...novaEvolucao,
                      plano_acompanhamento: e.target.value,
                    })
                  }
                />

                <label className="checkbox-line">
                  <input
                    type="checkbox"
                    checked={novaEvolucao.necessidade_retorno}
                    onChange={(e) =>
                      setNovaEvolucao({
                        ...novaEvolucao,
                        necessidade_retorno: e.target.checked,
                      })
                    }
                  />
                  Necessita retorno
                </label>

                {novaEvolucao.necessidade_retorno && (
                  <input
                    className="input"
                    type="date"
                    value={novaEvolucao.data_retorno_sugerida}
                    onChange={(e) =>
                      setNovaEvolucao({
                        ...novaEvolucao,
                        data_retorno_sugerida: e.target.value,
                      })
                    }
                  />
                )}

                <textarea
                  className="textarea"
                  placeholder="Observações"
                  value={novaEvolucao.observacoes}
                  onChange={(e) =>
                    setNovaEvolucao({
                      ...novaEvolucao,
                      observacoes: e.target.value,
                    })
                  }
                />

                <button
                  className="primary-button"
                  onClick={salvarEvolucao}
                  disabled={salvandoEvolucao}
                >
                  {salvandoEvolucao ? "Salvando..." : "Salvar evolução"}
                </button>
              </div>
            )}

                        

                {evolucaoParaDesfecho && (
              <div className="form-card">
                <h3>Registrar desfecho clínico</h3>

                <p className="muted">
                  Evolução selecionada: {evolucaoParaDesfecho.titulo}
                </p>

                <select
                  className="input"
                  value={novoDesfecho.melhora_clinica}
                  onChange={(e) =>
                    setNovoDesfecho({
                      ...novoDesfecho,
                      melhora_clinica: e.target.value,
                    })
                  }
                >
                  <option value="sim">Melhora clínica: sim</option>
                  <option value="parcial">Melhora clínica: parcial</option>
                  <option value="nao">Melhora clínica: não</option>
                </select>

                <select
                  className="input"
                  value={novoDesfecho.adesao_tratamento}
                  onChange={(e) =>
                    setNovoDesfecho({
                      ...novoDesfecho,
                      adesao_tratamento: e.target.value,
                    })
                  }
                >
                  <option value="boa">Adesão boa</option>
                  <option value="regular">Adesão regular</option>
                  <option value="ruim">Adesão ruim</option>
                  <option value="nao_avaliada">Não avaliada</option>
                </select>

                <label className="checkbox-line">
                  <input
                    type="checkbox"
                    checked={novoDesfecho.resolucao_problema}
                    onChange={(e) =>
                      setNovoDesfecho({
                        ...novoDesfecho,
                        resolucao_problema: e.target.checked,
                      })
                    }
                  />
                  Problema resolvido
                </label>

                <label className="checkbox-line">
                  <input
                    type="checkbox"
                    checked={novoDesfecho.necessidade_encaminhamento}
                    onChange={(e) =>
                      setNovoDesfecho({
                        ...novoDesfecho,
                        necessidade_encaminhamento: e.target.checked,
                      })
                    }
                  />
                  Necessitou encaminhamento
                </label>

                {novoDesfecho.necessidade_encaminhamento && (
                  <input
                    className="input"
                    placeholder="Encaminhamento realizado"
                    value={novoDesfecho.encaminhamento_realizado}
                    onChange={(e) =>
                      setNovoDesfecho({
                        ...novoDesfecho,
                        encaminhamento_realizado: e.target.value,
                      })
                    }
                  />
                )}

                <textarea
                  className="textarea"
                  placeholder="Resultado observado"
                  value={novoDesfecho.resultado_observado}
                  onChange={(e) =>
                    setNovoDesfecho({
                      ...novoDesfecho,
                      resultado_observado: e.target.value,
                    })
                  }
                />

                <textarea
                  className="textarea"
                  placeholder="Observações"
                  value={novoDesfecho.observacoes}
                  onChange={(e) =>
                    setNovoDesfecho({
                      ...novoDesfecho,
                      observacoes: e.target.value,
                    })
                  }
                />

                <div className="form-actions">
                  <button
                    className="secondary-button"
                    onClick={() => setEvolucaoParaDesfecho(null)}
                  >
                    Cancelar
                  </button>

                  <button
                    className="primary-button"
                    onClick={salvarDesfecho}
                    disabled={salvandoDesfecho}
                  >
                    {salvandoDesfecho ? "Salvando..." : "Salvar desfecho"}
                  </button>
                </div>
              </div>
            )}

              </div>
            )}

            {abaProntuario === "timeline" && (
              <div className="prontuario-tab-content">
                <div className="form-card">
                  <div className="section-header-row">
                    <div>
                      <h3>Timeline única do cuidado</h3>
                      <p className="muted">
                        Jornada longitudinal do paciente reunindo CEAF, agenda, documentos, OCR, consultório, PRM, intervenções, metas, plano e desfechos.
                      </p>
                    </div>
                  </div>

                  {categoriasTimelineUnificada.length > 0 && (
                    <div className="timeline-summary-grid">
                      {categoriasTimelineUnificada.map(([categoria, total]) => (
                        <div className="timeline-summary-card" key={categoria}>
                          <span>{traduzirTipoEvento(categoria)}</span>
                          <strong>{total}</strong>
                        </div>
                      ))}
                    </div>
                  )}

                  {linhaTempoClinica.length === 0 ? (
                    <p className="muted">Nenhum evento clínico registrado.</p>
                  ) : (
                    <div className="clinical-timeline">
                      {linhaTempoClinica.map((evento, index) => (
                        <div
                          className={`clinical-timeline-item ${evento.categoria || evento.tipo}`}
                          key={`${evento.tipo}-${evento.data || index}-${index}`}
                        >
                          <div className="clinical-timeline-marker" />

                          <div className="clinical-timeline-content">
                            <div className="clinical-timeline-top">
                              <strong>{evento.titulo || "Evento clínico"}</strong>

                              <span>
                                {evento.data
                                  ? new Date(evento.data).toLocaleString("pt-BR")
                                  : "Sem data"}
                              </span>
                            </div>

                            <div className="clinical-timeline-icon">
                              {iconeTimeline(evento)}
                            </div>

                            <span className="clinical-timeline-type">
                              {traduzirTipoEvento(evento.categoria || evento.tipo)} · {traduzirTipoEvento(evento.tipo)}
                            </span>

                            {evento.descricao && <p>{evento.descricao}</p>}

                            {evento.detalhes && (
                              <div className="clinical-timeline-details">
                                {Object.entries(evento.detalhes).map(([chave, valor]) =>
                                  valor ? (
                                    <div key={chave}>
                                      <strong>{chave}:</strong>{" "}
                                      {typeof valor === "boolean" ? (valor ? "Sim" : "Não") : valor}
                                    </div>
                                  ) : null
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}


          </>
        )}
      </div>
    );
  }

  return (
    <div>
      <h2>Consultório Farmacêutico</h2>

      <p className="muted">
        Centro de Atenção, pacientes clínicos, farmacoterapia, PRM, intervenções, metas, plano de cuidado e timeline em um único workspace.
      </p>

      <div className="tabs">
        <button
          className={abaConsultorio === "centro" ? "active" : ""}
          onClick={() => setAbaConsultorio("centro")}
        >
          Centro de Atenção
        </button>
        <button
          className={abaConsultorio === "pacientes" ? "active" : ""}
          onClick={() => setAbaConsultorio("pacientes")}
        >
          Pacientes e Prontuários
        </button>
      </div>

      {abaConsultorio === "centro" && <CuidadoFarmaceutico />}

      {abaConsultorio === "pacientes" && (
        <div className="table-card">
          <div className="section-header">
            <div>
              <h3>Pacientes e Prontuários</h3>
              <p className="muted">
                Busque diretamente por nome, CPF, CNS ou telefone para abrir o prontuário. A lista completa não é carregada automaticamente para manter a tela mais rápida.
              </p>
            </div>
          </div>

          <div className="filters-row">
            <label className="full-width-label">
              Buscar paciente
              <input
                value={buscaPacienteProntuario}
                onChange={(e) => setBuscaPacienteProntuario(e.target.value)}
                placeholder="Digite nome, CPF, CNS ou telefone"
              />
            </label>

            <div className="action-buttons">
              <button
                className="primary-button"
                onClick={() => buscarPacientesProntuario()}
                disabled={loading || buscaPacienteProntuario.trim().length < 3}
              >
                Buscar
              </button>
              <button
                className="secondary-button"
                onClick={() => {
                  setBuscaPacienteProntuario("");
                  setPacientes([]);
                  setBuscaPacientesRealizada(false);
                }}
              >
                Limpar
              </button>
            </div>
          </div>

          {loading ? (
            <p className="muted">Buscando pacientes...</p>
          ) : buscaPacienteProntuario.trim().length < 3 ? (
            <p className="muted table-empty">Digite pelo menos 3 caracteres para iniciar a busca.</p>
          ) : pacientes.length === 0 && buscaPacientesRealizada ? (
            <p className="muted table-empty">Nenhum paciente encontrado para o termo informado.</p>
          ) : pacientes.length > 0 ? (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Nome</th>
                  <th>CPF</th>
                  <th>CNS</th>
                  <th>Telefone</th>
                  <th>Bairro</th>
                  <th>Origem</th>
                  <th>Ação</th>
                </tr>
              </thead>

              <tbody>
                {pacientes.map((p) => (
                  <tr key={p.id}>
                    <td>{p.nome}</td>
                    <td>{p.cpf || "—"}</td>
                    <td>{p.cns || "—"}</td>
                    <td>{p.telefone || "—"}</td>
                    <td>{p.bairro || "—"}</td>
                    <td>{p.origem || "—"}</td>
                    <td>
                      <button className="primary-button" onClick={() => abrirProntuario(p)}>
                        Abrir prontuário
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : null}
        </div>
      )}
    </div>
  );
}
