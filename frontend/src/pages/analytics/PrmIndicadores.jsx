import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, CheckCircle2, Clock3, ListChecks, ShieldAlert, UsersRound } from "lucide-react";
import { api } from "../../api/api";

function normalizarLista(valor) {
  if (!valor) return [];
  if (Array.isArray(valor)) return valor;
  if (typeof valor === "object") {
    return Object.entries(valor).map(([chave, total]) => ({ chave, label: chave, total }));
  }
  return [];
}

function pegarPrimeiroObjeto(dados, chaves) {
  for (const chave of chaves) {
    if (dados && typeof dados[chave] === "object" && dados[chave] !== null) return dados[chave];
  }
  return {};
}

function pegarPrimeiraLista(dados, chaves) {
  for (const chave of chaves) {
    const lista = normalizarLista(dados?.[chave]);
    if (lista.length) return lista;
  }
  return [];
}

function totalItem(item) {
  return item?.total ?? item?.quantidade ?? item?.count ?? item?.valor ?? 0;
}

function labelItem(item) {
  return item?.label || item?.nome || item?.categoria || item?.criticidade || item?.status || item?.natureza || item?.subcategoria || item?.chave || "Não informado";
}

function percentual(valor) {
  const n = Number(valor || 0);
  if (!Number.isFinite(n)) return "0%";
  return `${n.toFixed(1).replace(".0", "")}%`;
}

function CardIndicador({ icone: Icon, titulo, valor, descricao, destaque }) {
  return (
    <article className={`prm-card ${destaque ? "destaque" : ""}`}>
      <div className="prm-card-icon"><Icon size={20} /></div>
      <div>
        <span>{titulo}</span>
        <strong>{valor ?? 0}</strong>
        {descricao ? <small>{descricao}</small> : null}
      </div>
    </article>
  );
}

function BlocoDistribuicao({ titulo, dados, vazio = "Sem dados estruturados." }) {
  return (
    <section className="prm-distribuicao-card">
      <h4>{titulo}</h4>
      {dados.length === 0 ? (
        <p className="muted-text">{vazio}</p>
      ) : (
        <div className="prm-distribuicao-lista">
          {dados.map((item, index) => (
            <div key={`${titulo}-${labelItem(item)}-${index}`} className="prm-distribuicao-item">
              <span>{labelItem(item)}</span>
              <strong>{totalItem(item)}</strong>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function LinhaPrioritaria({ item }) {
  const paciente = item?.paciente_nome || item?.nome_paciente || item?.paciente || "Paciente não informado";
  const categoria = item?.categoria || item?.categoria_prm || "PRM";
  const criticidade = item?.criticidade || item?.criticidade_prm || "Não informada";
  const status = item?.status || item?.status_prm || "Não informado";
  const dias = item?.dias_aberto ?? item?.dias_em_aberto ?? item?.dias ?? "-";
  const descricao = item?.descricao || item?.descricao_clinica || item?.subcategoria || item?.tipo || "Sem descrição resumida";

  return (
    <tr>
      <td>{paciente}</td>
      <td>{categoria}</td>
      <td><span className={`prm-badge ${String(criticidade).toLowerCase()}`}>{criticidade}</span></td>
      <td>{status}</td>
      <td>{dias}</td>
      <td>{descricao}</td>
    </tr>
  );
}

export default function PrmIndicadores() {
  const [dados, setDados] = useState(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState("");

  useEffect(() => {
    let ativo = true;

    async function carregar() {
      setCarregando(true);
      setErro("");
      try {
        const response = await api.get("/consultorio/cuidado/prm-indicadores");
        if (ativo) setDados(response.data || {});
      } catch (error) {
        if (ativo) {
          setErro("Não foi possível carregar os indicadores de PRM.");
          console.warn("Indicadores PRM indisponíveis", error.response?.data || error);
        }
      } finally {
        if (ativo) setCarregando(false);
      }
    }

    carregar();
    return () => { ativo = false; };
  }, []);

  const indicadores = useMemo(() => {
    const base = pegarPrimeiroObjeto(dados, ["indicadores", "resumo", "totais", "dashboard"]);
    return {
      total: dados?.total_prm ?? base.total_prm ?? base.total ?? 0,
      criticos: dados?.prm_criticos_abertos ?? base.prm_criticos_abertos ?? base.criticos_abertos ?? base.criticos ?? 0,
      abertos30: dados?.prm_abertos_mais_30_dias ?? base.prm_abertos_mais_30_dias ?? base.abertos_30_dias ?? base.abertos_mais_30 ?? 0,
      abertos60: dados?.prm_abertos_mais_60_dias ?? base.prm_abertos_mais_60_dias ?? base.abertos_60_dias ?? base.abertos_mais_60 ?? 0,
      pacientesPrioritarios: dados?.pacientes_prioritarios_total ?? base.pacientes_prioritarios_total ?? base.pacientes_prioritarios ?? 0,
      taxaResolucao: dados?.taxa_resolucao ?? base.taxa_resolucao ?? 0,
      taxaPadronizacao: dados?.taxa_padronizacao ?? base.taxa_padronizacao ?? 0,
    };
  }, [dados]);

  const porCategoria = pegarPrimeiraLista(dados, ["por_categoria", "prm_por_categoria", "categorias"]);
  const porCriticidade = pegarPrimeiraLista(dados, ["por_criticidade", "prm_por_criticidade", "criticidades"]);
  const porNatureza = pegarPrimeiraLista(dados, ["por_natureza", "prm_por_natureza", "naturezas"]);
  const porStatus = pegarPrimeiraLista(dados, ["por_status", "prm_por_status", "status"]);
  const porDesfecho = pegarPrimeiraLista(dados, ["por_desfecho", "prm_por_desfecho", "desfechos"]);
  const pacientesPrioritarios = pegarPrimeiraLista(dados, ["pacientes_prioritarios", "prioritarios", "fila_prioritaria", "pendencias_prm"]);

  if (carregando) {
    return <div className="prm-indicadores loading-card">Carregando indicadores de PRM...</div>;
  }

  if (erro) {
    return <div className="prm-indicadores error-card">{erro}</div>;
  }

  return (
    <div className="prm-indicadores">
      <header className="prm-indicadores-header">
        <div>
          <p className="workspace-eyebrow">Indicadores Assistenciais</p>
          <h3>Problemas Relacionados a Medicamentos</h3>
          <p>
            Distribuição, criticidade, resolução e fila prioritária de PRM com base no catálogo padronizado.
          </p>
        </div>
      </header>

      <section className="prm-cards-grid">
        <CardIndicador icone={ListChecks} titulo="Total de PRM" valor={indicadores.total} descricao="Registros analisados" />
        <CardIndicador icone={ShieldAlert} titulo="Críticos abertos" valor={indicadores.criticos} descricao="Prioridade clínica" destaque />
        <CardIndicador icone={Clock3} titulo="Abertos >30 dias" valor={indicadores.abertos30} descricao="Acompanhamento pendente" />
        <CardIndicador icone={AlertTriangle} titulo="Abertos >60 dias" valor={indicadores.abertos60} descricao="Risco de atraso" destaque />
        <CardIndicador icone={UsersRound} titulo="Pacientes prioritários" valor={indicadores.pacientesPrioritarios} descricao="Fila clínica" />
        <CardIndicador icone={CheckCircle2} titulo="Taxa de resolução" valor={percentual(indicadores.taxaResolucao)} descricao={`Padronização: ${percentual(indicadores.taxaPadronizacao)}`} />
      </section>

      <section className="prm-distribuicoes-grid">
        <BlocoDistribuicao titulo="PRM por categoria" dados={porCategoria} />
        <BlocoDistribuicao titulo="PRM por criticidade" dados={porCriticidade} />
        <BlocoDistribuicao titulo="PRM por natureza" dados={porNatureza} />
        <BlocoDistribuicao titulo="PRM por status" dados={porStatus} />
        <BlocoDistribuicao titulo="PRM por desfecho" dados={porDesfecho} />
      </section>

      <section className="prm-tabela-card">
        <div className="prm-tabela-header">
          <h4>Pacientes prioritários e pendências de PRM</h4>
          <span>Ordene a atuação clínica por criticidade e tempo em aberto.</span>
        </div>
        {pacientesPrioritarios.length === 0 ? (
          <p className="muted-text">Nenhum paciente prioritário identificado pelos critérios atuais.</p>
        ) : (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Paciente</th>
                  <th>Categoria</th>
                  <th>Criticidade</th>
                  <th>Status</th>
                  <th>Dias</th>
                  <th>Resumo</th>
                </tr>
              </thead>
              <tbody>
                {pacientesPrioritarios.map((item, index) => (
                  <LinhaPrioritaria key={`prioritario-${index}`} item={item} />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
