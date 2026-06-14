# Passo 14E.2C.1B.1 — Visualização dos Indicadores PRM no Analytics

## Objetivo

Completar a entrega dos indicadores automáticos de PRM, tornando visível no frontend o endpoint já validado:

```txt
GET /consultorio/cuidado/prm-indicadores
```

## Alterações incluídas

Arquivos alterados/adicionados:

```txt
frontend/src/pages/analytics/AnalyticsWorkspace.jsx
frontend/src/pages/analytics/AnalyticsWorkspace.css
frontend/src/pages/analytics/PrmIndicadores.jsx
```

## O que muda na interface

No menu **Analytics**, a aba **Assistencial e Epidemiológico** passa a ter subtabs internas:

```txt
Panorama assistencial
Indicadores de PRM
```

A subaba **Indicadores de PRM** apresenta:

```txt
Total de PRM
PRM críticos abertos
PRM abertos há mais de 30 dias
PRM abertos há mais de 60 dias
Pacientes prioritários
Taxa de resolução
Taxa de padronização
PRM por categoria
PRM por criticidade
PRM por natureza
PRM por status
PRM por desfecho
Tabela de pacientes prioritários e pendências de PRM
```

## Backend

Não há alteração de backend neste pacote.

## Aplicação

Copie os arquivos do pacote para a raiz do projeto, sobrescrevendo quando solicitado.

Depois rode:

```cmd
cd frontend
npm run dev
```

Se necessário, rode também:

```cmd
npm install
npm run build
```

## Observação de validação

A tentativa de build no sandbox não pôde ser concluída porque o `node_modules` empacotado não contém o binding nativo Linux do Rolldown/Vite. Esse problema já havia ocorrido em etapas anteriores e é relacionado ao ambiente/dependências opcionais, não às alterações React/CSS deste pacote. Em ambiente local Windows, rode `npm install` antes do build quando necessário.
