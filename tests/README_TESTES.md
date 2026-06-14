# Testes automatizados — Sistema de Intervenção Farmacêutica

## 1. Instalar dependências

Dentro do ambiente virtual:

```cmd
pip install requests pytest
```

## 2. Iniciar o backend

Terminal 1:

```cmd
cd backend
uvicorn main:app --reload
```

## 3. Executar teste de fumaça

Terminal 2, na raiz do projeto:

```cmd
python tests\smoke_tests.py
```

## 4. Executar suíte pytest

```cmd
pytest -q tests
```

## 5. Variáveis opcionais

```cmd
set API_URL=http://127.0.0.1:8000
set API_EMAIL=admin@farmacia.local
set API_PASSWORD=admin123
```

## 6. O que os testes cobrem nesta versão

- login válido e inválido;
- usuário logado em `/me`;
- indicadores gerais;
- listagem de intervenções;
- pacientes clínicos;
- dashboards do consultório;
- dashboard farmacoterapêutico;
- alertas pendentes;
- presença das rotas críticas no OpenAPI.

Esta ainda é uma suíte inicial. Ela protege contra regressões estruturais e rotas quebradas, mas não substitui testes de criação, edição e exclusão de registros.
