# 15E.2 — Cadastro Mestre com busca sob demanda

## Objetivo

Reduzir a lentidão do Cadastro Mestre de Pacientes eliminando o carregamento inicial da lista completa de pacientes.

## Alterações realizadas

### Backend

Arquivo alterado:

- `backend/routers/pacientes.py`

Ajustes:

- `GET /consultorio/pacientes` passa a exigir termo com pelo menos 3 caracteres.
- Adicionados parâmetros `limit` e `offset`.
- Retorno passa a incluir `total`, `limit` e `offset`.
- Evita consulta integral ao abrir a página.
- Busca por nome, CPF, CNS e telefone.

### Frontend

Arquivo alterado:

- `frontend/src/pages/pacientes/Pacientes.jsx`

Ajustes:

- Remove carregamento automático de pacientes ao abrir a tela.
- Exibe instrução inicial para buscar por nome, CPF, CNS ou telefone.
- Só permite pesquisa com 3 ou mais caracteres.
- Retorna até 30 pacientes por busca.
- Mantém ações existentes de Histórico e Editar.
- Após edição, recarrega apenas a busca atual, se houver termo válido.

## Validação sugerida

1. Abrir `Pacientes → Cadastro Mestre`.
2. Confirmar que a lista não carrega automaticamente.
3. Digitar menos de 3 caracteres e confirmar que a busca não roda.
4. Buscar por nome.
5. Buscar por CPF.
6. Buscar por CNS.
7. Buscar por telefone.
8. Abrir histórico de um paciente.
9. Editar paciente e salvar.
10. Confirmar melhora no tempo de abertura da página.

## Deploy

Este patch exige deploy no Render e no Vercel.
