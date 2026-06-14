# Passo 6H — Relatórios do Consultório

Foram separados relatórios PDF/autônomos para `backend/services/relatorios_consultorio.py`.

Movidos nesta subetapa:
- declaração de atendimento rápido;
- laudo de bioimpedância;
- relatório mensal do consultório;
- PDF do prontuário clínico simples;
- PDF da evolução farmacêutica.

Os endpoints foram preservados no `routers/consultorio.py`, que agora funciona como wrapper para o service.

Relatórios científicos/exportações mais complexos foram mantidos no router para uma próxima subetapa, pois dependem de outros dashboards internos.
