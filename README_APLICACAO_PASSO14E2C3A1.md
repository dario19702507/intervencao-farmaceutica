# Passo 14E.2C.3A.1 — Formulário de Metas Terapêuticas no Consultório

## Objetivo

Completar a entrega das Metas Terapêuticas Estruturadas no frontend. O backend já estava ativo, mas a aba **6. Metas** do Consultório apenas exibia as metas; agora ela permite criar e editar metas terapêuticas.

## Arquivos alterados

- `frontend/src/pages/consultorio/Consultorio.jsx`
- `frontend/src/style.css`

## O que foi incluído

Na aba **Consultório → Metas**:

- botão **Nova meta**;
- formulário para criação de meta terapêutica;
- edição de metas existentes;
- seleção de categoria e subcategoria;
- descrição clínica;
- valor atual, valor alvo e unidade;
- data inicial, prazo previsto e conclusão;
- status e origem;
- vínculo opcional com PRM;
- vínculo opcional com intervenção farmacoterapêutica.

## Endpoints utilizados

- `GET /consultorio/metas/opcoes`
- `POST /consultorio/metas`
- `PUT /consultorio/metas/{meta_id}`
- `GET /consultorio/paciente-clinico/{paciente_id}/resumo-cuidado`

## Aplicação

Extraia o pacote na raiz do projeto, sobrescrevendo os arquivos indicados.

Depois rode:

```cmd
cd frontend
npm run dev
```

Não há alteração de backend nem de banco de dados neste ajuste.
