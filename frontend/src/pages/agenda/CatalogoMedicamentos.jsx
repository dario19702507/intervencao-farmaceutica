import { useEffect, useMemo, useRef, useState } from "react";
import { api } from "../../api/api";

const LIMITE_PAGINA = 50;

const medicamentoVazio = {
  principio_ativo: "",
  concentracao: "",
  forma_farmaceutica: "",
  via_administracao: "",
  classe_terapeutica: "",
  registro_anvisa: "",
  codigo_atc: "",
  nome_comercial: "",
  laboratorio: "",
  apresentacao: "",
  componente: "",
  observacoes: "",
  ativo: true,
};

function normalizarErro(error, fallback) {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((item) => item.msg || item.detail || String(item)).join("; ");
  return fallback;
}

function textoMedicamento(item) {
  return [
    item.principio_ativo || item.farmaco,
    item.concentracao,
    item.forma_farmaceutica,
    item.via_administracao,
  ]
    .filter(Boolean)
    .join(" • ");
}

export default function CatalogoMedicamentos() {
  const [medicamentos, setMedicamentos] = useState([]);
  const [resumo, setResumo] = useState(null);
  const [busca, setBusca] = useState("");
  const [somenteAtivos, setSomenteAtivos] = useState(true);
  const [offset, setOffset] = useState(0);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [salvando, setSalvando] = useState(false);
  const [mensagem, setMensagem] = useState("");
  const [erro, setErro] = useState("");
  const [formularioAberto, setFormularioAberto] = useState(false);
  const [editandoId, setEditandoId] = useState(null);
  const [formulario, setFormulario] = useState(medicamentoVazio);
  const [arquivoCsv, setArquivoCsv] = useState(null);
  const [substituirExistentes, setSubstituirExistentes] = useState(false);
  const inputArquivoRef = useRef(null);

  const paginaAtual = Math.floor(offset / LIMITE_PAGINA) + 1;
  const totalPaginas = Math.max(Math.ceil(total / LIMITE_PAGINA), 1);

  const formasFrequentes = useMemo(() => resumo?.formas_frequentes || [], [resumo]);

  async function carregarResumo() {
    try {
      const response = await api.get("/medicamentos/resumo");
      setResumo(response.data || null);
    } catch (error) {
      console.error("Erro ao carregar resumo do catálogo:", error);
    }
  }

  async function carregarMedicamentos(novoOffset = offset) {
    setLoading(true);
    setErro("");
    try {
      const response = await api.get("/medicamentos", {
        params: {
          q: busca.trim() || undefined,
          ativo: somenteAtivos ? true : undefined,
          limit: LIMITE_PAGINA,
          offset: novoOffset,
        },
      });
      setMedicamentos(response.data?.medicamentos || []);
      setTotal(response.data?.total || 0);
      setOffset(response.data?.offset ?? novoOffset);
    } catch (error) {
      console.error("Erro ao carregar catálogo de medicamentos:", error);
      setErro(normalizarErro(error, "Não foi possível carregar o catálogo de medicamentos."));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    carregarResumo();
    carregarMedicamentos(0);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function atualizarCampo(campo, valor) {
    setFormulario((atual) => ({ ...atual, [campo]: valor }));
  }

  function novoMedicamento() {
    setEditandoId(null);
    setFormulario(medicamentoVazio);
    setFormularioAberto(true);
    setMensagem("");
    setErro("");
  }

  function editarMedicamento(item) {
    setEditandoId(item.id);
    setFormulario({
      principio_ativo: item.principio_ativo || item.farmaco || "",
      concentracao: item.concentracao || "",
      forma_farmaceutica: item.forma_farmaceutica || "",
      via_administracao: item.via_administracao || "",
      classe_terapeutica: item.classe_terapeutica || "",
      registro_anvisa: item.registro_anvisa || "",
      codigo_atc: item.codigo_atc || "",
      nome_comercial: item.nome_comercial || "",
      laboratorio: item.laboratorio || "",
      apresentacao: item.apresentacao || "",
      componente: item.componente || "",
      observacoes: item.observacoes || "",
      ativo: item.ativo !== false,
    });
    setFormularioAberto(true);
    setMensagem("");
    setErro("");
  }

  async function salvarMedicamento(event) {
    event.preventDefault();
    if (!formulario.principio_ativo.trim()) {
      setErro("Informe o princípio ativo.");
      return;
    }
    setSalvando(true);
    setErro("");
    setMensagem("");
    try {
      const payload = {
        ...formulario,
        principio_ativo: formulario.principio_ativo.trim(),
      };
      if (editandoId) {
        await api.put(`/medicamentos/${editandoId}`, payload);
        setMensagem("Medicamento atualizado com sucesso.");
      } else {
        await api.post("/medicamentos", payload);
        setMensagem("Medicamento cadastrado com sucesso.");
      }
      setFormularioAberto(false);
      setEditandoId(null);
      setFormulario(medicamentoVazio);
      await carregarResumo();
      await carregarMedicamentos(offset);
    } catch (error) {
      console.error("Erro ao salvar medicamento:", error);
      setErro(normalizarErro(error, "Erro ao salvar medicamento."));
    } finally {
      setSalvando(false);
    }
  }

  async function alterarAtivo(item) {
    const novoStatus = !(item.ativo !== false);
    const confirmar = window.confirm(novoStatus ? "Reativar este medicamento?" : "Inativar este medicamento?");
    if (!confirmar) return;
    setErro("");
    setMensagem("");
    try {
      await api.post(`/medicamentos/${item.id}/ativar`, null, { params: { ativo: novoStatus } });
      setMensagem(novoStatus ? "Medicamento reativado." : "Medicamento inativado.");
      await carregarResumo();
      await carregarMedicamentos(offset);
    } catch (error) {
      console.error("Erro ao alterar status do medicamento:", error);
      setErro(normalizarErro(error, "Erro ao alterar status do medicamento."));
    }
  }

  async function importarCsv(event) {
    event.preventDefault();
    if (!arquivoCsv) {
      setErro("Selecione um arquivo CSV ou TXT.");
      return;
    }
    setSalvando(true);
    setErro("");
    setMensagem("");
    try {
      const formData = new FormData();
      formData.append("file", arquivoCsv);
      const response = await api.post("/medicamentos/importar-csv", formData, {
        params: { substituir_existentes: substituirExistentes },
        headers: { "Content-Type": "multipart/form-data" },
      });
      const data = response.data || {};
      setMensagem(
        `Importação concluída. Criados: ${data.criados || 0}. Atualizados: ${data.atualizados || 0}. Ignorados: ${data.ignorados || 0}.`
      );
      setArquivoCsv(null);
      if (inputArquivoRef.current) inputArquivoRef.current.value = "";
      await carregarResumo();
      await carregarMedicamentos(0);
    } catch (error) {
      console.error("Erro ao importar catálogo:", error);
      setErro(normalizarErro(error, "Erro ao importar CSV."));
    } finally {
      setSalvando(false);
    }
  }

  async function aplicarBusca(event) {
    event.preventDefault();
    await carregarMedicamentos(0);
  }

  async function mudarPagina(delta) {
    const novoOffset = Math.max(offset + delta * LIMITE_PAGINA, 0);
    if (novoOffset >= total && total > 0) return;
    await carregarMedicamentos(novoOffset);
  }

  return (
    <div className="catalogo-medicamentos-page">
      <div className="page-header-row">
        <div>
          <h2>Catálogo de Medicamentos</h2>
          <p className="muted">
            Base simplificada para padronizar medicamentos em consultório, farmacoterapia e intervenções.
          </p>
        </div>
        <div className="action-buttons">
          <button className="secondary-button" onClick={() => { carregarResumo(); carregarMedicamentos(offset); }} disabled={loading}>
            {loading ? "Atualizando..." : "Atualizar"}
          </button>
          <button className="primary-button" onClick={novoMedicamento}>Novo medicamento</button>
        </div>
      </div>

      {mensagem && <div className="alert success">{mensagem}</div>}
      {erro && <div className="alert error">{erro}</div>}

      <div className="cards-grid four">
        <div className="metric-card"><span>Total</span><strong>{resumo?.total ?? 0}</strong></div>
        <div className="metric-card success"><span>Ativos</span><strong>{resumo?.ativos ?? 0}</strong></div>
        <div className="metric-card warning"><span>Inativos</span><strong>{resumo?.inativos ?? 0}</strong></div>
        <div className="metric-card"><span>Com registro ANVISA</span><strong>{resumo?.com_registro_anvisa ?? 0}</strong></div>
      </div>

      {formasFrequentes.length > 0 && (
        <div className="form-card">
          <h3>Formas farmacêuticas frequentes</h3>
          <div className="tag-list">
            {formasFrequentes.map((item) => (
              <span className="timeline-tag" key={item.forma_farmaceutica}>
                {item.forma_farmaceutica}: {item.total}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="form-card">
        <div className="section-header">
          <div>
            <h3>Buscar medicamentos</h3>
            <p className="muted">Pesquise por princípio ativo, nome comercial, apresentação ou registro ANVISA.</p>
          </div>
        </div>
        <form className="filters-row" onSubmit={aplicarBusca}>
          <label>
            Termo de busca
            <input
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
              placeholder="Ex.: losartana, insulina, 50 mg, registro"
            />
          </label>
          <label className="checkbox-row catalogo-checkbox-inline">
            <input
              type="checkbox"
              checked={somenteAtivos}
              onChange={(e) => setSomenteAtivos(e.target.checked)}
            />
            Exibir apenas ativos
          </label>
          <div className="action-buttons">
            <button className="primary-button" type="submit" disabled={loading}>Buscar</button>
            <button
              className="secondary-button"
              type="button"
              onClick={() => { setBusca(""); setSomenteAtivos(true); setTimeout(() => carregarMedicamentos(0), 0); }}
            >
              Limpar
            </button>
          </div>
        </form>
      </div>

      {formularioAberto && (
        <form className="form-card" onSubmit={salvarMedicamento}>
          <div className="section-header">
            <div>
              <h3>{editandoId ? "Editar medicamento" : "Novo medicamento"}</h3>
              <p className="muted">Cadastre a forma simplificada que será usada futuramente na farmacoterapia.</p>
            </div>
            <button type="button" className="secondary-button" onClick={() => setFormularioAberto(false)}>Fechar</button>
          </div>

          <div className="filters-row">
            <label>Princípio ativo<input value={formulario.principio_ativo} onChange={(e) => atualizarCampo("principio_ativo", e.target.value)} required /></label>
            <label>Nome comercial<input value={formulario.nome_comercial} onChange={(e) => atualizarCampo("nome_comercial", e.target.value)} /></label>
            <label>Concentração<input value={formulario.concentracao} onChange={(e) => atualizarCampo("concentracao", e.target.value)} placeholder="Ex.: 50 mg" /></label>
            <label>Forma farmacêutica<input value={formulario.forma_farmaceutica} onChange={(e) => atualizarCampo("forma_farmaceutica", e.target.value)} placeholder="Comprimido, solução..." /></label>
            <label>Via de administração<input value={formulario.via_administracao} onChange={(e) => atualizarCampo("via_administracao", e.target.value)} placeholder="Oral, SC, IV..." /></label>
            <label>Classe terapêutica<input value={formulario.classe_terapeutica} onChange={(e) => atualizarCampo("classe_terapeutica", e.target.value)} /></label>
            <label>Registro ANVISA<input value={formulario.registro_anvisa} onChange={(e) => atualizarCampo("registro_anvisa", e.target.value)} /></label>
            <label>Código ATC<input value={formulario.codigo_atc} onChange={(e) => atualizarCampo("codigo_atc", e.target.value)} /></label>
            <label>Laboratório<input value={formulario.laboratorio} onChange={(e) => atualizarCampo("laboratorio", e.target.value)} /></label>
            <label>Componente<input value={formulario.componente} onChange={(e) => atualizarCampo("componente", e.target.value)} placeholder="Básico, CEAF..." /></label>
          </div>

          <label className="full-width-label">
            Apresentação
            <input value={formulario.apresentacao} onChange={(e) => atualizarCampo("apresentacao", e.target.value)} placeholder="Descrição da apresentação" />
          </label>
          <label className="full-width-label">
            Observações
            <textarea value={formulario.observacoes} onChange={(e) => atualizarCampo("observacoes", e.target.value)} />
          </label>
          <label className="checkbox-row">
            <input type="checkbox" checked={formulario.ativo} onChange={(e) => atualizarCampo("ativo", e.target.checked)} />
            Medicamento ativo
          </label>
          <div className="action-buttons">
            <button className="primary-button" type="submit" disabled={salvando}>{salvando ? "Salvando..." : "Salvar"}</button>
            <button className="secondary-button" type="button" onClick={() => setFormularioAberto(false)}>Cancelar</button>
          </div>
        </form>
      )}

      <form className="form-card" onSubmit={importarCsv}>
        <div className="section-header">
          <div>
            <h3>Importação CSV</h3>
            <p className="muted">Aceita CSV/TXT com colunas como princípio ativo, concentração, forma, via e registro ANVISA.</p>
          </div>
        </div>
        <div className="filters-row">
          <label>
            Arquivo CSV/TXT
            <input ref={inputArquivoRef} type="file" accept=".csv,.txt" onChange={(e) => setArquivoCsv(e.target.files?.[0] || null)} />
          </label>
          <label className="checkbox-row catalogo-checkbox-inline">
            <input type="checkbox" checked={substituirExistentes} onChange={(e) => setSubstituirExistentes(e.target.checked)} />
            Atualizar existentes
          </label>
          <div className="action-buttons"><button className="primary-button" type="submit" disabled={salvando}>Importar</button></div>
        </div>
      </form>

      <div className="form-card">
        <div className="section-header">
          <div>
            <h3>Medicamentos cadastrados</h3>
            <p className="muted">{total} registro(s) encontrado(s). Página {paginaAtual} de {totalPaginas}.</p>
          </div>
          <div className="action-buttons">
            <button className="secondary-button" disabled={offset === 0 || loading} onClick={() => mudarPagina(-1)}>Anterior</button>
            <button className="secondary-button" disabled={offset + LIMITE_PAGINA >= total || loading} onClick={() => mudarPagina(1)}>Próxima</button>
          </div>
        </div>

        {loading ? (
          <p className="muted">Carregando medicamentos...</p>
        ) : medicamentos.length === 0 ? (
          <p className="muted">Nenhum medicamento encontrado.</p>
        ) : (
          <div className="table-wrapper">
            <table className="agenda-table catalogo-medicamentos-table">
              <thead>
                <tr>
                  <th>Medicamento</th>
                  <th>Nome comercial</th>
                  <th>Registro</th>
                  <th>Classe/Componente</th>
                  <th>Status</th>
                  <th>Ações</th>
                </tr>
              </thead>
              <tbody>
                {medicamentos.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <strong>{textoMedicamento(item) || "-"}</strong>
                      {item.apresentacao ? <small className="muted block">{item.apresentacao}</small> : null}
                    </td>
                    <td>{item.nome_comercial || "-"}</td>
                    <td>{item.registro_anvisa || "-"}</td>
                    <td>
                      {item.classe_terapeutica || "-"}
                      {item.componente ? <small className="muted block">{item.componente}</small> : null}
                    </td>
                    <td><span className={`timeline-tag ${item.ativo === false ? "cancelado" : "realizado"}`}>{item.ativo === false ? "Inativo" : "Ativo"}</span></td>
                    <td>
                      <div className="action-buttons">
                        <button className="secondary-button" onClick={() => editarMedicamento(item)}>Editar</button>
                        <button className="secondary-button" onClick={() => alterarAtivo(item)}>{item.ativo === false ? "Ativar" : "Inativar"}</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
