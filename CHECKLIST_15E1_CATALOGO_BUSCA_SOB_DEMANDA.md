# 15E.1 — Catálogo de Medicamentos com busca sob demanda

## Objetivo
Reduzir a lentidão do Catálogo de Medicamentos após a importação de mais de mil registros, evitando o carregamento automático da lista completa ao abrir a página.

## Arquivo alterado
- `frontend/src/pages/agenda/CatalogoMedicamentos.jsx`

## Ajustes realizados
- A página não carrega mais medicamentos automaticamente ao abrir.
- A busca exige pelo menos 3 caracteres.
- O limite por página foi reduzido de 50 para 20 resultados.
- O botão Atualizar recarrega a lista somente se já houver uma busca válida.
- O botão Limpar remove os resultados da tela e mantém a página leve.
- Após cadastro, edição, inativação ou importação, a listagem só é recarregada se houver busca ativa.
- A mensagem da seção de resultados foi ajustada para explicar que a lista completa não é carregada.

## Validação recomendada
1. Acessar Agenda → Catálogo.
2. Confirmar que a tela abre sem carregar lista de medicamentos.
3. Buscar por `los`, `ins`, `ros` ou outro termo com 3 caracteres ou mais.
4. Confirmar retorno limitado e paginação funcional.
5. Usar Limpar e confirmar que os resultados desaparecem.
6. Testar edição/inativação de um item localizado pela busca.

## Deploy necessário
- Vercel apenas.
