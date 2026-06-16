# 15D.2C — Sidebar fechada por padrão

## Ajuste realizado

A navegação lateral passou a iniciar com as seções recolhidas quando o usuário acessa a página inicial (`/`).

Quando o usuário acessa diretamente uma rota interna, como `/atendimento/pacientes-ceaf`, apenas a seção correspondente é aberta automaticamente para contextualizar a tela atual.

## Arquivo alterado

- `frontend/src/components/layout/Sidebar.jsx`

## Validação recomendada

1. Acessar `https://intervencao-farmaceutica-vqmm.vercel.app/` e confirmar que as seções do menu aparecem recolhidas.
2. Acessar `https://intervencao-farmaceutica-vqmm.vercel.app/atendimento/pacientes-ceaf` e confirmar que a seção Atendimento abre automaticamente.
3. Abrir manualmente as seções no desktop e no celular.
4. Confirmar que a tela Pacientes CEAF permanece acessível.
