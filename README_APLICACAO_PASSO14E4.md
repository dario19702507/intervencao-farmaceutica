# Passo 14E.4 — Workspace Agenda

Este pacote consolida a área de agenda e comunicação em uma única entrada de menu.

## Objetivo

Reduzir redundância no frontend, mantendo os fluxos existentes:

- Agenda e Alertas
- Agenda Integrada
- Agenda + Medicamentos
- Notificações
- WhatsApp

Tudo passa a ficar em uma única tela:

```txt
Agenda
├── Visão Geral
├── Agenda
├── Notificações
├── WhatsApp
└── Catálogo
```

## Arquivos incluídos

```txt
frontend/src/navigation/catalog.jsx
frontend/src/pages/agenda/AgendaWorkspace.jsx
frontend/src/pages/agenda/AgendaWorkspace.css
```

## O que muda

- O menu lateral exibe apenas um item: **Agenda**.
- As rotas antigas continuam redirecionando para o workspace.
- Não há alteração no backend.
- As telas já existentes são reaproveitadas como abas internas.

## Como aplicar

Copie os arquivos do pacote para os mesmos caminhos no projeto.

Depois rode:

```cmd
cd frontend
npm run dev
```

## Validação sugerida

Abrir o frontend e conferir:

```txt
Agenda > Visão Geral
Agenda > Agenda
Agenda > Notificações
Agenda > WhatsApp
Agenda > Catálogo
```

Também testar os redirects antigos:

```txt
/agenda-integrada
/agenda-catalogo
/notificacoes-whatsapp
/medicamentos
/whatsapp
```

Todos devem abrir o workspace de Agenda.
