import { useMemo, useState } from "react";

function normalizarTexto(valor) {
  return String(valor || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

export function labelMedicamentoUso(medicamento) {
  if (!medicamento) return "";
  return [
    medicamento.nome_medicamento,
    medicamento.dose,
    medicamento.via,
    medicamento.frequencia_uso || medicamento.frequencia,
  ].filter(Boolean).join(" · ") || `Medicamento ${medicamento.id || ""}`;
}

export default function BuscaMedicamentoUso({
  id = "busca-medicamento-uso",
  name = "buscaMedicamentoUso",
  label = "Medicamento em uso",
  placeholder = "Buscar medicamento em uso",
  medicamentos = [],
  value = "",
  onSelect,
  ajuda = "Busque entre os medicamentos já registrados na farmacoterapia do paciente.",
  minLength = 2,
  limit = 20,
  disabled = false,
}) {
  const [busca, setBusca] = useState("");

  const selecionado = useMemo(
    () => medicamentos.find((m) => String(m.id) === String(value)),
    [medicamentos, value]
  );

  const resultados = useMemo(() => {
    const termo = normalizarTexto(busca);
    if (termo.length < minLength) return [];

    return medicamentos
      .filter((m) => {
        const alvo = normalizarTexto([
          m.nome_medicamento,
          m.dose,
          m.via,
          m.frequencia_uso,
          m.frequencia,
          m.indicacao,
          m.status_farmacoterapia,
        ].filter(Boolean).join(" "));
        return alvo.includes(termo);
      })
      .slice(0, limit);
  }, [busca, medicamentos, minLength, limit]);

  const listboxId = `${id}-resultados`;

  function selecionar(medicamento) {
    onSelect?.(medicamento || null);
    setBusca("");
  }

  return (
    <div className="busca-base busca-medicamento-uso">
      <label className="busca-base-label" htmlFor={id}>{label}</label>

      {selecionado ? (
        <div className="busca-selecionado">
          <span>{labelMedicamentoUso(selecionado)}</span>
          <button type="button" onClick={() => selecionar(null)} disabled={disabled}>
            Limpar
          </button>
        </div>
      ) : (
        <>
          <input
            id={id}
            name={name}
            type="search"
            className="input busca-base-input"
            placeholder={placeholder}
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
            disabled={disabled}
            autoComplete="off"
            autoCorrect="off"
            autoCapitalize="none"
            spellCheck={false}
            aria-label={label}
            role="combobox"
            aria-expanded={resultados.length > 0}
            aria-controls={listboxId}
            aria-haspopup="listbox"
          />

          {busca.trim().length > 0 && busca.trim().length < minLength && (
            <p className="muted busca-ajuda">Digite pelo menos {minLength} caracteres.</p>
          )}

          {!busca && ajuda && <p className="muted busca-ajuda">{ajuda}</p>}

          {resultados.length > 0 && (
            <div id={listboxId} className="busca-resultados" role="listbox">
              {resultados.map((m) => (
                <button
                  key={m.id}
                  type="button"
                  className="busca-resultado-item"
                  role="option"
                  onClick={() => selecionar(m)}
                >
                  <span>
                    <strong>{m.nome_medicamento || `Medicamento ${m.id}`}</strong>
                    <small>{[m.dose, m.via, m.frequencia_uso || m.frequencia, m.status_farmacoterapia].filter(Boolean).join(" · ")}</small>
                  </span>
                </button>
              ))}
            </div>
          )}

          {busca.trim().length >= minLength && resultados.length === 0 && (
            <p className="muted busca-ajuda">Nenhum medicamento em uso encontrado para a busca.</p>
          )}
        </>
      )}
    </div>
  );
}
