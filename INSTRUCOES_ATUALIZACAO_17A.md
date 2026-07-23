# Aplicação do patch 17A

Extraia o ZIP na raiz do projeto, preservando as pastas `backend`, `frontend` e `sql`.

## Banco de dados

O backend executa as novas colunas por `backend/migrations.py`. Como alternativa, execute no SQL Editor do Supabase:

`sql/17A_data_atendimento_off_label.sql`

## Git — executando na raiz do projeto

```cmd
git add backend frontend sql CHANGELOG_17A.md INSTRUCOES_ATUALIZACAO_17A.md
git commit -m "Adiciona data retrospectiva e avaliacao off-label"
git push origin main
```

## Publicação

1. Aguarde ou acione o deploy do backend no Render.
2. Aguarde ou acione o deploy do frontend na Vercel.
3. Confirme que a migração foi executada no banco.

## Testes

1. Registre um serviço rápido com data anterior e confira o histórico.
2. Registre uma evolução clínica com data anterior e confira a linha do tempo.
3. Cadastre medicamento como off-label sem justificativa: o backend deve recusar.
4. Cadastre com indicação e justificativa: deve salvar e exibir `OFF-LABEL`.
5. Gere o prontuário e as orientações farmacêuticas e confira a informação.
