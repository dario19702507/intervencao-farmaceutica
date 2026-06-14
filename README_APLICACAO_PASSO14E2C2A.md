# Passo 14E.2C.2A — Intervenções Padronizadas e Mapeamento do App de Intervenções

Este pacote cria a primeira camada de padronização das intervenções farmacêuticas, aproveitando os textos já utilizados no App de Intervenções em produção.

## Objetivo

- Criar catálogo versionado de intervenções farmacêuticas.
- Mapear textos legados do App de Intervenções para categorias padronizadas.
- Manter dados originais preservados.
- Preparar a futura padronização dos formulários de intervenção e dos indicadores clínicos.

## Novos endpoints

```txt
GET  /consultorio/intervencoes-padronizadas/opcoes
POST /consultorio/intervencoes-padronizadas/preparar-estrutura
GET  /consultorio/intervencoes-padronizadas/mapeamento-legado
GET  /consultorio/intervencoes-padronizadas/dashboard
```

## Catálogo inicial

```txt
Educação em saúde
Orientação farmacêutica
Conciliação medicamentosa
Monitoramento farmacoterapêutico
Encaminhamento
Contato com prescritor
Contato com equipe multiprofissional
Ajuste terapêutico sugerido
Reforço de adesão
Prevenção ou manejo de evento adverso
Orientação documental
Outra intervenção
```

## Campos estruturais preparados

```txt
tipo_intervencao_padronizado
nivel_intervencao
aceitacao
implementacao
resultado
descricao_clinica_complementar
prm_id
origem_sistema
origem_id
```

## Aplicação

Extraia o pacote na raiz do projeto e rode:

```cmd
python scripts\aplicar_passo14E2C2A.py
```

Depois valide:

```cmd
pytest -q tests
python tests\smoke_tests.py
```

## Observação

Esta etapa não altera os registros já existentes. Ela apenas cria o catálogo e um painel de mapeamento inicial dos textos legados, deixando a migração real para a etapa seguinte.
