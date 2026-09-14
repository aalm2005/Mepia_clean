-- MEPIA - alinea audit_results con el contrato usado por el pipeline y el chat.
-- Corrige instalaciones creadas desde 001_init.sql, donde CREATE TABLE IF NOT
-- EXISTS de 002_hybrid_schema.sql no agregó las columnas posteriores.

ALTER TABLE audit_results
    ADD COLUMN IF NOT EXISTS run_id UUID,
    ADD COLUMN IF NOT EXISTS business_id UUID REFERENCES businesses(id),
    ADD COLUMN IF NOT EXISTS date DATE,
    ADD COLUMN IF NOT EXISTS pipeline_layer TEXT,
    ADD COLUMN IF NOT EXISTS node_id TEXT,
    ADD COLUMN IF NOT EXISTS result_data JSONB,
    ADD COLUMN IF NOT EXISTS node_status TEXT;

ALTER TABLE audit_results
    ALTER COLUMN module DROP NOT NULL;

ALTER TABLE audit_results
    DROP CONSTRAINT IF EXISTS audit_results_pipeline_layer_check;

ALTER TABLE audit_results
    ADD CONSTRAINT audit_results_pipeline_layer_check
    CHECK (pipeline_layer IS NULL OR pipeline_layer IN ('sequential', 'parallel', 'loop'));

ALTER TABLE audit_results
    DROP CONSTRAINT IF EXISTS audit_results_node_status_check;

-- Los productores anteriores usaron estados que describian tanto la ejecucion
-- como el veredicto de dominio. Hay que convertirlos antes de validar el nuevo
-- contrato; de lo contrario, ADD CONSTRAINT falla al encontrar filas legacy.
-- pending representaba un handoff incompleto hacia N06, por eso pasa a partial.
-- Los estados desconocidos se conservan como filas auditables, marcando que su
-- ejecucion no cumple el contrato actual.
UPDATE audit_results
SET node_status = CASE lower(btrim(node_status))
    WHEN 'success' THEN 'success'
    WHEN 'completed' THEN 'success'
    WHEN 'complete' THEN 'success'
    WHEN 'approved' THEN 'success'
    WHEN 'approved_with_warning_cortafuegos' THEN 'success'
    WHEN 'partial' THEN 'partial'
    WHEN 'rejected' THEN 'partial'
    WHEN 'pending' THEN 'partial'
    WHEN 'failed' THEN 'failed'
    WHEN 'timeout' THEN 'timeout'
    WHEN 'error' THEN 'error'
    ELSE 'error'
END
WHERE node_status IS NOT NULL;

ALTER TABLE audit_results
    ADD CONSTRAINT audit_results_node_status_check
    CHECK (node_status IS NULL OR node_status IN ('success', 'partial', 'failed', 'timeout', 'error'));

CREATE INDEX IF NOT EXISTS idx_audit_results_run
    ON audit_results (run_id);

CREATE INDEX IF NOT EXISTS idx_audit_results_lookup
    ON audit_results (business_id, date, pipeline_layer, node_id);
