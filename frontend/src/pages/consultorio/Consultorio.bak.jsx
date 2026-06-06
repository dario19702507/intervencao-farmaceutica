import { useEffect, useState } from "react";
import { api } from "../../api/api";
import { ArrowLeft, Clock, UserRound } from "lucide-react";

export default function Consultorio({ usuario }) {
  const [pacientes, setPacientes] = useState([]);
  const [pacienteSelecionado, setPacienteSelecionado] = useState(null);
  const [detalhe, setDetalhe] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingProntuario, setLoadingProntuario] = useState(false);
  const [mostrarFormularioEvolucao, setMostrarFormularioEvolucao] = useState(false);
  const [salvandoEvolucao, setSalvandoEvolucao] = useState(false);

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

  useEffect(() => {
    carregarPacientes();
  }, []);

  async function carregarPacientes() {
    try {
      setLoading(true);
      const response = await api.get("/consultorio/pacientes-clinicos");
      setPacientes(response.data.pacientes || []);
    } catch (error) {
      console.error("Erro ao carregar pacientes:", error);
    } finally {
      setLoading(false);
    }
  }

  async function abrirProntuario(paciente) {
    try {
      setLoadingProntuario(true);
      setPacienteSelecionado(paciente);

      const detalheResponse = await api.get(
        `/consultorio/paciente-clinico/${paciente.id}`
      );

      const timelineResponse = await api.get(
        `/consultorio/paciente-clinico/${paciente.id}/timeline`
      );

      setDetalhe(detalheResponse.data);
      setTimeline(timelineResponse.data.timeline || []);
    } catch (error) {
      console.error("Erro ao abrir prontuário:", error);
    } finally {
      setLoadingProntuario(false);
    }
  }

  function voltarLista() {
    setPacienteSelecionado(null);
    setDetalhe(null);
    setTimeline([]);
    setMostrarFormularioEvolucao(false);
  }

  function podeRegistrarClinico() {
    if (!usuario) return false;
    if (usuario.perfil === "admin") return true;

    return ["Farmacêutico", "Docente"].includes(
      usuario.categoria_profissional
    );
  }

  async function salvarEvolucao() {
    if (!detalhe?.prontuario?.id) {
      alert("Prontuário não localizado.");
      return;
    }

    try {
      setSalvandoEvolucao(true);

      const dados = {
        ...novaEvolucao,
        data_retorno_sugerida: novaEvolucao.data_retorno_sugerida || null,
      };

      await api.post(
        `/consultorio/prontuario/${detalhe.prontuario.id}/evolucao`,
        dados
      );

      alert("Evolução clínica registrada com sucesso.");

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

      const timelineResponse = await api.get(
        `/consultorio/paciente-clinico/${pacienteSelecionado.id}/timeline`
      );

      setTimeline(timelineResponse.data.timeline || []);
    } catch (error) {
      console.error("Erro ao salvar evolução:", error);
      alert("Erro ao salvar evolução clínica.");
    } finally {
      setSalvandoEvolucao(false);
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

          {podeRegistrarClinico() && (
            <button
              className="primary-button"
              onClick={() =>
                setMostrarFormularioEvolucao(!mostrarFormularioEvolucao)
              }
            >
              {mostrarFormularioEvolucao
                ? "Cancelar evolução"
                : "Nova evolução clínica"}
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
                <strong>{timeline.length}</strong>
                <p>Histórico longitudinal do paciente</p>
              </div>
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

            <h3 className="section-title">Linha do tempo</h3>

            {timeline.length === 0 ? (
              <p className="muted">Nenhum evento registrado.</p>
            ) : (
              <div className="timeline">
                {timeline.map((item, index) => (
                  <div
                    className={`timeline-item timeline-${item.tipo}`}
                    key={`${item.tipo}-${index}`}
                  >
                    <div className="timeline-icon">
                      {getTimelineIcon(item.tipo)}
                    </div>

                    <div className="timeline-content">
                      <div className="timeline-top">
                        <strong>{item.titulo}</strong>
                        <span>{formatarData(item.data)}</span>
                      </div>

                      <p>{item.descricao || "Sem descrição."}</p>

                      <div className="timeline-tags">
                        <span>{item.tipo}</span>
                        {item.subtipo && <span>{item.subtipo}</span>}
                        {item.intervencao_id && (
                          <span>Intervenção #{item.intervencao_id}</span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
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
        Pacientes clínicos, prontuário, evolução, desfechos e timeline.
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
                    <button
                      className="primary-button"
                      onClick={() => abrirProntuario(p)}
                    >
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

function formatarData(valor) {
  if (!valor) return "Sem data";

  try {
    return new Date(valor).toLocaleString("pt-BR");
  } catch {
    return valor;
  }
}

function getTimelineIcon(tipo) {
  if (tipo === "servico_rapido") return "SR";
  if (tipo === "prontuario") return "P";
  if (tipo === "evolucao") return "E";
  if (tipo === "desfecho") return "D";
  return "•";
}