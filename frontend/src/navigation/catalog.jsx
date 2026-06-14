import { lazy } from "react";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  BellRing,
  CalendarDays,
  FileSpreadsheet,
  FileText,
  FolderUp,
  Gauge,
  LayoutDashboard,
  Microscope,
  Pill,
  Stethoscope,
  UserCog,
  Users,
} from "lucide-react";

const DashboardPage = lazy(() => import("../pages/dashboard/Dashboard.jsx"));
const ServicosRapidosPage = lazy(() => import("../pages/servicos/ServicosRapidos.jsx"));
const ConsultorioPage = lazy(() => import("../pages/consultorio/Consultorio.jsx"));
const FilaClinicaPage = lazy(() => import("../pages/fila/FilaClinica.jsx"));
const PacientesPage = lazy(() => import("../pages/pacientes/Pacientes.jsx"));

const AgendaWorkspacePage = lazy(() => import("../pages/agenda/AgendaWorkspace.jsx"));

const DocumentosWorkspacePage = lazy(() => import("../pages/documentos/DocumentosWorkspace.jsx"));
const RelatoriosPage = lazy(() => import("../pages/relatorios/Relatorios.jsx"));

const PainelOperacionalPage = lazy(() => import("../pages/operacional/PainelOperacional.jsx"));
const AnalyticsWorkspacePage = lazy(() => import("../pages/analytics/AnalyticsWorkspace.jsx"));
const PerfilProfissionalPage = lazy(() => import("../pages/perfil/PerfilProfissional.jsx"));
const UsuariosPerfisPage = lazy(() => import("../pages/sistema/UsuariosPerfis.jsx"));

const ALL = ["*"];
const WRITE_ASSISTENCIAL = ["admin", "farmaceutico", "estagiario"];
const WRITE_GESTAO = ["admin", "farmaceutico"];

export const ROUTES = [
  {
    key: "dashboard",
    path: "/",
    label: "Dashboard",
    section: "inicio",
    icon: LayoutDashboard,
    title: "Dashboard",
    subtitle: "Visão geral do cuidado farmacêutico e dos principais indicadores.",
    component: DashboardPage,
    permissions: { view: ALL, write: [] },
    telemetryKey: "inicio_dashboard",
    legacyKeys: ["dashboard"],
    redirectFrom: ["/dashboard"],
  },
  {
    key: "painel-operacional",
    path: "/operacoes/painel",
    label: "Painel Operacional",
    section: "inicio",
    icon: Gauge,
    title: "Painel Operacional",
    subtitle: "Acompanhamento diário de agenda, documentos, notificações e pendências.",
    component: PainelOperacionalPage,
    permissions: { view: ALL, write: WRITE_GESTAO },
    telemetryKey: "operacoes_painel",
    legacyKeys: ["painel-operacional", "central-operacional"],
    redirectFrom: ["/painel-operacional", "/central-operacional", "/operacoes", "/operacional"],
  },
  {
    key: "servicos",
    path: "/atendimento/servicos",
    label: "Serviços Rápidos",
    section: "atendimento",
    icon: Activity,
    title: "Serviços Rápidos",
    subtitle: "Registro de PA, glicemia, bioimpedância, pico de fluxo e demais atendimentos rápidos.",
    component: ServicosRapidosPage,
    permissions: { view: ALL, write: WRITE_ASSISTENCIAL },
    telemetryKey: "atendimento_servicos",
    legacyKeys: ["servicos"],
    redirectFrom: ["/servicos"],
  },
  {
    key: "consultorio",
    path: "/atendimento/consultorio",
    label: "Consultório",
    section: "atendimento",
    icon: Stethoscope,
    title: "Consultório Farmacêutico",
    subtitle: "Prontuário, evolução clínica, desfechos e acompanhamento farmacoterapêutico.",
    component: ConsultorioPage,
    permissions: { view: ALL, write: WRITE_ASSISTENCIAL },
    telemetryKey: "atendimento_consultorio",
    legacyKeys: ["consultorio"],
    redirectFrom: ["/consultorio"],
  },
  {
    key: "fila-clinica",
    path: "/atendimento/fila",
    label: "Fila Clínica",
    section: "atendimento",
    icon: AlertTriangle,
    title: "Fila Clínica",
    subtitle: "Triagem e organização dos pacientes que precisam de avaliação farmacêutica.",
    component: FilaClinicaPage,
    permissions: { view: ALL, write: WRITE_GESTAO },
    telemetryKey: "atendimento_fila_clinica",
    legacyKeys: ["fila-clinica"],
    redirectFrom: ["/fila-clinica"],
  },
  {
    key: "pacientes",
    path: "/atendimento/pacientes",
    label: "Pacientes",
    section: "atendimento",
    icon: Users,
    title: "Pacientes",
    subtitle: "Consulta e acompanhamento dos pacientes registrados no sistema.",
    component: PacientesPage,
    permissions: { view: ALL, write: WRITE_GESTAO },
    telemetryKey: "atendimento_pacientes",
    legacyKeys: ["pacientes"],
    redirectFrom: ["/pacientes", "/atendimento"],
  },
  {
    key: "agenda",
    path: "/agenda",
    label: "Agenda",
    section: "agenda",
    icon: CalendarDays,
    title: "Agenda e Comunicação",
    subtitle: "Retornos, alertas, notificações, WhatsApp e catálogo em um único workspace.",
    component: AgendaWorkspacePage,
    permissions: { view: ALL, write: WRITE_GESTAO },
    telemetryKey: "agenda_workspace",
    legacyKeys: [
      "agenda",
      "agenda-alertas",
      "agenda-integrada",
      "agenda-catalogo",
      "notificacoes-whatsapp"
    ],
    redirectFrom: [
      "/agenda/visao-geral",
      "/agenda/eventos",
      "/agenda/catalogo",
      "/agenda/comunicacoes",
      "/agenda-integrada",
      "/agenda-catalogo",
      "/medicamentos",
      "/notificacoes-whatsapp",
      "/notificacoes",
      "/whatsapp"
    ],
  },
  {
    key: "documentos",
    path: "/documentos",
    label: "Documentos",
    section: "documentos",
    icon: FolderUp,
    title: "Documentos",
    subtitle: "Gestão documental, pacotes, OCR, vigências e pendências em um único workspace.",
    component: DocumentosWorkspacePage,
    permissions: { view: ALL, write: WRITE_GESTAO },
    telemetryKey: "documentos_workspace",
    legacyKeys: ["documentos", "processos-documentais", "ocr-documental"],
    redirectFrom: [
      "/documentos/gestao",
      "/documentos/processos",
      "/documentos/ocr",
      "/processos-documentais",
      "/ocr-documental"
    ],
  },

  {
    key: "impressao",
    path: "/impressao",
    label: "Impressões",
    section: "documentos",
    icon: FileText,
    title: "Central de Impressões",
    subtitle: "Prontuários, planos de cuidado, declarações, laudos e relatórios para impressão.",
    component: RelatoriosPage,
    permissions: { view: ALL, write: [] },
    telemetryKey: "documentos_impressao",
    legacyKeys: ["impressao", "central-impressao", "relatorios"],
    redirectFrom: ["/relatorios", "/central-impressao", "/documentos/impressao"],
  },
  {
    key: "analytics",
    path: "/inteligencia",
    label: "Analytics",
    section: "inteligencia",
    icon: BarChart3,
    title: "Analytics",
    subtitle: "Painéis, indicadores científicos, epidemiológicos e relatórios em um único workspace.",
    component: AnalyticsWorkspacePage,
    permissions: { view: ALL, write: [] },
    telemetryKey: "inteligencia_analytics",
    legacyKeys: [
      "dashboard-epidemiologico",
      "indicadores-cientificos",
      "relatorios-gerenciais",
      "analytics"
    ],
    redirectFrom: [
      "/dashboard-epidemiologico",
      "/indicadores-cientificos",
      "/relatorios-gerenciais",
      "/inteligencia/epidemiologia",
      "/inteligencia/ciencia",
      "/inteligencia/relatorios"
    ],
  },

  {
    key: "usuarios-perfis",
    path: "/sistema/usuarios",
    label: "Usuários e Perfis",
    section: "sistema",
    icon: Users,
    title: "Usuários e Perfis",
    subtitle: "Cadastro único de usuários e permissões por módulo.",
    component: UsuariosPerfisPage,
    permissions: { view: ["admin"], write: ["admin"] },
    telemetryKey: "sistema_usuarios_perfis",
    legacyKeys: ["usuarios", "perfis", "administracao-usuarios"],
    redirectFrom: ["/usuarios", "/perfis", "/sistema/administracao"],
  },
  {
    key: "perfil-profissional",
    path: "/sistema/perfil",
    label: "Perfil profissional",
    section: "sistema",
    icon: UserCog,
    title: "Perfil Profissional",
    subtitle: "Dados do usuário, perfil de acesso e categoria profissional.",
    component: PerfilProfissionalPage,
    permissions: { view: ALL, write: ALL },
    telemetryKey: "sistema_perfil",
    legacyKeys: ["perfil-profissional"],
    redirectFrom: ["/perfil-profissional", "/sistema"],
  },
];

export const SIDEBAR_SECTIONS = [
  { key: "inicio", label: "Início", items: ["dashboard", "painel-operacional"] },
  { key: "atendimento", label: "Atendimento", items: ["servicos", "consultorio", "fila-clinica", "pacientes"] },
  { key: "agenda", label: "Agenda e Comunicação", items: ["agenda"] },
  { key: "documentos", label: "Documentos", items: ["documentos", "impressao"] },
  { key: "inteligencia", label: "Inteligência", items: ["analytics"] },
  { key: "sistema", label: "Sistema", items: ["usuarios-perfis", "perfil-profissional"] },
];

export const ROUTES_BY_KEY = Object.fromEntries(ROUTES.map((route) => [route.key, route]));

export const LEGACY_REDIRECTS = ROUTES.flatMap((route) =>
  (route.redirectFrom || [])
    .filter((from) => from !== route.path)
    .map((from) => ({ from, to: route.path }))
);

const LEGACY_KEY_TO_PATH = new Map();
for (const route of ROUTES) {
  LEGACY_KEY_TO_PATH.set(route.key, route.path);
  for (const key of route.legacyKeys || []) {
    LEGACY_KEY_TO_PATH.set(key, route.path);
  }
}

export function getPathByPageKey(pageKey) {
  return LEGACY_KEY_TO_PATH.get(pageKey) || "/";
}

export function normalizePerfil(perfil) {
  return String(perfil || "").trim().toLowerCase();
}

export function canView(route, usuario) {
  const allowed = route.permissions?.view || ALL;
  const perfil = normalizePerfil(usuario?.perfil);
  return allowed.includes("*") || allowed.includes(perfil);
}

export function findRouteByPath(pathname) {
  if (!pathname) return ROUTES_BY_KEY.dashboard;

  const exact = ROUTES.find((route) => route.path === pathname);
  if (exact) return exact;

  const nested = ROUTES
    .filter((route) => route.path !== "/" && pathname.startsWith(`${route.path}/`))
    .sort((a, b) => b.path.length - a.path.length)[0];

  return nested || ROUTES_BY_KEY.dashboard;
}
