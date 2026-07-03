import BuscaBase from "./BuscaBase.jsx";

function normalizar(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.medicamentos)) return payload.medicamentos;
  if (Array.isArray(payload?.items)) return payload.items;
  return [];
}

export function labelMedicamento(m) {
  return m?.descricao_completa
    || [
      m?.farmaco || m?.principio_ativo || m?.nome_comercial,
      m?.concentracao,
      m?.forma_farmaceutica,
      m?.via_administracao,
    ].filter(Boolean).join(" · ")
    || `Medicamento ${m?.id || ""}`;
}

export function aplicarMedicamentoEmFormulario(medicamento, atual = {}) {
  const descricao = labelMedicamento(medicamento);
  return {
    ...atual,
    catalogo_medicamento_id: medicamento?.id || "",
    nome_medicamento: descricao || atual.nome_medicamento || "",
    dose: atual.dose || medicamento?.concentracao || medicamento?.apresentacao || "",
    via: atual.via || medicamento?.via_administracao || "",
  };
}

export default function BuscaMedicamento({
  endpoint = "/medicamentos/buscar",
  label = "Medicamento",
  id,
  name,
  ariaLabel = "Pesquisar medicamento",
  placeholder = "Buscar medicamento por princípio ativo, nome ou apresentação",
  onSelect,
  onClear,
  selectedLabel,
  limit = 20,
  disabled = false,
  paramName,
  extraParams = {},
}) {
  const paramNameFinal = paramName || (endpoint.includes("catalogo-medicamentos") ? "busca" : "termo");

  return (
    <BuscaBase
      label={label}
      id={id}
      name={name}
      ariaLabel={ariaLabel}
      endpoint={endpoint}
      paramName={paramNameFinal}
      extraParams={{ ativo: true, ...extraParams }}
      placeholder={placeholder}
      normalizeResults={normalizar}
      getItemLabel={labelMedicamento}
      renderItem={(m) => (
        <span>
          <strong>{labelMedicamento(m)}</strong>
          <small>{[m.classe_terapeutica, m.via_administracao, m.registro_anvisa].filter(Boolean).join(" · ")}</small>
        </span>
      )}
      onSelect={onSelect}
      onClear={onClear}
      selectedLabel={selectedLabel}
      limit={limit}
      disabled={disabled}
    />
  );
}
