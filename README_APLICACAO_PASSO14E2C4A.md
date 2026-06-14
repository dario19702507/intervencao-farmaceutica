# Passo 14E.2C.4A — Plano de Cuidado Estruturado

Este pacote complementa o Consultório Farmacêutico com formulário operacional para **ações estruturadas do plano de cuidado**, fechando o ciclo:

```txt
PRM → Intervenção → Meta → Ação do plano → Evolução/Desfecho
```

## O que foi alterado

Arquivo alterado:

```txt
frontend/src/pages/consultorio/Consultorio.jsx
```

## Funcionalidades incluídas

Na aba **6. Metas**, o bloco **Ações do plano** passa a permitir:

- criar nova ação do plano de cuidado;
- selecionar tipo de ação;
- selecionar responsável;
- definir prazo;
- definir prioridade;
- definir status;
- vincular a PRM;
- vincular a meta terapêutica;
- vincular a intervenção farmacoterapêutica;
- registrar descrição da ação;
- atualizar status e resultado da ação.

## Endpoints utilizados

Este passo usa endpoints já existentes no backend:

```txt
GET  /consultorio/cuidado/opcoes
POST /consultorio/paciente-clinico/{paciente_id}/acoes-plano-cuidado
PUT  /consultorio/acoes-plano-cuidado/{acao_id}/status
GET  /consultorio/paciente-clinico/{paciente_id}/resumo-cuidado
```

## Aplicação

Extraia o pacote na raiz do projeto, sobrescrevendo o arquivo indicado.

Depois rode:

```cmd
cd frontend
npm run dev
```

## Observação

Este passo não altera backend, banco de dados ou testes automatizados. Ele completa no frontend a funcionalidade de plano de cuidado estruturado que já estava parcialmente disponível na API do motor de cuidado farmacêutico.
