# Passo 13B.2 — Excel em abas

Ajusta os relatórios gerenciais para exportação em `.xlsx`, com seções separadas por abas:

- Indicadores
- Eventos
- Processos Vencendo
- Processos Vencidos
- Processos Incompletos
- Documentos Rejeitados

O CSV com `;` foi mantido para compatibilidade simples, mas o botão principal do frontend passa a ser **Exportar Excel**.

## Dependência

Se necessário, instale:

```cmd
pip install openpyxl
```

## Testes

```cmd
pytest -q tests
python tests\smoke_tests.py
```
