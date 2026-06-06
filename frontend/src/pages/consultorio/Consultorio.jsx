import { useEffect, useState } from "react";
import { api } from "../../api/api";
import { ArrowLeft, UserRound } from "lucide-react";

export default function Consultorio({ usuario }) {
  const [pacientes, setPacientes] = useState([]);
  const [pacienteSelecionado, setPacienteSelecionado] = useState(null);
  const [detalhe, setDetalhe] = useState(null);

  const [loading, setLoading] = useState(true);
  const [loadingProntuario, setLoadingProntuario] = useState(false);

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
    nome_medicamento: "",
    dose: "",
    via: "",
    frequencia: "",
    indicacao: "",
    uso_continuo: true,
    adesao_referida: "",
    observacoes: "",
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
  const [abaProntuario, setAbaProntuario] = useState("identificacao");

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

  useEffect(() => {
    carregarPacientes();
  }, []);

  function podeRegistrarClinico() {
    if (!usuario) return false;
    if (usuario.perfil === "admin") return true;
    return ["Farmacêutico", "Docente"].includes(usuario.categoria_profissional);
  }

  function traduzirTipoEvento(tipo) {
    const mapa = {
      evolucao_clinica: "Evolução clínica",
      intervencao_farmacoterapeutica: "Intervenção farmacoterapêutica",
      desfecho_clinico: "Desfecho clínico",
      farmacoterapia: "Farmacoterapia",
    };

    return mapa[tipo] || tipo;
  }

  async function carregarPacientes() {
    try {
      setLoading(true);
      const response = await api.get("/consultorio/pacientes-clinicos");
      setPacientes(response.data.pacientes || []);
    } catch (error) {
      console.error("Erro ao carregar pacientes:", error.response?.data || error);
      alert("Erro ao carregar pacientes.");
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
      setAbaProntuario("identificacao");

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

      await carregarAvaliacaoPolifarmacia(paciente.id);

      await carregarPlanosCuidado(paciente.id);

      await carregarSugestoesPlano(paciente.id);

      await carregarEvolucaoFarmacoterapeutica(paciente.id);    } catch (error) {
      console.error("Erro ao abrir prontuário:", error.response?.data || error);
      alert("Erro ao abrir prontuário.");
    } finally {
      setLoadingProntuario(false);
    }
  }

  function voltarLista() {
    setPacienteSelecionado(null);
    setDetalhe(null);
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
    setAbaProntuario("identificacao");
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

    if (!novoMedicamento.nome_medicamento.trim()) {
      alert("Informe o nome do medicamento.");
      return;
    }

    try {
      setSalvandoMedicamento(true);

      await api.post(
        `/consultorio/paciente-clinico/${pacienteSelecionado.id}/medicamento`,
        novoMedicamento
      );

      setNovoMedicamento({
        nome_medicamento: "",
        dose: "",
        via: "",
        frequencia: "",
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
            Exportar PDF
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
            <div className="cards-grid two">
              <div className="metric-card">
                <span>Prontuário</span>
                <strong>{detalhe?.prontuario?.status || "—"}</strong>
                <p>ID: {detalhe?.prontuario?.id || "Não localizado"}</p>
              </div>

              <div className="metric-card">
                <span>Eventos na timeline</span>
                <strong>{linhaTempoClinica.length}</strong>
                <p>Histórico longitudinal do paciente</p>
              </div>
            </div>

            <div className="prontuario-tabs">
              <button
                type="button"
                className={abaProntuario === "identificacao" ? "active" : ""}
                onClick={() => setAbaProntuario("identificacao")}
              >
                Identificação
              </button>

              <button
                type="button"
                className={abaProntuario === "perfil" ? "active" : ""}
                onClick={() => setAbaProntuario("perfil")}
              >
                Perfil clínico
              </button>

              <button
                type="button"
                className={abaProntuario === "farmacoterapia" ? "active" : ""}
                onClick={() => setAbaProntuario("farmacoterapia")}
              >
                Farmacoterapia
              </button>

              <button
                type="button"
                className={abaProntuario === "intervencoes" ? "active" : ""}
                onClick={() => setAbaProntuario("intervencoes")}
              >
                Intervenções
              </button>

              <button
                type="button"
                className={abaProntuario === "evolucoes" ? "active" : ""}
                onClick={() => setAbaProntuario("evolucoes")}
              >
                Evoluções
              </button>

              <button
                className={abaProntuario === "plano" ? "active" : ""}
                onClick={() => setAbaProntuario("plano")}
              >
                Plano de cuidado
              </button>

              <button
                type="button"
                className={abaProntuario === "timeline" ? "active" : ""}
                onClick={() => setAbaProntuario("timeline")}
              >
                Linha do tempo
              </button>
            </div>

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
                        {m.frequencia || "Frequência não informada"}
                      </p>
                      <p className="muted">
                        Indicação: {m.indicacao || "não informada"} · Adesão:{" "}
                        {m.adesao_referida || "não informada"}
                      </p>
                      {m.observacoes && <p className="muted">Observações: {m.observacoes}</p>}
                    </div>
                  ))}
                </div>
              )}

              {mostrarFormularioMedicamento && (
                <div className="nested-form">
                  <input
                    className="input"
                    placeholder="Nome do medicamento"
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

                    <input
                      className="input"
                      placeholder="Via"
                      value={novoMedicamento.via}
                      onChange={(e) =>
                        setNovoMedicamento({
                          ...novoMedicamento,
                          via: e.target.value,
                        })
                      }
                    />
                  </div>

                  <input
                    className="input"
                    placeholder="Frequência"
                    value={novoMedicamento.frequencia}
                    onChange={(e) =>
                      setNovoMedicamento({
                        ...novoMedicamento,
                        frequencia: e.target.value,
                      })
                    }
                  />

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

            {abaProntuario === "plano" && (
              <div className="prontuario-tab-content">
                <div className="form-card">
                  <div className="section-header">
                    <div>
                      <h3>Plano de cuidado farmacêutico</h3>
                      <p className="muted">
                        Registre objetivos, intervenções planejadas, prazos e resultados do acompanhamento.
                      </p>
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
                      <h3>Linha do tempo clínica</h3>
                      <p className="muted">
                        Registro cronológico das evoluções, intervenções, desfechos e farmacoterapia.
                      </p>
                    </div>
                  </div>

                  {linhaTempoClinica.length === 0 ? (
                    <p className="muted">Nenhum evento clínico registrado.</p>
                  ) : (
                    <div className="clinical-timeline">
                      {linhaTempoClinica.map((evento, index) => (
                        <div
                          className={`clinical-timeline-item ${evento.tipo}`}
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
                              {["evolucao_clinica", "evolucao"].includes(evento.tipo) && "🩺"}
                              {["intervencao_farmacoterapeutica", "intervencao"].includes(evento.tipo) && "💊"}
                              {["desfecho_clinico", "desfecho", "desfecho_intervencao"].includes(evento.tipo) && "📈"}
                              {["farmacoterapia", "medicamento"].includes(evento.tipo) && "📋"}
                            </div>

                            <span className="clinical-timeline-type">
                              {traduzirTipoEvento(evento.tipo)}
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
        Pacientes clínicos, prontuário, evolução, desfechos, farmacoterapia e timeline.
      </p>

      {loading ? (
        <p>Carregando pacientes...</p>
      ) : (
        <div className="table-card">
          <table className="data-table">
            <thead>
              <tr>
                <th>Nome</th>
                <th>Idade</th>
                <th>Sexo</th>
                <th>Bairro</th>
                <th>Ação</th>
              </tr>
            </thead>

            <tbody>
              {pacientes.map((p) => (
                <tr key={p.id}>
                  <td>{p.nome}</td>
                  <td>{p.idade || "—"}</td>
                  <td>{p.sexo || "—"}</td>
                  <td>{p.bairro || "—"}</td>
                  <td>
                    <button className="primary-button" onClick={() => abrirProntuario(p)}>
                      Abrir prontuário
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {pacientes.length === 0 && (
            <p className="muted table-empty">Nenhum paciente encontrado.</p>
          )}
        </div>
      )}
    </div>
  );
}