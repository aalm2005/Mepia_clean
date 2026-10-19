-- Unificación autorizada: ejecutar en el proyecto principal MEPIA.
-- Reutiliza las migraciones 009 y 010 sin reescribir auditorías históricas.
-- No copia fixtures de pruebas, no elimina filas y no asigna propietarios.
BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '30s';
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

-- Paso 5: propiedad explícita y lectura por propietario. Aplicar solo con autorización.
-- No inferir dueños para negocios históricos: NULL implica acceso denegado.

ALTER TABLE public.businesses ADD COLUMN IF NOT EXISTS owner_id uuid
    REFERENCES auth.users(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_businesses_owner ON public.businesses(owner_id);
ALTER TABLE public.businesses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_results ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS anon_read_businesses ON public.businesses;
DROP POLICY IF EXISTS anon_read_audit_results ON public.audit_results;
DROP POLICY IF EXISTS owner_read_businesses ON public.businesses;
DROP POLICY IF EXISTS owner_read_audit_results ON public.audit_results;
CREATE POLICY owner_read_businesses ON public.businesses FOR SELECT TO authenticated
    USING (owner_id = (SELECT auth.uid()));
CREATE POLICY owner_read_audit_results ON public.audit_results FOR SELECT TO authenticated
    USING (EXISTS (SELECT 1 FROM public.businesses b
                  WHERE b.id = audit_results.business_id AND b.owner_id = (SELECT auth.uid())));


COMMIT;
