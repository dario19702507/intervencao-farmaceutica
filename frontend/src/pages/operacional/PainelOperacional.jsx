import { useEffect, useState } from "react";
import { api } from "../../api/api";
import "./PainelOperacional.css";

function formatarData(data) {
  if (!data) return "-";
  const d = new Date(`${data}T00:00:00`);
  if (Number.isNaN(d.getTime())) return data;
  return d.toLocaleDateString("pt-BR");
}

function badgeClasse(valor) {
  const v = (valor || "").toString().toUpperCase();
  if (v.includes("URGENTE") || v.includes("VENC") || v.includes("REJEITADO") || v.includes("ATRAS")) return "danger";
  if (v.includes("IMPORTANTE") || v.includes("INCOMPLETO") || v.includes("PENDENTE") || v.includes("AGUARDANDO")) return "warning";
  if (v.includes("COMPLETO") || v.includes("VALIDADO") || v.includes("REALIZADO")) return "success";
  return "neutral";
}

function Lista({ titulo, subtitulo, itens, render }) {
  return (
    <section className="op-panel">
      <div className="op-panel-header">
        <div>
          <h2>{titulo}</h2>
          {subtitulo && <p>{subtitulo}</p>}
        </div>
        <span className="op-count">{itens?.length || 0}</span>
      </div>
      <div className="op-list">
        {(!itens || itens.length === 0) && <p className="op-empty">Nenhum item para exibir.</p>}
        {(itens || []).map((item) => render(item))}
      </div>
    </section>
  );
}

export default function PainelOperacional() {
  const [dados, setDados] = useState(null);
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState("");

  async function carregar() {
    setLoading(true);
    setErro("");
    try {
      const resp = await api.get("/consultorio/painel-operacional");
      setDados(resp.data || null);
    } catch (e) {
      console.error(e);
      setErro("Não foi possível carregar o painel operacional. Verifique se o backend está ativo.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    carregar();
  }, []);

  const resumo = dados?.resumo || {};
  const listas = dados?.listas || {};

  const cards = [
    ["Retiradas hoje", resumo.retiradas_hoje, "neutral"],
    ["Retiradas atrasadas", resumo.retiradas_atrasadas, "danger"],
    ["Laudos vencendo", resumo.laudos_vencendo_60_dias, "warning"],
    ["Laudos vencidos", resumo.laudos_vencidos, "danger"],
    ["Processos incompletos", resumo.processos_incompletos, "warning"],
    ["Documentos rejeitados", resumo.documentos_rejeitados, "danger"],
    ["Notificações urgentes", resumo.notificacoes_urgentes, "danger"],
    ["WhatsApp pendentes", resumo.whatsapp_pendentes, "warning"],
  ];

  return (
    <div className="painel-op-page">
      <div className="painel-op-header">
        <div>
          <p className="op-eyebrow">Rotina da Farmácia Escola</p>
          <h1>Painel Operacional</h1>
          <p>Retiradas, vencimentos, processos incompletos, documentos rejeitados e pendências em uma visão única.</p>
          {dados?.data_referencia && <small>Data de referência: {formatarData(dados.data_referencia)}</small>}
        </div>
        <button className="op-btn" onClick={carregar} disabled={loading}>{loading ? "Atualizando..." : "Atualizar"}</button>
      </div>

      {erro && <div className="op-alert error">{erro}</div>}

      <section className="op-cards">
        {cards.map(([label, valor, tipo]) => (
          <div key={label} className={`op-card ${tipo}`}>
            <span>{label}</span>
            <strong>{valor ?? 0}</strong>
          </div>
        ))}
      </section>

      <section className="op-grid">
        <Lista
          titulo="Retiradas atrasadas"
          subtitulo="Pacientes com retirada pendente após a data prevista."
          itens={listas.retiradas_atrasadas}
          render={(item) => (
            <article key={item.id} className="op-item">
              <div>
                <strong>{item.paciente_nome || "Paciente não informado"}</strong>
                <span>{item.medicamento || item.titulo || "Retirada"}</span>
              </div>
              <div className="op-item-meta">
                <span>{formatarData(item.data_evento)}</span>
                <b className={`op-badge ${badgeClasse(item.prioridade)}`}>{item.prioridade || "NORMAL"}</b>
              </div>
            </article>
          )}
        />

        <Lista
          titulo="Laudos vencendo em 60 dias"
          subtitulo="Processos com vigência próxima do fim."
          itens={listas.laudos_vencendo}
          render={(item) => (
            <article key={item.id} className="op-item">
              <div>
                <strong>{item.paciente_nome || `Paciente #${item.paciente_id}`}</strong>
                <span>{item.titulo || item.tipo_processo}</span>
              </div>
              <div className="op-item-meta">
                <span>Vence: {formatarData(item.vigencia_fim)}</span>
                <b className={`op-badge ${badgeClasse(item.prioridade)}`}>{item.prioridade || "NORMAL"}</b>
              </div>
            </article>
          )}
        />

        <Lista
          titulo="Laudos vencidos"
          subtitulo="Vigências encerradas que ainda exigem acompanhamento."
          itens={listas.laudos_vencidos}
          render={(item) => (
            <article key={item.id} className="op-item">
              <div>
                <strong>{item.paciente_nome || `Paciente #${item.paciente_id}`}</strong>
                <span>{item.titulo || item.tipo_processo}</span>
              </div>
              <div className="op-item-meta">
                <span>Venceu: {formatarData(item.vigencia_fim)}</span>
                <b className="op-badge danger">URGENTE</b>
              </div>
            </article>
          )}
        />

        <Lista
          titulo="Processos documentais incompletos"
          subtitulo="Documentos obrigatórios ainda não validados."
          itens={listas.processos_incompletos}
          render={(item) => (
            <article key={item.id} className="op-item tall">
              <div>
                <strong>{item.paciente_nome || `Paciente #${item.paciente_id}`}</strong>
                <span>{item.titulo || item.tipo_processo}</span>
                <div className="op-tags">
                  {(item.documentos_pendentes || []).map((doc) => <em key={doc}>{doc}</em>)}
                </div>
              </div>
              <div className="op-item-meta">
                <b className="op-badge warning">INCOMPLETO</b>
              </div>
            </article>
          )}
        />

        <Lista
          titulo="Documentos rejeitados"
          subtitulo="Pendências documentais exigem avaliação humana; WhatsApp permanece manual."
          itens={listas.documentos_rejeitados}
          render={(item) => (
            <article key={item.id} className="op-item tall">
              <div>
                <strong>{item.paciente_nome || `Paciente #${item.paciente_id}`}</strong>
                <span>{item.tipo_documento} · {item.nome_arquivo_original}</span>
                {item.status_documental_motivo && <small>{item.status_documental_motivo}</small>}
              </div>
              <div className="op-item-meta">
                <b className="op-badge danger">REJEITADO</b>
              </div>
            </article>
          )}
        />

        <Lista
          titulo="Eventos de hoje"
          subtitulo="Atividades operacionais previstas para a data de referência."
          itens={listas.eventos_hoje}
          render={(item) => (
            <article key={item.id} className="op-item">
              <div>
                <strong>{item.paciente_nome || "Paciente não informado"}</strong>
                <span>{item.tipo_evento} · {item.medicamento || item.titulo || "Evento"}</span>
              </div>
              <div className="op-item-meta">
                <b className={`op-badge ${badgeClasse(item.prioridade)}`}>{item.prioridade || "NORMAL"}</b>
              </div>
            </article>
          )}
        />
      </section>

      {dados?.regras && (
        <section className="op-panel rules">
          <h2>Regras operacionais aplicadas</h2>
          <p>{dados.regras.documentos}</p>
          <p>{dados.regras.whatsapp_documental}</p>
          <p>{dados.regras.agenda}</p>
        </section>
      )}
    </div>
  );
}
