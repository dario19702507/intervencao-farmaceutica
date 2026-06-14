# Passo 11C — Frontend da Gestão Documental

Substitua/adicone somente os arquivos do frontend.

Arquivos incluídos:

- frontend/src/pages/documentos/DocumentosPaciente.jsx
- frontend/src/pages/documentos/DocumentosPaciente.css
- frontend/src/App.jsx
- frontend/src/components/layout/Sidebar.jsx

Funcionalidades:

- Dashboard documental.
- Upload de documentos por paciente clínico.
- Listagem de documentos do paciente.
- Download de documento.
- Inativação lógica.
- Vencimentos documentais.
- Geração de notificações de validade documental.

Após substituir, rode:

```cmd
cd frontend
npm run dev
```

Backend esperado:

- GET /consultorio/documentos/opcoes
- GET /consultorio/documentos/validade-dashboard
- GET /consultorio/documentos/vencimentos
- POST /consultorio/documentos/gerar-notificacoes-validade
- GET /consultorio/paciente-clinico/{paciente_id}/documentos
- POST /consultorio/paciente-clinico/{paciente_id}/documentos
- GET /consultorio/documentos/{id}/download
- DELETE /consultorio/documentos/{id}
