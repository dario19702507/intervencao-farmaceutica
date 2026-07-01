import BuscaBase from "./BuscaBase.jsx";

function normalizar(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.medicamentos)) return payload.medicamentos;
  if (Array.isArray(payload?.items)) return payload.items;
  return [];
}

function labelMedicamento(m) {
  return m?.descricao_completa
    || [m?.farmaco || m?.principio_ativo || m?.nome_comercial, m?.concentracao, m?.forma_farmaceutica].filter(Boolean).join(" · ")
    || `Medicamento ${m?.id || ""}`;
}

export default function BuscaMedicamento({
  endpoint = "/medicamentos/buscar",
  label = "Medicamento",
  placeholder = "Buscar medicamento por princípio ativo, nome ou apresentação",
  onSelect,
  onClear,
  selectedLabel,
  limit = 20,
  disabled = false,
}) {
  return (
    <BuscaBase
      label={label}
      endpoint={endpoint}
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
