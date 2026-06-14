# Passo 12D.1 — Extrator Estruturado de LME/CEAF

Este pacote acrescenta um extrator específico para LME/Laudo do Componente Especializado da Assistência Farmacêutica.

## Entregas

- Novo módulo `backend/services/extratores/lme_extractor.py`.
- Integração com `services/ocr_documentos.py`.
- Campos estruturados retornados dentro de `campos_sugeridos.campos_estruturados`.
- Nenhuma atualização automática em cadastro, vigência, agenda, notificação ou WhatsApp.

## Campos iniciais

- nome do paciente;
- nome da mãe;
- CID;
- diagnóstico;
- medicamento;
- CNS;
- município;
- data de solicitação, quando presente.

## Validação

```cmd
pytest -q tests
python tests\smoke_tests.py
```
