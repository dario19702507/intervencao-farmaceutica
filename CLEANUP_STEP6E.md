# Passo 6E — Auditoria

## Objetivo
Separar a função de auditoria do router principal do Consultório, reduzindo acoplamento e preparando o sistema para controle de rastreabilidade, permissões e logs mais estruturados.

## Alterações realizadas

- Criado `backend/services/auditoria.py`.
- Movida a função `registrar_auditoria` para o novo service.
- Removido o import direto de `AuditoriaSistema` de `routers/consultorio.py`.
- `routers/consultorio.py` passou a importar:

```python
from services.auditoria import registrar_auditoria
```

## Observação técnica
A função mantém o comportamento anterior: ela adiciona o registro de auditoria à sessão do banco, mas não executa `commit()` diretamente. O `commit()` continua sob responsabilidade da rota chamadora.

## Validação
Executar:

```bash
cd backend
uvicorn main:app --reload
```

Depois testar o Swagger em:

```txt
http://127.0.0.1:8000/docs
```
