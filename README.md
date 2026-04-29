# Sistema de Intervenção Farmacêutica

MVP web multiusuário para registrar intervenções farmacêuticas e analisar indicadores.

## Campos implementados
- Data de atendimento
- Paciente
- Data de nascimento
- Tipo de atendimento: presencial/remoto
- Motivo do atendimento
- Comorbidade
- Tipo de intervenção, com múltipla seleção
- Resultado
- Observações
- Profissional responsável automaticamente pelo login

## Como rodar

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

Acesse a documentação da API em: http://127.0.0.1:8000/docs

### Frontend
Em outro terminal:
```bash
cd frontend
npm install
npm run dev
```

Abra: http://localhost:5173

## Login inicial
- E-mail: admin@farmacia.local
- Senha: admin123

Troque a chave `SECRET_KEY` e a senha do administrador antes de uso real.

## Observação para produção
Este MVP usa SQLite local. Para uso institucional, recomenda-se PostgreSQL, HTTPS, controle formal de perfis, logs de auditoria e política de proteção de dados conforme LGPD.
