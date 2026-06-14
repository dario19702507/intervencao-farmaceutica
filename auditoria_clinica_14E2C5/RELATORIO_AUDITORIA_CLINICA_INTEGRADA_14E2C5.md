# 14E.2C.5 — Auditoria Clínica Integrada do Núcleo de Cuidado Farmacêutico

## 1. Síntese executiva

A versão analisada já apresenta um núcleo clínico bastante avançado: farmacoterapia estruturada, PRM padronizados, indicadores de PRM, intervenções padronizadas, metas estruturadas, ações do plano de cuidado, timeline unificada, Centro de Atenção Farmacêutica e Analytics. A principal conclusão da auditoria é que o sistema já não sofre por falta de módulos, mas por coexistência de camadas antigas e novas. Essa coexistência é compreensível, porque preserva compatibilidade e evita perda de dados, porém agora precisa ser governada para não gerar dupla digitação, divergência semântica e dificuldade de treinamento.

O maior ponto de atenção está no Consultório. O arquivo `frontend/src/pages/consultorio/Consultorio.jsx` possui aproximadamente 3.494 linhas e concentra muitos fluxos clínicos em uma única tela. Do ponto de vista operacional, isso funcionou para acelerar a construção do sistema, mas do ponto de vista de manutenção e usabilidade, tornou-se o principal ponto de complexidade. A recomendação não é reescrever tudo agora, mas consolidar a semântica clínica antes de novas expansões.

## 2. Situação clínica atual

O ciclo clínico esperado já existe de forma funcional:

```txt
Farmacoterapia
↓
PRM
↓
Intervenção
↓
Meta terapêutica
↓
Ação do plano de cuidado
↓
Evolução/desfecho
↓
Analytics
```

Entretanto, ainda há duas camadas de registro convivendo:

```txt
Camada antiga/textual:
- Evolução clínica com problemas_identificados, conduta, orientacoes_realizadas e plano_acompanhamento
- PlanoCuidado textual com problema_identificado, objetivo_terapeutico e intervencoes_planejadas
- IntervencaoFarmacoterapia com tipo_intervencao em texto livre

Camada nova/estruturada:
- ProblemaFarmacoterapeutico padronizado
- MetaTerapeutica estruturada
- AcaoPlanoCuidado estruturada
- Catálogo/mapeamento de intervenções padronizadas
```

Essa coexistência não é um erro, mas precisa ser interpretada como fase de transição. O sistema deve continuar aceitando o legado, mas a interface principal deve incentivar a camada estruturada.

## 3. Principais achados

### Achado 1 — Sobreposição entre PlanoCuidado antigo e AcaoPlanoCuidado novo

O modelo ainda possui `PlanoCuidado`, com campos textuais como `problema_identificado`, `objetivo_terapeutico`, `intervencoes_planejadas`, `prazo_reavaliacao`, `resultado` e `resultado_classificacao`. Ao mesmo tempo, o sistema já possui `AcaoPlanoCuidado`, que registra ações estruturadas com `tipo_acao`, `responsavel`, `prazo`, `prioridade`, `status`, `resultado` e vínculos com PRM, meta e intervenção.

**Interpretação:** o `PlanoCuidado` antigo funciona como nota ou plano narrativo, enquanto `AcaoPlanoCuidado` é a estrutura operacional correta para acompanhamento longitudinal.

**Risco:** o farmacêutico pode registrar a mesma conduta no plano textual e na ação estruturada.

**Recomendação:** manter `PlanoCuidado` apenas como plano narrativo legado/resumo clínico. A interface principal deve privilegiar `AcaoPlanoCuidado`. O botão “Novo plano” da aba 7 deve ser reavaliado, pois pode concorrer com o formulário de ações da aba 6.

### Achado 2 — Sobreposição entre Intervenção e Plano de Cuidado

A intervenção deve representar a decisão clínica tomada diante de um PRM. O plano deve representar as tarefas que operacionalizam a decisão.

Exemplo correto:

```txt
PRM: Baixa adesão
Intervenção: Reforço de adesão
Meta: Adesão ≥ 80% em 90 dias
Plano: retorno em 30 dias; revisar técnica; telefonar em 15 dias
```

**Risco:** registrar “orientação farmacêutica” como intervenção e repetir a mesma orientação como ação do plano sem diferenciar decisão de execução.

**Recomendação:** ajustar rótulos de interface e textos de ajuda:

```txt
Intervenção = decisão/conduta clínica
Plano = tarefas, responsáveis e prazos
```

### Achado 3 — Intervenções padronizadas ainda não alteram totalmente o registro nativo

Existe catálogo e dashboard de intervenções padronizadas, mas o modelo `IntervencaoFarmacoterapia` ainda mantém `tipo_intervencao` como texto e a interface ainda apresenta opções fixas legadas, como “Orientação farmacêutica”, “Ajuste de adesão”, “Suspeita de RAM”, “PRM/RNM”, “Conciliação medicamentosa”, “Encaminhamento” e “Outro”.

**Interpretação:** o sistema já padroniza para Analytics/mapeamento, mas o registro do Consultório ainda não consome plenamente o catálogo padronizado.

**Recomendação:** próximo ajuste clínico deve ser fazer o formulário de intervenção consumir `GET /consultorio/intervencoes-padronizadas/opcoes`, mantendo campo “Outro/descrição” para exceções.

### Achado 4 — Metas aparecem em dois lugares sem separação semântica clara

O paciente clínico ainda possui campos como `meta_pressao_arterial`, `meta_glicemica` e `meta_peso`. Agora existe também `MetaTerapeutica`, com categoria, subcategoria, valor atual, valor alvo, unidade, prazo, status e vínculos.

**Interpretação:** os campos antigos podem servir como metas gerais do perfil clínico, mas não devem concorrer com metas terapêuticas estruturadas.

**Recomendação:** tratar os campos antigos como “metas gerais legadas/observacionais” e considerar futuramente migrá-los de forma assistida para `MetaTerapeutica`.

### Achado 5 — Evolução clínica ainda concentra campos que se sobrepõem ao novo ciclo estruturado

`EvolucaoClinica` ainda contém `problemas_identificados`, `conduta`, `orientacoes_realizadas` e `plano_acompanhamento`. Esses campos são úteis como narrativa SOAP, mas podem repetir PRM, intervenção e plano.

**Recomendação:** a evolução deve ser interpretada como narrativa clínica e não como fonte primária de indicadores. Indicadores devem vir das tabelas estruturadas: `ProblemaFarmacoterapeutico`, `IntervencaoFarmacoterapia`, `MetaTerapeutica` e `AcaoPlanoCuidado`.

### Achado 6 — Aba 6 “Metas” concentra metas e ações, enquanto aba 7 “Plano” mantém plano antigo

A aba 6 agora permite metas e ações estruturadas. A aba 7 ainda permite plano de cuidado textual. Isso é funcional, mas cria ambiguidade.

**Recomendação de curto prazo:** renomear a aba 6 para “Metas e Ações” e a aba 7 para “Plano narrativo” ou “Resumo do plano”.

**Recomendação de médio prazo:** incorporar a aba 7 dentro da aba 6 como seção “Resumo narrativo/observações gerais do plano”, evitando duas áreas competindo pelo mesmo conceito.

### Achado 7 — O Consultório continua monolítico

`Consultorio.jsx` é o maior componente do frontend, com quase 3.500 linhas. Isso aumenta risco de regressão em qualquer ajuste clínico.

**Recomendação:** não reescrever agora, mas iniciar decomposição controlada em componentes:

```txt
Consultorio/
├── CentroAtencaoTab.jsx
├── FarmacoterapiaTab.jsx
├── PrmIntervencoesTab.jsx
├── MetasAcoesTab.jsx
├── PlanoNarrativoTab.jsx
├── EvolucoesTab.jsx
└── TimelineTab.jsx
```

## 4. Matriz de decisão clínica

| Conceito | Onde deve ser registrado | O que evitar |
|---|---|---|
| Medicamento em uso | Farmacoterapia | Repetir medicamento em PRM ou evolução |
| Baixa adesão referida | MedicamentoUso.adesao_referida | Criar PRM automaticamente sem validação clínica |
| PRM de adesão | ProblemaFarmacoterapeutico | Usar evolução como fonte principal do indicador |
| Decisão clínica | IntervencaoFarmacoterapia | Repetir como ação do plano sem prazo/responsável |
| Resultado esperado | MetaTerapeutica | Registrar como texto solto no plano |
| Tarefa de acompanhamento | AcaoPlanoCuidado | Registrar como meta ou intervenção |
| Narrativa do atendimento | EvolucaoClinica | Usar como tabela primária de analytics |
| Plano textual legado | PlanoCuidado | Competir com AcaoPlanoCuidado |

## 5. Recomendações priorizadas

### Prioridade 1 — Baixo risco e alto ganho

1. Renomear a aba 6 para **“Metas e Ações”**.
2. Renomear a aba 7 para **“Plano narrativo”** ou **“Resumo do Plano”**.
3. Inserir textos de ajuda: “Intervenção = decisão clínica; ação do plano = execução com responsável e prazo”.
4. Marcar `PlanoCuidado` como “legado/narrativo” na interface.

### Prioridade 2 — Consolidação funcional

1. Fazer o formulário de intervenção consumir o catálogo padronizado.
2. Exibir aviso quando uma intervenção estiver sem categoria padronizada.
3. Impedir que uma meta seja criada sem descrição e sem subcategoria.
4. Sugerir criação de ação do plano após salvar uma meta, sem automatizar de forma obrigatória.

### Prioridade 3 — Refatoração técnica

1. Separar `Consultorio.jsx` em componentes por aba.
2. Criar hooks internos: `useResumoCuidado`, `useMetas`, `usePlanoCuidado`, `usePrmIntervencoes`.
3. Consolidar rotas duplicadas do backend apenas depois que o frontend estiver estabilizado.

## 6. Próximo passo recomendado

A próxima entrega deveria ser:

```txt
14E.2C.5A — Ajustes de Usabilidade Clínica do Consultório
```

Escopo sugerido:

```txt
- Renomear aba 6 para Metas e Ações
- Renomear aba 7 para Plano narrativo
- Adicionar microtextos explicativos
- Reorganizar os blocos da aba 6 para Meta → Ações vinculadas
- Manter PlanoCuidado como legado/narrativo
- Não alterar backend
```

Depois disso, a próxima entrega clínica deve ser:

```txt
14E.2C.5B — Intervenção nativa consumindo catálogo padronizado
```

Essa ordem reduz ambiguidade para o usuário antes de mexer na estrutura de registro de intervenções.

## 7. Conclusão

O sistema já possui base clínica suficiente para operar como prontuário farmacêutico longitudinal. A principal melhoria agora é evitar que a riqueza do modelo gere confusão operacional. A regra de ouro para a próxima fase deve ser:

```txt
Farmacoterapia descreve o tratamento.
PRM descreve o problema.
Intervenção descreve a decisão clínica.
Meta descreve o resultado esperado.
Plano descreve a execução.
Evolução descreve a narrativa do acompanhamento.
Analytics mede os resultados.
```

