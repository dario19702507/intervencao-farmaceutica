# 15C.1 — Consolidação de usuários e perfis

## Decisão aplicada

O sistema mantém **um cadastro único de usuários**, reaproveitando a base já existente do módulo de Intervenções. Não foi criado um segundo login para o Consultório Farmacêutico.

## Ajustes incluídos

- Matriz centralizada de permissões por módulo no backend.
- Retorno de `/me`, `/users`, `/profissionais` e `/supervisores` com permissões consolidadas.
- Endpoint administrativo para editar nome, e-mail, perfil e categoria profissional do usuário.
- Tela administrativa **Sistema → Usuários e Perfis**.
- Proteção visual da rota administrativa para perfil não administrador.
- Página com matriz de permissões por módulo: Intervenções, Consultório, Documentos, Relatórios, Agenda e Administração.

## Perfis operacionais sugeridos

| Perfil | Uso recomendado |
|---|---|
| Administrador | Gestão do sistema, usuários e perfis |
| Farmacêutico | Registro assistencial completo |
| Estagiário | Registro assistencial supervisionado |
| Pesquisador | Consulta e análise, sem edição |
| Leitura | Consulta operacional, sem edição |

## Teste após aplicar o patch

1. Entrar com usuário administrador.
2. Acessar **Sistema → Usuários e Perfis**.
3. Criar um usuário farmacêutico.
4. Criar um usuário leitura.
5. Editar perfil de um usuário.
6. Redefinir senha de teste.
7. Sair e entrar com usuário leitura.
8. Confirmar que ações de escrita continuam bloqueadas.

## Observação

As permissões por módulo são calculadas a partir do perfil. Isso reduz complexidade no piloto e evita inconsistências de permissões individuais por usuário.
