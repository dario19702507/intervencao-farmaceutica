import BuscaBase from "./BuscaBase.jsx";

function normalizar(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.pacientes)) return payload.pacientes;
  if (Array.isArray(payload?.items)) return payload.items;
  return [];
}

function labelPaciente(p) {
  const nome = p?.nome || p?.nome_completo || `Paciente ${p?.id || ""}`;
  const doc = p?.cpf || p?.cns || p?.telefone || p?.telefone_celular || "";
  return doc ? `${nome} · ${doc}` : nome;
}

export default function BuscaPaciente({
  tipo = "clinico",
  endpoint,
  label = "Paciente",
  placeholder = "Buscar por nome, CPF, CNS ou telefone",
  onSelect,
  onClear,
  selectedLabel,
  limit = 30,
  disabled = false,
}) {
  const endpointFinal = endpoint || (tipo === "simplificado"
    ? "/consultorio/pacientes-simplificados/buscar"
    : tipo === "ceaf"
      ? "/ceaf/pacientes"
      : "/consultorio/pacientes-clinicos/buscar");

  return (
    <BuscaBase
      label={label}
      endpoint={endpointFinal}
      placeholder={placeholder}
      normalizeResults={normalizar}
      getItemLabel={labelPaciente}
      renderItem={(p) => (
        <span>
          <strong>{p.nome || p.nome_completo || `Paciente ${p.id}`}</strong>
          <small>{[p.cpf, p.cns, p.telefone || p.telefone_celular, p.medicamento_prescrito].filter(Boolean).join(" · ")}</small>
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
