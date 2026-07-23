# Atualização — perfil profissional nos relatórios

## Correção realizada

- O formulário agora carrega os dados pela mesma API usada para salvar.
- `nome_completo` atualiza a coluna existente `users.nome`, já utilizada pelos relatórios.
- `crf` e `assinatura_digital` passam a ser persistidos na tabela `users`.
- Os modelos principal e do consultório foram alinhados com as novas colunas.
- As respostas GET e PUT devolvem todos os campos do perfil profissional.

## 1. Aplicar os arquivos

Extraia este ZIP na raiz do projeto:

`C:\Users\Dario\Desktop\intervencao-farmaceutica`

Confirme a substituição dos arquivos existentes.

## 2. Atualizar o Supabase

No Supabase, abra **SQL Editor**, cole e execute o conteúdo de:

`sql/01_perfil_profissional.sql`

Isso cria as colunas sem apagar dados existentes.

## 3. Validar localmente

Na raiz do projeto:

```cmd
python -m py_compile backend\models\core.py backend\models\consultorio_models.py backend\routers\consultorio.py backend\migrations.py
cd frontend
npm run build
cd ..
```

## 4. Versionar

Execute a partir da raiz do projeto, e não de dentro da pasta `backend`:

```cmd
git add backend/models/core.py backend/models/consultorio_models.py backend/routers/consultorio.py backend/migrations.py frontend/src/pages/perfil/PerfilProfissional.jsx
git commit -m "Corrige perfil profissional nos relatorios"
git push origin main
```

## 5. Publicar

- Render: faça **Manual Deploy → Deploy latest commit**, caso o deploy automático não inicie.
- Vercel: aguarde o deploy automático do frontend ou solicite novo deploy.

## 6. Teste final

1. Abra **Perfil Profissional**.
2. Informe nome completo e CRF.
3. Salve.
4. Atualize a página e confirme que os dados permanecem preenchidos.
5. Gere novamente um relatório ou PDF. O nome e o CRF devem aparecer atualizados.

> Relatórios já gerados anteriormente não são alterados; é necessário gerar um novo documento.
