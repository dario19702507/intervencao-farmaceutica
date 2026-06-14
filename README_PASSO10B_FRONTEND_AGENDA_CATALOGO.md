# Passo 10B — Frontend da Agenda e Catálogo de Medicamentos

Este pacote adiciona uma nova tela ao frontend:

- **Agenda + Medicamentos**

A tela permite:

- visualizar indicadores básicos da Agenda;
- listar eventos agendados;
- criar evento de Agenda com tipo `INCLUSAO`, `RETIRADA`, `RENOVACAO`, `ADEQUACAO` ou `ENCERRAMENTO`;
- selecionar medicamento a partir do catálogo padronizado;
- cadastrar medicamento/apresentação;
- editar medicamento;
- inativar medicamento;
- carregar catálogo padrão via seed.

## Arquivos alterados

```txt
frontend/src/App.jsx
frontend/src/components/layout/Sidebar.jsx
```

## Arquivos novos

```txt
frontend/src/pages/agenda/AgendaCatalogo.jsx
frontend/src/pages/agenda/AgendaCatalogo.css
```

## Como aplicar

Substitua/adicone apenas os arquivos listados acima no frontend.

Depois rode:

```cmd
cd frontend
npm run dev
```

Para validar build:

```cmd
npm run build
```

## Requisitos de backend

Este frontend pressupõe que o Passo 10A já está aplicado e que estas rotas respondem:

```txt
GET  /consultorio/agenda/opcoes
GET  /consultorio/agenda/dashboard
GET  /consultorio/agenda
POST /consultorio/agenda
GET  /consultorio/catalogo-medicamentos
POST /consultorio/catalogo-medicamentos
PUT  /consultorio/catalogo-medicamentos/{id}
DELETE /consultorio/catalogo-medicamentos/{id}
POST /consultorio/catalogo-medicamentos/seed
GET  /consultorio/pacientes-clinicos
```
