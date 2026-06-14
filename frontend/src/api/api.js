import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const MUTATION_METHODS = new Set(["post", "put", "patch", "delete"]);
const pendingMutations = new Map();

function buildMutationKey(config) {
  const method = (config.method || "get").toLowerCase();
  const url = `${config.baseURL || ""}${config.url || ""}`;
  const params = config.params ? JSON.stringify(config.params) : "";
  const data = typeof config.data === "string" ? config.data : JSON.stringify(config.data || {});
  return `${method}:${url}:${params}:${data}`;
}

function createRequestId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export const api = axios.create({
  baseURL: API_URL,
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    const method = (config.method || "get").toLowerCase();

    if (MUTATION_METHODS.has(method)) {
      const key = buildMutationKey(config);

      if (pendingMutations.has(key)) {
        throw new axios.CanceledError(
          "Solicitação duplicada bloqueada: aguarde a conclusão do salvamento anterior."
        );
      }

      config.__mutationKey = key;
      pendingMutations.set(key, Date.now());
      config.headers["X-Request-ID"] = createRequestId();
    }

    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => {
    const key = response.config?.__mutationKey;
    if (key) pendingMutations.delete(key);
    return response;
  },
  (error) => {
    const key = error.config?.__mutationKey;
    if (key) pendingMutations.delete(key);

    if (axios.isCancel(error)) {
      return Promise.reject(error);
    }

    const status = error.response?.status;

    if (status === 401) {
      localStorage.removeItem("token");
      localStorage.removeItem("usuario_email");
      window.dispatchEvent(new CustomEvent("frontend_auth_expired"));
      window.location.assign("/");
    }

    if (status === 403) {
      window.dispatchEvent(
        new CustomEvent("frontend_forbidden", {
          detail: {
            endpoint: error.config?.url,
            method: error.config?.method,
            timestamp: new Date().toISOString(),
          },
        })
      );
    }

    return Promise.reject(error);
  }
);
