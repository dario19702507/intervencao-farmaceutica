import { useEffect, useMemo, useState } from "react";
import { api } from "../../api/api";

const LIMIT = 50;

function formatarData(data) {
  if (!data) return "-";
  try {
    return new Date(`${data}T00:00:00`).toLocaleDateString("pt-BR");
  } catch {
    return data;
  }
}

function dataISOEmDias(dias) {
  const data = new Date();
  data.setDate(data.getDate() + dias);
  return data.toISOString().slice(0, 10);
}

function classificarVigencia(dataFim) {
  if (!dataFim) return { label: "Sem vigência", className: "badge" };
  const hoje = new Date();
  hoje.setHours(0, 0, 0, 0);
  const fim = new Date(`${dataFim}T00:00:00`);
  const diferencaDias = Math.ceil((fim - hoje) / (1000 * 60 * 60 * 24));

  if (diferencaDias < 0) {
    return { label: "Vencida", className: "badge badge-alta" };
  }
  if (diferencaDias <= 30) {
    return { label: "A vencer", className: "badge badge-warning" };
  }
  return { label: "Vigente", className: "badge badge-success" };
}

function resumoPercentual(valor, total) {
  if (!total) return "0%";
  return `${Math.round((Number(valor || 0) / Number(total || 1)) * 100)}%`;
}

export default function PacientesCeaf() {
  const [pacientes, setPacientes] = useState([]);
  const [resumo, setResumo] = useState(null);
  const [detalhe, setDetalhe] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingDetalhe, setLoadingDetalhe] = useState(false);
  const [erro, setErro] = useState("");
  const [offset, setOffset] = useState(0);
  const [total, setTotal] = useState(0);
  const [filtros, setFiltros] = useState({
    termo: "",
    medicamento: "",
    municipio: "",
    situacao_lme: "",
    vigencia: "",
  });

  const paginaAtual = useMemo(() => Math.floor(offset / LIMIT) + 1, [offset]);
  const totalPaginas = useMemo(() => Math.max(1, Math.ceil(total / LIMIT)), [total]);

  function montarParametros(offsetAtual = offset) {
    const params = {
      limit: LIMIT,
      offset: offsetAtual,
      ativo: true,
    };

    if (filtros.termo.trim()) params.termo = filtros.termo.trim();
    if (filtros.medicamento.trim()) params.medicamento = filtros.medicamento.trim();
    if (filtros.municipio.trim()) params.municipio = filtros.municipio.trim();
    if (filtros.situacao_lme.trim()) params.situacao_lme = filtros.situacao_lme.trim();

    if (filtros.vigencia === "vencidas") params.vigencia_ate = dataISOEmDias(0);
    if (filtros.vigencia === "30") params.vigencia_ate = dataISOEmDias(30);
    if (filtros.vigencia === "60") params.vigencia_ate = dataISOEmDias(60);

    return params;
  }

  async function carregarResumo() {
    try {
      const response = await api.get("/ceaf/pacientes/resumo");
      setResumo(response.data);
    } catch (error) {
      console.error(error);
    }
  }

  async function carregarPacientes(offsetAtual = 0) {
    try {
      setLoading(true);
      setErro("");
      const response = await api.get("/ceaf/pacientes", {
        params: montarParametros(offsetAtual),
      });
      setPacientes(response.data.pacientes || []);
      setTotal(response.data.total || 0);
      setOffset(response.data.offset || offsetAtual);
    } catch (error) {
      console.error(error);
      setErro("Erro ao carregar pacientes CEAF. Verifique conexão, autenticação e permissões.");
    } finally {
      setLoading(false);
    }
  }

  async function abrirDetalhe(paciente) {
    try {
      setLoadingDetalhe(true);
      setDetalhe({ paciente });
      const response = await api.get(`/ceaf/pacientes/${paciente.id}`);
      setDetalhe(response.data);
    } catch (error) {
      console.error(error);
      alert("Erro ao carregar detalhes do paciente CEAF.");
    } finally {
      setLoadingDetalhe(false);
    }
  }

  function atualizarFiltro(campo, valor) {
    setFiltros((atual) => ({ ...atual, [campo]: valor }));
  }

  function pesquisar() {
    setDetalhe(null);
    carregarPacientes(0);
  }

  function limparFiltros() {
    setFiltros({ termo: "", medicamento: "", municipio: "", situacao_lme: "", vigencia: "" });
    setDetalhe(null);
    setTimeout(() => carregarPacientes(0), 0);
  }

  useEffect(() => {
    carregarResumo();
    carregarPacientes(0);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="agenda-container pacientes-ceaf-page">
      <div className="page-header">
        <div>
          <h2>Pacientes CEAF</h2>
          <p>Consulta dos pacientes importados do CEAF para conferência de cadastro, vigência de LME e preparação do cuidado farmacêutico.</p>
        </div>
      </div>

      <div className="dashboard-grid ceaf-summary-grid">
        <div className="summary-card">
          <strong>Total CEAF</strong>
          <div>{resumo?.total ?? "-"}</div>
          <small>Registros importados</small>
        </div>
        <div className="summary-card">
          <strong>Ativos</strong>
          <div>{resumo?.ativos ?? "-"}</div>
          <small>{resumoPercentual(resumo?.ativos, resumo?.total)} da base</small>
        </div>
        <div className="summary-card">
          <strong>Com CPF</strong>
          <div>{resumo?.com_cpf ?? "-"}</div>
          <small>{resumoPercentual(resumo?.com_cpf, resumo?.total)} com identificação</small>
        </div>
        <div className="summary-card">
          <strong>Medicamentos</strong>
          <div>{resumo?.medicamentos_distintos ?? "-"}</div>
          <small>Medicamentos distintos</small>
        </div>
      </div>

      <div className="form-card ceaf-filter-card">
        <div className="section-header-row">
          <div>
            <h3>Filtros</h3>
            <p>Pesquise por nome, CPF, CNS, telefone, medicamento, município, situação da LME ou vencimento.</p>
          </div>
        </div>

        <div className="filters-row ceaf-filters-row">
          <label>
            Busca geral
            <input
              type="text"
              value={filtros.termo}
              placeholder="Nome, CPF, CNS ou telefone"
              onChange={(e) => atualizarFiltro("termo", e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && pesquisar()}
            />
          </label>

          <label>
            Medicamento
            <input
              type="text"
              value={filtros.medicamento}
              placeholder="Ex.: omalizumabe, formoterol"
              onChange={(e) => atualizarFiltro("medicamento", e.target.value)}
            />
          </label>

          <label>
            Município
            <input
              type="text"
              value={filtros.municipio}
              placeholder="Município"
              onChange={(e) => atualizarFiltro("municipio", e.target.value)}
            />
          </label>

          <label>
            Situação LME
            <input
              type="text"
              value={filtros.situacao_lme}
              placeholder="Ex.: Deferida"
              onChange={(e) => atualizarFiltro("situacao_lme", e.target.value)}
            />
          </label>

          <label>
            Vigência
            <select value={filtros.vigencia} onChange={(e) => atualizarFiltro("vigencia", e.target.value)}>
              <option value="">Todas</option>
              <option value="vencidas">Vencidas</option>
              <option value="30">Vencidas ou a vencer em 30 dias</option>
              <option value="60">Vencidas ou a vencer em 60 dias</option>
            </select>
          </label>
        </div>

        <div className="action-buttons">
          <button className="primary-button" onClick={pesquisar} disabled={loading}>
            {loading ? "Pesquisando..." : "Pesquisar"}
          </button>
          <button className="secondary-button" onClick={limparFiltros} disabled={loading}>
            Limpar filtros
          </button>
        </div>
      </div>

      <div className="form-card ceaf-table-card">
        <div className="section-header-row">
          <div>
            <h3>Registros encontrados</h3>
            <p>{total} paciente(s) CEAF. Página {paginaAtual} de {totalPaginas}.</p>
          </div>
          <div className="ceaf-pagination-actions">
            <button className="secondary-button" disabled={loading || offset <= 0} onClick={() => carregarPacientes(Math.max(0, offset - LIMIT))}>
              Anterior
            </button>
            <button className="secondary-button" disabled={loading || offset + LIMIT >= total} onClick={() => carregarPacientes(offset + LIMIT)}>
              Próxima
            </button>
          </div>
        </div>

        {erro && <div className="alert-card alert-alta"><div className="alert-content"><strong>Atenção</strong><p>{erro}</p></div></div>}

        {loading ? (
          <p>Carregando pacientes CEAF...</p>
        ) : pacientes.length === 0 ? (
          <p>Nenhum paciente encontrado para os filtros selecionados.</p>
        ) : (
          <div className="ceaf-table-wrapper">
            <table className="agenda-table ceaf-table">
              <thead>
                <tr>
                  <th>Paciente</th>
                  <th>CPF/CNS</th>
                  <th>Medicamento</th>
                  <th>Município</th>
                  <th>Vigência</th>
                  <th>Situação</th>
                  <th>Ações</th>
                </tr>
              </thead>
              <tbody>
                {pacientes.map((paciente) => {
                  const vigencia = classificarVigencia(paciente.data_fim_vigencia);
                  return (
                    <tr key={paciente.id}>
                      <td>
                        <strong>{paciente.nome}</strong>
                        <small className="table-subtext">Tel.: {paciente.telefone_celular || paciente.telefone || paciente.telefone_comercial || "-"}</small>
                      </td>
                      <td>
                        <div>CPF: {paciente.cpf || "-"}</div>
                        <small className="table-subtext">CNS: {paciente.cns || "-"}</small>
                      </td>
                      <td>{paciente.medicamento_prescrito || "-"}</td>
                      <td>{paciente.municipio || "-"}</td>
                      <td>
                        <span className={vigencia.className}>{vigencia.label}</span>
                        <small className="table-subtext">{formatarData(paciente.data_fim_vigencia)}</small>
                      </td>
                      <td>{paciente.situacao_lme || "-"}</td>
                      <td>
                        <button className="secondary-button" onClick={() => abrirDetalhe(paciente)}>
                          Detalhes
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {detalhe?.paciente && (
        <div className="form-card ceaf-detail-card">
          <div className="section-header-row">
            <div>
              <h3>Detalhes do paciente CEAF</h3>
              <p>{detalhe.paciente.nome}</p>
            </div>
            <button className="secondary-button" onClick={() => setDetalhe(null)}>Fechar</button>
          </div>

          {loadingDetalhe ? (
            <p>Carregando detalhes...</p>
          ) : (
            <div className="ceaf-detail-grid">
              <div><strong>CPF</strong><span>{detalhe.paciente.cpf || "-"}</span></div>
              <div><strong>CNS</strong><span>{detalhe.paciente.cns || "-"}</span></div>
              <div><strong>Município</strong><span>{detalhe.paciente.municipio || "-"}</span></div>
              <div><strong>Telefone</strong><span>{detalhe.paciente.telefone_celular || detalhe.paciente.telefone || detalhe.paciente.telefone_comercial || "-"}</span></div>
              <div className="wide"><strong>Endereço</strong><span>{[detalhe.paciente.logradouro, detalhe.paciente.numero_residencia, detalhe.paciente.complemento_residencia].filter(Boolean).join(", ") || "-"}</span></div>
              <div className="wide"><strong>Medicamento prescrito</strong><span>{detalhe.paciente.medicamento_prescrito || "-"}</span></div>
              <div><strong>Início do medicamento</strong><span>{formatarData(detalhe.paciente.data_inicio_medicamento)}</span></div>
              <div><strong>Fim da vigência</strong><span>{formatarData(detalhe.paciente.data_fim_vigencia)}</span></div>
              <div><strong>Situação LME</strong><span>{detalhe.paciente.situacao_lme || "-"}</span></div>
              <div><strong>Lote de importação</strong><span>{detalhe.paciente.lote_importacao || "-"}</span></div>
            </div>
          )}

          <p className="helper-text">
            A conversão para paciente clínico será habilitada na próxima etapa, após validação da deduplicação entre CEAF, pacientes clínicos e prontuário longitudinal.
          </p>
        </div>
      )}
    </div>
  );
}
