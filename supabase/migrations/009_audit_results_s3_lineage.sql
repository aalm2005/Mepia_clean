-- MEPIA - linaje exacto desde cada resultado descendiente hasta la fila S3.
--
-- Las filas historicas quedan en NULL deliberadamente: business_id + date no
-- demuestra que dos filas pertenezcan a la misma ejecucion y no es seguro
-- reconstruir esa relacion de forma retrospectiva.

ALTER TABLE audit_results
    ADD COLUMN IF NOT EXISTS source_s3_result_id UUID;

-- No se elimina una FK ya instalada: una reejecucion debe ser idempotente y no
-- abrir una ventana sin integridad referencial. NOT VALID evita escanear la
-- tabla mientras se toma el bloqueo inicial; VALIDATE comprueba despues las
-- filas historicas (que deliberadamente conservan NULL).
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'audit_results'::regclass
          AND conname = 'audit_results_source_s3_result_id_fkey'
    ) THEN
        EXECUTE $ddl$
            ALTER TABLE audit_results
                ADD CONSTRAINT audit_results_source_s3_result_id_fkey
                FOREIGN KEY (source_s3_result_id)
                REFERENCES audit_results(id) ON DELETE SET NULL
                NOT VALID
        $ddl$;
    END IF;
END
$$;

ALTER TABLE audit_results
    VALIDATE CONSTRAINT audit_results_source_s3_result_id_fkey;

CREATE INDEX IF NOT EXISTS idx_audit_results_s3_lineage
    ON audit_results (business_id, source_s3_result_id, node_id, created_at DESC);
