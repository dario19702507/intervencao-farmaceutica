# Matriz inicial de permissões por perfil — Passo 9B

## Perfis padronizados

- `admin`: administração completa do sistema.
- `farmaceutico`: registro e acompanhamento clínico-assistencial.
- `estagiario`: registro assistencial com supervisão quando aplicável.
- `pesquisador`: leitura e extração restrita, sem alteração de registros.
- `visualizacao`: leitura restrita, sem alteração de registros.

## Perfis legados mantidos por compatibilidade

- `leitor`: tratado como perfil de visualização restrita.
- `operador`: tratado temporariamente como perfil com permissão de escrita assistencial.

## Regras implementadas neste passo

- Criação/listagem/reativação de usuários: `admin`.
- Alteração de registros de intervenção: bloqueada para `leitor`, `pesquisador` e `visualizacao`.
- Registros assistenciais do consultório: permitidos para perfis de escrita e categorias assistenciais.
- Plano de cuidado: restrito a administrador, farmacêutico ou docente.
- Perfis novos são validados na criação de usuário.

## Observação

Este passo cria uma camada centralizada de autorização em `backend/permissions.py`, preservando compatibilidade com as regras existentes. A próxima etapa pode aplicar permissões mais específicas em cada router, caso necessário.
