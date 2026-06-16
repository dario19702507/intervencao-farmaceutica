import { useEffect, useMemo, useState } from "react";
import { api } from "../../api/api";

function mesAtual() {
  const hoje = new Date();
  return String(hoje.getMonth() + 1).padStart(2, "0");
}

function anoAtual() {
  return String(new Date().getFullYear());
}

function formatarData(data) {
  if (!data) return "-";
  return new Date(`${data}T00:00:00`).toLocaleDateString("pt-BR");
}

function formatarPeriodo(periodo) {
  if (!periodo?.inicio || !periodo?.fim) return "mês selecionado";
  return `${formatarData(periodo.inicio)} a ${formatarData(periodo.fim)}`;
}

export default function ConciliacaoCeaf() {
  const [ano, setAno] = useState(anoAtual());
  const [mes, setMes] = useState(mesAtual());
  const [resumo, setResumo] = useState(null);
  const [resultado, setResultado] = useState(null);
  const [loading, setLoading] = useState(false);
  const [sincronizando, setSincronizando] = useState(false);
  const [criarPendencia, setCriarPendencia] = useState(true);

  const params = useMemo(
    () => ({ ano: Number(ano), mes: Number(mes) }),
    [ano, mes]
  );

  async function carregarResumo() {
    try {
      setLoading(true);
      const response = await api.get("/consultorio/agenda/conciliacao-ceaf/resumo", {
        params,
      });
      setResumo(response.data || null);
    } catch (error) {
      console.error("Erro ao carregar resumo da conciliação CEAF:", error);
      alert("Erro ao carregar resumo da conciliação CEAF.");
    } finally {
      setLoading(false);
    }
  }

  async function sincronizarRetiradas() {
    const confirmado = window.confirm(
      "A conciliação criará retiradas previstas para pacientes CEAF com LME vigente e sem retirada agendada ou realizada no mês selecionado. Deseja continuar?"
    );

    if (!confirmado) return;

    try {
      setSincronizando(true);
      const response = await api.post("/consultorio/agenda/conciliacao-ceaf/sincronizar", null, {
        params: {
          ...params,
          criar_pendencia_renovacao: criarPendencia,
        },
      });
      setResultado(response.data || null);
      await carregarResumo();
      alert("Conciliação CEAF concluída.");
    } catch (error) {
      console.error("Erro ao sincronizar retiradas CEAF:", error);
      alert("Erro ao sincronizar retiradas CEAF.");
    } finally {
      setSincronizando(false);
    }
  }

  useEffect(() => {
    carregarResumo();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.ano, params.mes]);

  const dados = resumo || {};
  const periodo = dados.periodo || resultado?.periodo;

  return (
    <div className="page-container conciliacao-ceaf-page">
      <div className="page-header">
        <div>
          <h2>Conciliação Mensal CEAF</h2>
          <p className="muted">
            Analisa pacientes CEAF, vigência da LME e agenda para identificar retiradas previstas, pendências e bloqueios no mês selecionado.
          </p>
        </div>

        <div className="action-buttons">
          <button className="secondary-button" onClick={carregarResumo} disabled={loading}>
            {loading ? "Atualizando..." : "Atualizar resumo"}
          </button>
          <button className="primary-button" onClick={sincronizarRetiradas} disabled={sincronizando}>
            {sincronizando ? "Sincronizando..." : "Sincronizar retiradas CEAF"}
          </button>
        </div>
      </div>

      <div className="form-card">
        <div className="section-header">
          <div>
            <h3>Período de conciliação</h3>
            <p className="muted">Selecione o mês operacional que será conferido na agenda.</p>
          </div>
        </div>

        <div className="filters-row">
          <label>
            Ano
            <input
              type="number"
              min="2024"
              max="2100"
              value={ano}
              onChange={(e) => setAno(e.target.value)}
            />
          </label>

          <label>
            Mês
            <select value={mes} onChange={(e) => setMes(e.target.value)}>
              <option value="01">Janeiro</option>
              <option value="02">Fevereiro</option>
              <option value="03">Março</option>
              <option value="04">Abril</option>
              <option value="05">Maio</option>
              <option value="06">Junho</option>
              <option value="07">Julho</option>
              <option value="08">Agosto</option>
              <option value="09">Setembro</option>
              <option value="10">Outubro</option>
              <option value="11">Novembro</option>
              <option value="12">Dezembro</option>
            </select>
          </label>

          <label className="checkbox-row inline-checkbox">
            <input
              type="checkbox"
              checked={criarPendencia}
              onChange={(e) => setCriarPendencia(e.target.checked)}
            />
            Criar pendência de renovação quando a LME estiver vencida
          </label>
        </div>

        <p className="muted">Período analisado: {formatarPeriodo(periodo)}</p>
      </div>

      <div className="cards-grid five">
        <div className="metric-card">
          <span>Pacientes CEAF ativos</span>
          <strong>{dados.pacientes_ceaf_ativos ?? 0}</strong>
        </div>
        <div className="metric-card warning">
          <span>Retiradas previstas</span>
          <strong>{dados.retiradas_previstas ?? 0}</strong>
        </div>
        <div className="metric-card">
          <span>Retiradas agendadas</span>
          <strong>{dados.retiradas_agendadas ?? 0}</strong>
        </div>
        <div className="metric-card success">
          <span>Realizadas</span>
          <strong>{dados.retiradas_realizadas ?? 0}</strong>
        </div>
        <div className="metric-card danger">
          <span>LME vencidas</span>
          <strong>{dados.lme_vencidas ?? 0}</strong>
        </div>
      </div>

      <div className="cards-grid four">
        <div className="summary-card">
          <strong>Sem retirada prevista</strong>
          <div>{dados.sem_retirada_prevista ?? 0}</div>
          <span>Pacientes elegíveis sem retirada no mês.</span>
        </div>
        <div className="summary-card agenda-atencao">
          <strong>LME vencendo em 30 dias</strong>
          <div>{dados.lme_vencendo_30_dias ?? 0}</div>
          <span>Requer acompanhamento de renovação.</span>
        </div>
        <div className="summary-card agenda-risco">
          <strong>Bloqueados por LME</strong>
          <div>{dados.bloqueados_por_lme ?? 0}</div>
          <span>Retirada não deve ser gerada sem regularização.</span>
        </div>
        <div className="summary-card">
          <strong>Faltosos/cancelados</strong>
          <div>{(dados.faltosos ?? 0) + (dados.retiradas_canceladas ?? 0)}</div>
          <span>Eventos que não devem aparecer como ativos.</span>
        </div>
      </div>

      {resultado && (
        <div className="form-card conciliacao-resultado">
          <div className="section-header">
            <div>
              <h3>Resultado da última sincronização</h3>
              <p className="muted">{resultado.mensagem || "Conciliação executada."}</p>
            </div>
          </div>

          <div className="cards-grid five">
            <div className="metric-card success">
              <span>Previstas criadas</span>
              <strong>{resultado.retiradas_previstas_criadas ?? 0}</strong>
            </div>
            <div className="metric-card">
              <span>Já existentes</span>
              <strong>{resultado.retiradas_ja_existentes ?? 0}</strong>
            </div>
            <div className="metric-card success">
              <span>Já realizadas</span>
              <strong>{resultado.retiradas_ja_realizadas ?? 0}</strong>
            </div>
            <div className="metric-card danger">
              <span>Bloqueadas</span>
              <strong>{resultado.bloqueadas_por_lme ?? 0}</strong>
            </div>
            <div className="metric-card warning">
              <span>Pendências criadas</span>
              <strong>{resultado.pendencias_renovacao_criadas ?? 0}</strong>
            </div>
          </div>

          <div className="dashboard-grid two">
            <div className="form-card compact-card">
              <h4>Exemplos de retiradas criadas</h4>
              {resultado.exemplos_criados?.length ? (
                <ul className="compact-list">
                  {resultado.exemplos_criados.map((item, index) => (
                    <li key={`${item.paciente}-${index}`}>
                      <strong>{item.paciente}</strong>
                      <span>{formatarData(item.data_evento)} · {item.medicamento || "medicamento não informado"}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="muted">Nenhum exemplo criado nesta execução.</p>
              )}
            </div>

            <div className="form-card compact-card">
              <h4>Exemplos bloqueados</h4>
              {resultado.exemplos_bloqueados?.length ? (
                <ul className="compact-list">
                  {resultado.exemplos_bloqueados.map((item, index) => (
                    <li key={`${item.paciente}-${index}`}>
                      <strong>{item.paciente}</strong>
                      <span>{item.motivo} · Vigência: {formatarData(item.data_fim_vigencia)}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="muted">Nenhum exemplo bloqueado nesta execução.</p>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="form-card">
        <h3>Como interpretar a conciliação</h3>
        <p className="muted">
          A sincronização não apaga agendamentos e não duplica retiradas. Ela cria apenas o status <strong>retirada prevista</strong> para pacientes com LME vigente e sem retirada agendada ou realizada no mês. Pacientes com LME vencida são bloqueados para retirada e podem receber pendência de renovação.
        </p>
      </div>
    </div>
  );
}
