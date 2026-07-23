# Changelog

## Perfil profissional e relatórios — v2

### Backend
- Adicionadas as propriedades `crf` e `assinatura_digital` aos dois mapeamentos da tabela `users`.
- Adicionadas migrações incrementais para essas colunas.
- Corrigido `GET /consultorio/me/perfil-profissional`.
- Corrigido `PUT /consultorio/me/perfil-profissional`.
- O nome completo passa a atualizar `users.nome`, fonte usada nos relatórios.

### Frontend
- O perfil passa a ser carregado por `/consultorio/me/perfil-profissional`, eliminando a inconsistência com `/me`.

### Banco
- Incluído script SQL idempotente para Supabase/PostgreSQL.
