# Passo 14D — Refatoração visual do Consultório Farmacêutico

## Objetivo

Transformar a tela do Consultório em um fluxo mais intuitivo, longitudinal e orientado ao cuidado farmacêutico, reduzindo redundância de navegação interna e aproximando o prontuário do raciocínio clínico do farmacêutico.

## Arquivos alterados

- `frontend/src/pages/consultorio/Consultorio.jsx`
- `frontend/src/style.css`

## O que mudou

- A aba inicial agora é **Resumo**, não mais Identificação.
- A navegação interna do prontuário foi reorganizada em fluxo sequencial:
  1. Resumo
  2. Dados do paciente
  3. Perfil clínico
  4. Farmacoterapia
  5. PRM / Intervenções
  6. Metas
  7. Plano
  8. Evoluções
  9. Timeline
- Inclusão de faixa superior com indicadores-chave:
  - status do prontuário;
  - complexidade farmacoterapêutica;
  - PRM em aberto;
  - metas ativas;
  - eventos longitudinais.
- Inclusão de visão-resumo do cuidado farmacêutico.
- Inclusão de painel de pontos de atenção.
- A aba PRM / Intervenções passa a exibir os PRM estruturados antes das intervenções.
- Inclusão de aba **Metas**, exibindo metas terapêuticas e ações do plano de cuidado.
- Uso preferencial do endpoint canônico:
  - `GET /consultorio/paciente-clinico/{paciente_id}/resumo-cuidado`
- Mantém fallback para o carregamento legado, caso o endpoint canônico esteja indisponível.

## O que não muda

- Não altera backend.
- Não remove rotas antigas.
- Não altera banco de dados.
- Não altera permissões.
- Não remove formulários existentes.

## Validação realizada

Build do frontend validado em instalação limpa:

```cmd
npm run build
```

Resultado:

```txt
✓ built
```

## Como aplicar

Copie os arquivos do pacote para a raiz do projeto, sobrescrevendo os caminhos correspondentes.

Depois execute:

```cmd
cd frontend
npm install
npm run dev
```

Para validação de produção:

```cmd
npm run build
```

## Observação

Este passo é uma refatoração visual e operacional. Ele prepara a etapa seguinte, na qual o arquivo `Consultorio.jsx` poderá ser dividido em componentes menores por aba, sem mudar o comportamento já validado.
