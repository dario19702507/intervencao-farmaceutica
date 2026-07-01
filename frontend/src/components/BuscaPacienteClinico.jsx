import { useEffect, useMemo, useState } from "react";
import { api } from "../api/api";
import "./BuscaPacienteClinico.css";

const MIN_BUSCA = 3;
const LIMITE_PADRAO = 30;

function normalizarPacientes(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.pacientes)) return payload.pacientes;
  if (Array.isArray(payload?.items)) return payload.items;
  return [];
}

function nomePaciente(paciente) {
  if (!paciente) return "";
  return paciente.nome || paciente.nome_completo || paciente.paciente_nome || `Paciente #${paciente.id}`;
}

function documentoPaciente(paciente) {
  const partes = [];
  if (paciente?.cpf) partes.push(`CPF ${paciente.cpf}`);
  if (paciente?.cns) partes.push(`CNS ${paciente.cns}`);
  if (paciente?.telefone) partes.push(paciente.telefone);
  return partes.join(" · ");
}

export default function BuscaPacienteClinico({
  label = "Paciente clínico",
  value = "",
  selectedPaciente = null,
  onSelect,
  placeholder = "Buscar por nome, CPF, CNS ou telefone",
  disabled = false,
  required = false,
  limite = LIMITE_PADRAO,
  className = "",
}) {
  const [termo, setTermo] = useState("");
  const [resultados, setResultados] = useState([]);
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState("");
  const [buscaExecutada, setBuscaExecutada] = useState(false);

  const nomeSelecionado = useMemo(() => nomePaciente(selectedPaciente), [selectedPaciente]);

  useEffect(() => {
    if (!value) {
      setTermo("");
      setResultados([]);
      setBuscaExecutada(false);
    }
  }, [value]);

  useEffect(() => {
    const busca = termo.trim();

    if (busca.length < MIN_BUSCA) {
      setResultados([]);
      setErro("");
      setBuscaExecutada(false);
      return;
    }

    const timer = window.setTimeout(async () => {
      setLoading(true);
      setErro("");
      setBuscaExecutada(true);
      try {
        const response = await api.get("/consultorio/pacientes-clinicos/buscar", {
          params: { termo: busca, limit: limite },
        });
        setResultados(normalizarPacientes(response.data));
      } catch (error) {
        console.warn("Erro ao buscar pacientes clínicos.", error.response?.data || error);
        setResultados([]);
        setErro("Não foi possível buscar pacientes clínicos.");
      } finally {
        setLoading(false);
      }
    }, 350);

    return () => window.clearTimeout(timer);
  }, [termo, limite]);

  function selecionar(paciente) {
    setTermo(nomePaciente(paciente));
    setResultados([]);
    setBuscaExecutada(false);
    if (onSelect) onSelect(paciente);
  }

  function limparSelecao() {
    setTermo("");
    setResultados([]);
    setBuscaExecutada(false);
    if (onSelect) onSelect(null);
  }

  return (
    <div className={`busca-paciente-clinico ${className}`.trim()}>
      {label && <label className="busca-paciente-label">{label}{required ? " *" : ""}</label>}
      <div className="busca-paciente-input-row">
        <input
          className="input busca-paciente-input"
          value={termo}
          disabled={disabled}
          placeholder={placeholder}
          onChange={(e) => setTermo(e.target.value)}
        />
        {value && (
          <button type="button" className="secondary-button busca-paciente-clear" onClick={limparSelecao} disabled={disabled}>
            Limpar
          </button>
        )}
      </div>

      {nomeSelecionado && (
        <p className="busca-paciente-selecionado">Selecionado: <strong>{nomeSelecionado}</strong></p>
      )}
      {termo.trim().length > 0 && termo.trim().length < MIN_BUSCA && (
        <p className="busca-paciente-ajuda">Digite pelo menos {MIN_BUSCA} caracteres para pesquisar.</p>
      )}
      {loading && <p className="busca-paciente-ajuda">Buscando pacientes...</p>}
      {erro && <p className="busca-paciente-erro">{erro}</p>}

      {!loading && buscaExecutada && resultados.length === 0 && !erro && (
        <p className="busca-paciente-ajuda">Nenhum paciente encontrado.</p>
      )}

      {resultados.length > 0 && (
        <div className="busca-paciente-resultados">
          {resultados.map((paciente) => (
            <button
              type="button"
              key={paciente.id}
              className="busca-paciente-resultado"
              onClick={() => selecionar(paciente)}
            >
              <span>{nomePaciente(paciente)}</span>
              {documentoPaciente(paciente) && <small>{documentoPaciente(paciente)}</small>}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
