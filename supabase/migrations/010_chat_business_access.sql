-- Paso 5: propiedad explícita y lectura por propietario. Aplicar solo con autorización.
-- No inferir dueños para negocios históricos: NULL implica acceso denegado.
BEGIN;
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
