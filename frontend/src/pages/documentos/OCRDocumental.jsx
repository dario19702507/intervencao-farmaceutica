import { useEffect, useMemo, useState } from "react";
import { api } from "../../api/api";
import "./OCRDocumental.css";

function normalizarPacientes(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.pacientes)) return payload.pacientes;
  if (Array.isArray(payload?.items)) return payload.items;
  return [];
}

function normalizarProcessos(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.processos)) return payload.processos;
  if (Array.isArray(payload?.items)) return payload.items;
  return [];
}

function normalizarProcessoDetalhe(payload) {
  return payload?.processo || payload?.item || payload || null;
}

function normalizarDocumentos(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.documentos)) return payload.documentos;
  if (Array.isArray(payload?.items)) return payload.items;
  return [];
}

function nomePaciente(paciente) {
  return paciente?.nome || paciente?.nome_completo || paciente?.paciente_nome || `Paciente #${paciente?.id}`;
}

function formatarDataHora(valor) {
  if (!valor) return "-";
  const data = new Date(valor);
  if (Number.isNaN(data.getTime())) return valor;
  return data.toLocaleString("pt-BR");
}

function valorLegivel(valor) {
  if (valor === null || valor === undefined || valor === "") return "-";
  if (Array.isArray(valor)) return valor.length ? valor.join(", ") : "-";
  if (typeof valor === "object") return JSON.stringify(valor, null, 2);
  return String(valor);
}

function badgeClasse(valor) {
  const v = (valor || "").toString().toUpperCase();
  if (v.includes("ERRO") || v.includes("NAO_SUPORTADO")) return "danger";
  if (v.includes("SEM_TEXTO")) return "warning";
  if (v.includes("CONCLUIDO") || v.includes("PDF_TEXTO") || v.includes("TEXTO")) return "success";
  return "neutral";
}


function tipoClassificacao(extracao) {
  return extracao?.tipo_documento_sugerido || extracao?.classificacao_documental?.tipo || extracao?.campos_sugeridos?.classificacao_documental?.tipo || "";
}

function confiancaClassificacao(extracao) {
  const valor = extracao?.confianca_classificacao ?? extracao?.classificacao_documental?.confianca ?? extracao?.campos_sugeridos?.classificacao_documental?.confianca;
  if (valor === null || valor === undefined || valor === "") return "-";
  const n = Number(valor);
  if (Number.isNaN(n)) return String(valor);
  return `${Math.round(n * 100)}%`;
}

function classificacaoManual(extracao) {
  return Boolean(extracao?.classificacao_documental?.manual || extracao?.campos_sugeridos?.classificacao_documental?.manual);
}

export default function OCRDocumental() {
  const [pacientes, setPacientes] = useState([]);
  const [pacienteId, setPacienteId] = useState("");
  const [processos, setProcessos] = useState([]);
  const [processoId, setProcessoId] = useState("");
  const [processoDetalhe, setProcessoDetalhe] = useState(null);
  const [documentosProcesso, setDocumentosProcesso] = useState([]);
  const [opcoes, setOpcoes] = useState(null);
  const [extracoesProcesso, setExtracoesProcesso] = useState([]);
  const [extracaoSelecionadaId, setExtracaoSelecionadaId] = useState("");
  const [loading, setLoading] = useState(false);
  const [processandoId, setProcessandoId] = useState(null);
  const [classificacaoManualTipo, setClassificacaoManualTipo] = useState("");
  const [classificacaoManualObs, setClassificacaoManualObs] = useState("");
  const [erro, setErro] = useState("");
  const [sucesso, setSucesso] = useState("");

  const documentos = documentosProcesso.length ? documentosProcesso : (processoDetalhe?.documentos || []);

  const extracaoSelecionada = useMemo(() => {
    if (!extracaoSelecionadaId) return extracoesProcesso[0] || null;
    return extracoesProcesso.find((item) => String(item.id) === String(extracaoSelecionadaId)) || null;
  }, [extracoesProcesso, extracaoSelecionadaId]);

  const pacienteSelecionado = useMemo(
    () => pacientes.find((p) => String(p.id) === String(pacienteId)),
    [pacientes, pacienteId]
  );

  const ultimaExtracaoPorDocumento = useMemo(() => {
    const mapa = new Map();
    for (const extracao of extracoesProcesso) {
      if (!mapa.has(String(extracao.documento_id))) {
        mapa.set(String(extracao.documento_id), extracao);
      }
    }
    return mapa;
  }, [extracoesProcesso]);

  async function carregarBase() {
    setLoading(true);
    setErro("");
    try {
      const [pacientesResp, opcoesResp] = await Promise.all([
        api.get("/consultorio/pacientes-clinicos"),
        api.get("/consultorio/documentos/ocr/opcoes"),
      ]);
      const lista = normalizarPacientes(pacientesResp.data);
      setPacientes(lista);
      setOpcoes(opcoesResp.data || null);
      if (!pacienteId && lista.length > 0) {
        setPacienteId(String(lista[0].id));
      }
    } catch (e) {
      console.error(e);
      setErro("Não foi possível carregar a base do OCR. Verifique se o backend está ativo.");
    } finally {
      setLoading(false);
    }
  }

  async function carregarProcessosDoPaciente(idPaciente) {
    if (!idPaciente) return;
    setErro("");
    try {
      const resp = await api.get(`/consultorio/paciente-clinico/${idPaciente}/processos-documentais`);
      const lista = normalizarProcessos(resp.data);
      setProcessos(lista);
      setProcessoDetalhe(null);
      setDocumentosProcesso([]);
      setExtracoesProcesso([]);
      setExtracaoSelecionadaId("");
      if (lista.length > 0) {
        setProcessoId(String(lista[0].id));
      } else {
        setProcessoId("");
      }
    } catch (e) {
      console.error(e);
      setErro("Não foi possível carregar os pacotes documentais do paciente.");
    }
  }

  async function carregarProcesso(idProcesso) {
    if (!idProcesso) return;
    setErro("");
    try {
      const [processoResp, docsResp, ocrResp] = await Promise.all([
        api.get(`/consultorio/processos-documentais/${idProcesso}`),
        api.get(`/consultorio/processos-documentais/${idProcesso}/documentos`),
        api.get(`/consultorio/processos-documentais/${idProcesso}/ocr`),
      ]);

      const detalhe = normalizarProcessoDetalhe(processoResp.data);
      const docs = normalizarDocumentos(docsResp.data);

      setProcessoDetalhe(detalhe);
      setDocumentosProcesso(docs.length ? docs : (detalhe?.documentos || []));
      const extracoes = ocrResp.data?.extracoes || [];
      setExtracoesProcesso(extracoes);
      setExtracaoSelecionadaId(extracoes[0]?.id ? String(extracoes[0].id) : "");
    } catch (e) {
      console.error(e);
      setErro("Não foi possível carregar o pacote documental ou suas extrações.");
    }
  }

  useEffect(() => {
    carregarBase();
  }, []);

  useEffect(() => {
    if (pacienteId) carregarProcessosDoPaciente(pacienteId);
  }, [pacienteId]);

  useEffect(() => {
    if (processoId) carregarProcesso(processoId);
  }, [processoId]);

  useEffect(() => {
    setClassificacaoManualTipo(tipoClassificacao(extracaoSelecionada));
    setClassificacaoManualObs("");
  }, [extracaoSelecionada?.id]);

  async function extrairDocumento(documentoId) {
    setErro("");
    setSucesso("");
    setProcessandoId(documentoId);
    try {
      const resp = await api.post(`/consultorio/documentos/${documentoId}/ocr/extrair`);
      const extracao = resp.data?.extracao;
      setSucesso(`Extração concluída para o documento #${documentoId}.`);
      if (processoId) await carregarProcesso(processoId);
      if (extracao?.id) setExtracaoSelecionadaId(String(extracao.id));
    } catch (e) {
      console.error(e);
      const detalhe = e.response?.data?.detail;
      setErro(typeof detalhe === "string" ? detalhe : "Não foi possível executar o OCR deste documento.");
    } finally {
      setProcessandoId(null);
    }
  }

  async function extrairTodosDocumentos() {
    if (!documentos.length) return;
    setErro("");
    setSucesso("");
    let sucessoLocal = 0;
    for (const doc of documentos) {
      try {
        setProcessandoId(doc.id);
        await api.post(`/consultorio/documentos/${doc.id}/ocr/extrair`);
        sucessoLocal += 1;
      } catch (e) {
        console.error(e);
      }
    }
    setProcessandoId(null);
    setSucesso(`${sucessoLocal} documento(s) processado(s). Confira as sugestões antes de qualquer uso administrativo.`);
    if (processoId) await carregarProcesso(processoId);
  }

  async function salvarReclassificacaoManual() {
    if (!extracaoSelecionada?.documento_id || !classificacaoManualTipo) return;
    setErro("");
    setSucesso("");
    try {
      const resp = await api.patch(`/consultorio/documentos/${extracaoSelecionada.documento_id}/ocr/classificacao`, {
        tipo: classificacaoManualTipo,
        observacao: classificacaoManualObs || "Reclassificação manual confirmada na tela de OCR",
      });
      setSucesso("Classificação documental atualizada manualmente.");
      if (processoId) await carregarProcesso(processoId);
      if (resp.data?.extracao?.id) setExtracaoSelecionadaId(String(resp.data.extracao.id));
    } catch (e) {
      console.error(e);
      const detalhe = e.response?.data?.detail;
      setErro(typeof detalhe === "string" ? detalhe : "Não foi possível salvar a reclassificação manual.");
    }
  }

  return (
    <div className="ocr-page">
      <div className="ocr-header">
        <div>
          <span className="ocr-kicker">Passo 12B</span>
          <h1>OCR Documental</h1>
          <p>
            Extraia texto, classifique o tipo documental e confira campos sugeridos. Nada é aplicado automaticamente ao cadastro, vigência, agenda ou WhatsApp.
          </p>
        </div>
        <button className="ocr-primary" onClick={extrairTodosDocumentos} disabled={!documentos.length || Boolean(processandoId)}>
          {processandoId ? "Processando..." : "Extrair todos do pacote"}
        </button>
      </div>

      {erro && <div className="ocr-alert danger">{erro}</div>}
      {sucesso && <div className="ocr-alert success">{sucesso}</div>}
      {opcoes?.observacao && <div className="ocr-alert info">{opcoes.observacao}</div>}

      <section className="ocr-grid controls">
        <div className="ocr-card">
          <label>Paciente</label>
          <select value={pacienteId} onChange={(e) => setPacienteId(e.target.value)} disabled={loading}>
            {pacientes.map((paciente) => (
              <option key={paciente.id} value={paciente.id}>{nomePaciente(paciente)}</option>
            ))}
          </select>
          {pacienteSelecionado && (
            <small>Paciente selecionado: {nomePaciente(pacienteSelecionado)}</small>
          )}
        </div>

        <div className="ocr-card">
          <label>Pacote documental</label>
          <select value={processoId} onChange={(e) => setProcessoId(e.target.value)} disabled={!processos.length}>
            {processos.length === 0 && <option value="">Nenhum pacote encontrado</option>}
            {processos.map((processo) => (
              <option key={processo.id} value={processo.id}>
                #{processo.id} — {processo.tipo_processo} — {processo.titulo || "Sem título"}
              </option>
            ))}
          </select>
          <small>O OCR é feito sobre documentos já anexados ao pacote.</small>
        </div>
      </section>

      <section className="ocr-summary-grid">
        <div className="ocr-stat">
          <strong>{documentos.length}</strong>
          <span>Documentos no pacote</span>
        </div>
        <div className="ocr-stat">
          <strong>{extracoesProcesso.length}</strong>
          <span>Extrações registradas</span>
        </div>
        <div className="ocr-stat">
          <strong>{processoDetalhe?.tipo_processo || "-"}</strong>
          <span>Tipo do processo</span>
        </div>
        <div className="ocr-stat">
          <strong>{processoDetalhe?.vigencia_status || "-"}</strong>
          <span>Status de vigência</span>
        </div>
      </section>

      <div className="ocr-two-columns">
        <section className="ocr-card large">
          <div className="ocr-section-title">
            <h2>Documentos do pacote</h2>
            <span>{documentos.length} arquivo(s)</span>
          </div>
          {documentos.length === 0 ? (
            <p className="ocr-muted">Este pacote ainda não possui documentos vinculados, ou os documentos não foram carregados. Verifique se os arquivos foram anexados ao processo documental.</p>
          ) : (
            <div className="ocr-doc-list">
              {documentos.map((doc) => (
                <div className="ocr-doc-row" key={doc.id}>
                  <div>
                    <strong>{doc.titulo || doc.nome_arquivo_original || `Documento #${doc.id}`}</strong>
                    <small>
                      #{doc.id} · Informado: {doc.tipo_documento || "OUTRO"} · {doc.nome_arquivo_original || "arquivo"}
                    </small>
                    {ultimaExtracaoPorDocumento.get(String(doc.id)) && (
                      <small>
                        Sugerido: <b>{tipoClassificacao(ultimaExtracaoPorDocumento.get(String(doc.id))) || "-"}</b> · Confiança {confiancaClassificacao(ultimaExtracaoPorDocumento.get(String(doc.id)))}
                      </small>
                    )}
                  </div>
                  <button onClick={() => extrairDocumento(doc.id)} disabled={Boolean(processandoId)}>
                    {processandoId === doc.id ? "Extraindo..." : "Extrair OCR"}
                  </button>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="ocr-card large">
          <div className="ocr-section-title">
            <h2>Extrações do pacote</h2>
            <span>{extracoesProcesso.length} registro(s)</span>
          </div>
          {extracoesProcesso.length === 0 ? (
            <p className="ocr-muted">Nenhuma extração registrada para este pacote.</p>
          ) : (
            <div className="ocr-extraction-list">
              {extracoesProcesso.map((extracao) => (
                <button
                  key={extracao.id}
                  className={`ocr-extraction-item ${String(extracaoSelecionada?.id) === String(extracao.id) ? "active" : ""}`}
                  onClick={() => setExtracaoSelecionadaId(String(extracao.id))}
                >
                  <span>Documento #{extracao.documento_id}</span>
                  <small>{formatarDataHora(extracao.criado_em)}</small>
                  <em className={`ocr-badge ${badgeClasse(extracao.status)}`}>{extracao.status}</em>
                  <small className="ocr-extraction-classification">{tipoClassificacao(extracao) || "Sem classificação"} · {confiancaClassificacao(extracao)}</small>
                </button>
              ))}
            </div>
          )}
        </section>
      </div>

      {extracaoSelecionada && (
        <section className="ocr-result-card">
          <div className="ocr-section-title">
            <div>
              <h2>Resultado da extração</h2>
              <p>Documento #{extracaoSelecionada.documento_id} · Método {extracaoSelecionada.metodo}</p>
            </div>
            <div className="ocr-badges">
              <span className={`ocr-badge ${badgeClasse(extracaoSelecionada.status)}`}>{extracaoSelecionada.status}</span>
              <span className="ocr-badge neutral">{extracaoSelecionada.tamanho_texto || 0} caracteres</span>
            </div>
          </div>

          <div className="ocr-result-grid">
            <div className="ocr-suggestions">
              <h3>Classificação documental</h3>
              <div className="ocr-classification-box">
                <div>
                  <span>Tipo sugerido</span>
                  <strong>{tipoClassificacao(extracaoSelecionada) || "Não identificado"}</strong>
                </div>
                <div>
                  <span>Confiança</span>
                  <strong>{confiancaClassificacao(extracaoSelecionada)}</strong>
                </div>
                <div>
                  <span>Origem</span>
                  <strong>{classificacaoManual(extracaoSelecionada) ? "Manual" : "Automática"}</strong>
                </div>
              </div>

              <div className="ocr-manual-classification">
                <label>Reclassificar manualmente</label>
                <select value={classificacaoManualTipo} onChange={(e) => setClassificacaoManualTipo(e.target.value)}>
                  <option value="">Selecione</option>
                  {(opcoes?.tipos_documentais_classificacao || []).map((tipo) => (
                    <option key={tipo} value={tipo}>{tipo}</option>
                  ))}
                </select>
                <textarea
                  value={classificacaoManualObs}
                  onChange={(e) => setClassificacaoManualObs(e.target.value)}
                  placeholder="Observação da reclassificação manual"
                />
                <button onClick={salvarReclassificacaoManual} disabled={!classificacaoManualTipo}>Salvar reclassificação</button>
              </div>

              <h3>Campos sugeridos</h3>
              <div className="ocr-suggestion-table">
                {Object.entries(extracaoSelecionada.campos_sugeridos || {}).length === 0 ? (
                  <p className="ocr-muted">Nenhum campo sugerido identificado.</p>
                ) : (
                  Object.entries(extracaoSelecionada.campos_sugeridos || {}).map(([campo, valor]) => (
                    <div className="ocr-suggestion-row" key={campo}>
                      <span>{campo.replaceAll("_", " ")}</span>
                      <strong>{valorLegivel(valor)}</strong>
                    </div>
                  ))
                )}
              </div>
              <div className="ocr-warning-box">
                Estes dados não atualizam automaticamente paciente, processo, vigência, agenda ou WhatsApp. Use apenas como apoio à conferência.
              </div>
            </div>

            <div className="ocr-text-box">
              <h3>Texto extraído</h3>
              <pre>{extracaoSelecionada.texto_extraido || "Nenhum texto extraído."}</pre>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
