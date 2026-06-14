# Passo 11E — Frontend da Vigência Documental

Substituir/adicionar somente os arquivos do frontend.

## Entregas

- Campo de operação de vigência no upload: INCLUSAO, RENOVACAO, ADEQUACAO.
- Correção do upload para enviar `tipo_documento`, compatível com o backend do 11D.
- Visualização da vigência calculada: início, fim, status e edição manual.
- Edição de vigência com motivo obrigatório.
- Consulta do histórico/auditoria da vigência.
- Botão para reprocessar fluxo operacional do documento: Agenda, Notificação e WhatsApp.
- Exibição das regras automáticas definidas para a Farmácia Escola.

## Teste recomendado

1. Rodar o backend.
2. Rodar o frontend:

```cmd
cd frontend
npm run dev
```

3. Acessar Gestão Documental.
4. Enviar LAUDO com operação de vigência.
5. Editar vigência com motivo.
6. Consultar histórico.
7. Reprocessar fluxo.
