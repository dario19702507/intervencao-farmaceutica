# Passo 11A — Infraestrutura Documental

Implementa a base documental do Consultório Farmacêutico, sem OCR nesta etapa.

## Recursos

- Upload de documentos vinculado ao paciente clínico.
- Listagem por paciente.
- Download do arquivo.
- Atualização de metadados.
- Inativação lógica.

## Tipos iniciais

- RECEITA
- LAUDO
- EXAME
- DOCUMENTO_PESSOAL
- TERMO
- OUTRO

## Rotas

- `GET /consultorio/documentos/opcoes`
- `POST /consultorio/paciente-clinico/{paciente_id}/documentos`
- `GET /consultorio/paciente-clinico/{paciente_id}/documentos`
- `GET /consultorio/documentos/{documento_id}/download`
- `PUT /consultorio/documentos/{documento_id}/metadados`
- `DELETE /consultorio/documentos/{documento_id}`

## Observação

Os arquivos são salvos localmente em `backend/uploads/documentos`. Em produção, recomenda-se migrar para storage externo, como Supabase Storage ou S3 compatível.
