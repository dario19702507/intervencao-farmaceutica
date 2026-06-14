# Passo 14E.2A.1 — Centro de Atenção dentro do Consultório

## Objetivo

Este ajuste corrige a redundância de navegação criada no passo 14E.2A:

- remove o Centro de Atenção Farmacêutica como item separado do menu;
- mantém uma única entrada principal: Consultório;
- transforma o Centro de Atenção em aba inicial dentro do Consultório;
- preserva os redirecionamentos antigos para evitar quebra de links;
- corrige o import do api em CuidadoFarmaceutico.jsx.

## Arquivos alterados

- `frontend/src/navigation/catalog.jsx`
- `frontend/src/pages/consultorio/Consultorio.jsx`
- `frontend/src/pages/consultorio/CuidadoFarmaceutico.jsx`

## Resultado esperado

A navegação passa a ficar assim:

```txt
Atendimento
├── Serviços Rápidos
├── Consultório
├── Fila Clínica
└── Pacientes
```

Dentro de Consultório:

```txt
Consultório Farmacêutico
├── Centro de Atenção
└── Pacientes e Prontuários
```

Ao abrir um paciente, o fluxo do prontuário permanece igual:

```txt
Resumo
Identificação
Perfil clínico
Farmacoterapia
PRM / Intervenções
Metas
Plano de cuidado
Evoluções
Timeline
```

## Compatibilidade

Os caminhos antigos continuam redirecionando para o Consultório:

- `/cuidado-farmaceutico`
- `/centro-atencao-farmaceutica`
- `/atendimento/centro-atencao`

## Validação recomendada

```cmd
cd frontend
npm run dev
```

Depois conferir:

1. o menu lateral não mostra mais Centro de Atenção separado;
2. Consultório abre com a aba Centro de Atenção;
3. a aba Pacientes e Prontuários mostra a lista de pacientes;
4. Abrir prontuário continua funcionando;
5. não aparece mais erro de export default do api.
