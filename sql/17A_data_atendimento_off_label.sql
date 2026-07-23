-- Patch 17A — farmacoterapia off-label
-- Seguro para PostgreSQL/Supabase; pode ser executado mais de uma vez.
ALTER TABLE medicamentos_uso
    ADD COLUMN IF NOT EXISTS uso_off_label VARCHAR DEFAULT 'NAO_AVALIADO' NOT NULL;
ALTER TABLE medicamentos_uso
    ADD COLUMN IF NOT EXISTS justificativa_off_label TEXT;
ALTER TABLE medicamentos_uso
    ADD COLUMN IF NOT EXISTS evidencia_off_label TEXT;

UPDATE medicamentos_uso
SET uso_off_label = 'NAO_AVALIADO'
WHERE uso_off_label IS NULL OR uso_off_label = '';
