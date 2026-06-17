# 15D.7A Frontend — Catálogo simplificado de medicamentos

## Objetivo
Disponibilizar no frontend a tela de catálogo simplificado de medicamentos, consumindo os endpoints `/medicamentos` já criados no backend.

## Arquivos alterados
- `frontend/src/pages/agenda/AgendaWorkspace.jsx`
- `frontend/src/pages/agenda/CatalogoMedicamentos.jsx`
- `frontend/src/style.css`

## Funcionalidades
- Aba `Catálogo` passa a abrir a tela de medicamentos simplificados.
- Busca por princípio ativo, nome comercial, apresentação ou registro ANVISA.
- Paginação com limite de 50 registros por página.
- Resumo do catálogo: total, ativos, inativos e com registro ANVISA.
- Cadastro manual de medicamento.
- Edição de medicamento.
- Ativação/inativação.
- Importação CSV/TXT.

## Validação sugerida
1. Acessar `Agenda → Catálogo`.
2. Confirmar se a tela carrega sem erro.
3. Cadastrar um medicamento de teste.
4. Editar o medicamento.
5. Inativar e reativar.
6. Testar busca por princípio ativo.
7. Importar CSV pequeno de teste.

## Observação
Esta etapa não integra ainda o catálogo à farmacoterapia ou ao consultório. Essa integração deve ficar para o próximo passo para reduzir risco.
