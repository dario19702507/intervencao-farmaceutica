# Passo 14B — Arquitetura definitiva de navegação do frontend

Este pacote aplica a solução agressiva recomendada no relatório analítico: substituição da navegação baseada em `activePage` por navegação real com `react-router-dom`, catálogo único de rotas, redirects legados, sidebar agrupada por domínio, topbar dinâmica e unificação do `apiClient`.

## O que foi alterado

### 1. Catálogo único de navegação

Novo arquivo:

```txt
frontend/src/navigation/catalog.jsx
```

Ele concentra:

- `key` da tela;
- `path` canônico;
- label;
- seção do menu;
- ícone;
- título e subtítulo da Topbar;
- permissões básicas de visualização/escrita;
- `telemetryKey`;
- aliases e redirects legados.

### 2. Migração para URLs reais

Arquivos alterados:

```txt
frontend/src/main.jsx
frontend/src/App.jsx
```

Agora o sistema usa:

```txt
BrowserRouter
Routes
Route
Navigate
Suspense
lazy loading
```

Isso permite:

- recarregar a página e permanecer na tela correta;
- usar voltar/avançar do navegador;
- compartilhar URLs diretas;
- evoluir futuramente para rotas-filhas reais.

### 3. Sidebar agrupada e baseada no catálogo

Arquivo alterado:

```txt
frontend/src/components/layout/Sidebar.jsx
```

Grupos finais:

```txt
Início
Atendimento
Agenda e Comunicação
Documentos
Inteligência
Sistema
```

Itens redundantes foram tratados por agrupamento ou redirect. A Central Operacional e o item Relatórios antigo deixam de ser destinos principais.

### 4. Topbar dinâmica

Arquivo alterado:

```txt
frontend/src/components/layout/Topbar.jsx
```

O título e subtítulo agora são derivados da rota atual pelo catálogo único.

### 5. Layout simplificado

Arquivo alterado:

```txt
frontend/src/components/layout/MainLayout.jsx
```

Remove dependência de `activePage` e passa a trabalhar com a navegação por URL.

### 6. Compatibilidade com páginas antigas

Novo arquivo:

```txt
frontend/src/components/router/AppRoute.jsx
```

Ele mantém compatibilidade com páginas que ainda recebem `setActivePage`, convertendo chamadas antigas em navegação por URL.

### 7. Autenticação e telemetria básica

Novos arquivos:

```txt
frontend/src/components/router/RequireAuth.jsx
frontend/src/components/router/RouteTelemetry.jsx
```

`RequireAuth` mantém o comportamento atual de login. `RouteTelemetry` emite eventos locais (`CustomEvent`) para preparar futura instrumentação sem exigir mudança no backend agora.

### 8. API unificada

Arquivos alterados:

```txt
frontend/src/api/api.js
frontend/src/api.js
```

O `apiClient` agora tem interceptação consistente para:

- token no request;
- limpeza de sessão em 401;
- evento local para 403.

### 9. CSS complementar

Arquivo alterado:

```txt
frontend/src/style.css
```

Foram adicionadas regras para links do menu, grupos recolhidos e estado de carregamento de módulos lazy.

## Rotas canônicas principais

```txt
/                                  Dashboard
/operacoes/painel                  Painel Operacional
/atendimento/servicos              Serviços Rápidos
/atendimento/consultorio           Consultório
/atendimento/fila                  Fila Clínica
/atendimento/pacientes             Pacientes
/agenda/visao-geral                Visão geral da agenda
/agenda/eventos                    Agenda integrada/eventos
/agenda/catalogo                   Catálogo de medicamentos
/agenda/comunicacoes               Notificações e WhatsApp
/documentos/gestao                 Gestão documental
/documentos/processos              Processos documentais
/documentos/ocr                    OCR documental
/inteligencia/epidemiologia        Dashboard epidemiológico
/inteligencia/ciencia              Indicadores científicos
/inteligencia/relatorios           Relatórios gerenciais
/sistema/perfil                    Perfil profissional
```

## Redirects legados preservados

Exemplos:

```txt
/central-operacional     → /operacoes/painel
/relatorios              → /inteligencia/relatorios
/agenda                  → /agenda/visao-geral
/documentos              → /documentos/gestao
```

## Como aplicar

Copie a pasta `frontend/` deste pacote sobre a pasta `frontend/` do projeto.

Depois rode:

```cmd
cd frontend
npm install
npm run build
npm run dev
```

## Validação realizada

Foi executado build local do frontend após `npm install` limpo para recompor dependências nativas do Vite/Rolldown:

```txt
npm run build
✓ built
```

## Observações importantes

1. Este pacote não altera backend.
2. As páginas grandes não foram reescritas internamente; foram encapsuladas por rotas reais.
3. A compatibilidade com chamadas antigas de `setActivePage` foi mantida.
4. A limpeza física de `node_modules`, `venv`, backups e arquivos mortos não foi incluída no pacote para evitar apagar arquivos no ambiente do usuário. A recomendação é fazer essa limpeza depois de validar a navegação.
