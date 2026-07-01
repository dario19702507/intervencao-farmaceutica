import { useEffect, useId, useMemo, useRef, useState } from "react";
import { api } from "../../api/api";
import "./busca.css";

function defaultNormalize(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.items)) return payload.items;
  if (Array.isArray(payload?.pacientes)) return payload.pacientes;
  if (Array.isArray(payload?.medicamentos)) return payload.medicamentos;
  if (Array.isArray(payload?.resultados)) return payload.resultados;
  return [];
}

export default function BuscaBase({
  label,
  id,
  name,
  ariaLabel,
  placeholder = "Digite para buscar...",
  endpoint,
  minChars = 3,
  debounceMs = 400,
  limit = 30,
  paramName = "termo",
  extraParams = {},
  normalizeResults = defaultNormalize,
  renderItem,
  getItemLabel,
  onSelect,
  onClear,
  disabled = false,
  className = "",
  selectedLabel = "",
  emptyMessage = "Nenhum resultado encontrado.",
}) {
  const [termo, setTermo] = useState("");
  const [resultados, setResultados] = useState([]);
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState("");
  const [selecionado, setSelecionado] = useState(selectedLabel || "");
  const reqId = useRef(0);
  const reactId = useId();
  const inputId = id || `busca-${reactId.replace(/:/g, "")}`;
  const inputName = name || inputId;
  const listboxId = `${inputId}-resultados`;
  const labelTexto = ariaLabel || label || placeholder || "Campo de busca";

  useEffect(() => {
    setSelecionado(selectedLabel || "");
  }, [selectedLabel]);

  const podeBuscar = useMemo(() => termo.trim().length >= minChars, [termo, minChars]);

  useEffect(() => {
    if (!endpoint || disabled) return;
    const busca = termo.trim();
    if (busca.length < minChars) {
      setResultados([]);
      setErro("");
      setLoading(false);
      return;
    }

    const id = ++reqId.current;
    const timer = setTimeout(async () => {
      try {
        setLoading(true);
        setErro("");
        const response = await api.get(endpoint, {
          params: {
            ...extraParams,
            [paramName]: busca,
            limit,
            limite: limit,
          },
        });
        if (id !== reqId.current) return;
        setResultados(normalizeResults(response.data));
      } catch (error) {
        if (id !== reqId.current) return;
        console.warn("Erro na busca.", error.response?.data || error);
        setErro("Não foi possível realizar a busca.");
        setResultados([]);
      } finally {
        if (id === reqId.current) setLoading(false);
      }
    }, debounceMs);

    return () => clearTimeout(timer);
  }, [termo, endpoint, disabled, debounceMs, minChars, limit, paramName, JSON.stringify(extraParams)]);

  function selecionar(item) {
    const texto = getItemLabel ? getItemLabel(item) : String(item?.nome || item?.descricao_completa || item?.farmaco || item?.id || "Selecionado");
    setSelecionado(texto);
    setTermo("");
    setResultados([]);
    onSelect?.(item);
  }

  function limpar() {
    setTermo("");
    setSelecionado("");
    setResultados([]);
    setErro("");
    onClear?.();
  }

  return (
    <div className={`busca-base ${className}`.trim()}>
      {label && <label className="busca-base-label" htmlFor={inputId}>{label}</label>}
      {selecionado && (
        <div className="busca-selecionado">
          <span>{selecionado}</span>
          <button type="button" onClick={limpar} disabled={disabled} aria-label={`Trocar ${labelTexto}`}>Trocar</button>
        </div>
      )}
      {!selecionado && (
        <>
          <input
            id={inputId}
            name={inputName}
            type="search"
            className="input busca-base-input"
            value={termo}
            disabled={disabled}
            placeholder={placeholder}
            onChange={(e) => setTermo(e.target.value)}
            autoComplete="off"
            autoCorrect="off"
            autoCapitalize="none"
            spellCheck={false}
            aria-label={labelTexto}
            aria-expanded={resultados.length > 0}
            aria-controls={listboxId}
            aria-haspopup="listbox"
            role="combobox"
          />
          {termo && !podeBuscar && (
            <p className="muted busca-ajuda">Digite pelo menos {minChars} caracteres.</p>
          )}
          {loading && <p className="muted busca-ajuda">Buscando...</p>}
          {erro && <p className="muted busca-erro">{erro}</p>}
          {podeBuscar && !loading && resultados.length === 0 && !erro && (
            <p className="muted busca-ajuda">{emptyMessage}</p>
          )}
          {resultados.length > 0 && (
            <div id={listboxId} className="busca-resultados" role="listbox" aria-label={`Resultados para ${labelTexto}`}>
              {resultados.map((item) => (
                <button
                  type="button"
                  className="busca-resultado-item"
                  key={item.id || `${getItemLabel?.(item)}-${Math.random()}`}
                  onClick={() => selecionar(item)}
                  role="option"
                  aria-selected="false"
                >
                  {renderItem ? renderItem(item) : (getItemLabel ? getItemLabel(item) : item.nome || item.descricao_completa || item.farmaco)}
                </button>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
