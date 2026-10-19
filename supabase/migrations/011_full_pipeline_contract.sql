-- Completa contratos existentes de ingesta, cálculo y memoria.
-- Aditiva e idempotente; conserva filas y valores históricos.
BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '30s';

CREATE TABLE IF NOT EXISTS public.shift_audit_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id uuid NOT NULL REFERENCES public.businesses(id) ON DELETE CASCADE,
    sucursal_id text NOT NULL,
    date date NOT NULL,
    turno text NOT NULL,
    apertura numeric(12,2) NOT NULL,
    cierre_x numeric(12,2) NOT NULL,
    cierre_z numeric(12,2) NOT NULL,
    sobrante_faltante numeric(12,2) NOT NULL,
    cancellations jsonb DEFAULT '[]'::jsonb,
    reprints jsonb DEFAULT '[]'::jsonb,
    clock_records jsonb DEFAULT '[]'::jsonb,
    created_at timestamptz DEFAULT now()
);
-- No aplicar la antigua conversión 006, que descartaba los conteos.
DO $$ BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns
        WHERE table_schema='public' AND table_name='shift_audit_events'
          AND column_name='reprints' AND udt_name<>'jsonb') THEN
        RAISE EXCEPTION 'reprints requiere revisión de conversión; no se modificaron sus datos';
    END IF;
END $$;
ALTER TABLE public.shift_audit_events
    ADD COLUMN IF NOT EXISTS shift_id text,
    ADD COLUMN IF NOT EXISTS start_time timestamptz,
    ADD COLUMN IF NOT EXISTS end_time timestamptz;
CREATE UNIQUE INDEX IF NOT EXISTS uq_shift_audit_lookup
    ON public.shift_audit_events (business_id,date,sucursal_id,turno);

CREATE TABLE IF NOT EXISTS public.inventory_daily (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id uuid NOT NULL REFERENCES public.businesses(id) ON DELETE CASCADE,
    date date NOT NULL,
    ingredient_id text NOT NULL,
    ingredient_name text NOT NULL,
    unit text NOT NULL,
    consumo_teorico numeric(12,4) NOT NULL,
    waste_recorded numeric(12,4) DEFAULT 0,
    current_stock numeric(12,4) NOT NULL,
    unit_cost numeric(12,4) NOT NULL,
    created_at timestamptz DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_inventory_daily_lookup
    ON public.inventory_daily (business_id,date,ingredient_id);

CREATE TABLE IF NOT EXISTS public.delivery_platform_config (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id uuid NOT NULL REFERENCES public.businesses(id) ON DELETE CASCADE,
    platform text NOT NULL,
    commission_rate numeric(5,4) NOT NULL,
    effective_date date NOT NULL,
    created_at timestamptz DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_delivery_platform_config
    ON public.delivery_platform_config (business_id,platform,effective_date);

-- Nuevas tablas privadas. El backend usa service_role; no se amplía acceso anónimo.
ALTER TABLE public.shift_audit_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.inventory_daily ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.delivery_platform_config ENABLE ROW LEVEL SECURITY;
GRANT SELECT,INSERT,UPDATE,DELETE ON public.shift_audit_events,
    public.inventory_daily,public.delivery_platform_config TO service_role;

-- Campos históricos desconocidos permanecen NULL; defaults solo para nuevas filas.
ALTER TABLE public.businesses ADD COLUMN IF NOT EXISTS multi_sucursal boolean;
ALTER TABLE public.businesses ALTER COLUMN multi_sucursal SET DEFAULT false;
ALTER TABLE public.cash_counts
    ADD COLUMN IF NOT EXISTS created_at timestamptz,
    ADD COLUMN IF NOT EXISTS updated_at timestamptz;
ALTER TABLE public.cash_counts ALTER COLUMN created_at SET DEFAULT now();
ALTER TABLE public.transactions ADD COLUMN IF NOT EXISTS needs_human_review boolean;
ALTER TABLE public.transactions ALTER COLUMN needs_human_review SET DEFAULT false;
ALTER TABLE public.pos_inputs
    ADD COLUMN IF NOT EXISTS product_id uuid REFERENCES public.recipes(id),
    ADD COLUMN IF NOT EXISTS quantity numeric;
ALTER TABLE public.mepia_memory
    ADD COLUMN IF NOT EXISTS attempt_count integer,
    ADD COLUMN IF NOT EXISTS embedded_at timestamptz,
    ADD COLUMN IF NOT EXISTS updated_at timestamptz;
ALTER TABLE public.mepia_memory ALTER COLUMN attempt_count SET DEFAULT 0;
ALTER TABLE public.mepia_memory ALTER COLUMN updated_at SET DEFAULT now();

-- pos_inputs contiene registros históricos múltiples por fecha. No deduplicarlos
-- ni imponer unicidad que los borre: el agregado API usa una RPC atómica.
CREATE OR REPLACE FUNCTION public.upsert_pos_daily(p_record jsonb)
RETURNS uuid LANGUAGE plpgsql SECURITY INVOKER SET search_path = '' AS $$
DECLARE
    v_business uuid := (p_record->>'business_id')::uuid;
    v_date date := (p_record->>'date')::date;
    v_count integer;
    v_id uuid;
BEGIN
    IF v_business IS NULL OR v_date IS NULL THEN
        RAISE EXCEPTION 'MEPIA_POS_INVALID_KEY';
    END IF;
    PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(
        'mepia.pos_inputs:'||v_business::text||':'||v_date::text,0));
    SELECT count(*) INTO v_count FROM public.pos_inputs
        WHERE business_id=v_business AND date=v_date;
    IF v_count>1 THEN
        RAISE EXCEPTION 'MEPIA_POS_DATE_AMBIGUOUS';
    ELSIF v_count=1 THEN
        UPDATE public.pos_inputs SET
            total_sales=(p_record->>'total_sales')::numeric,
            cash_sales=(p_record->>'cash_sales')::numeric,
            card_sales=(p_record->>'card_sales')::numeric,
            refunds=(p_record->>'refunds')::numeric,
            num_transactions=(p_record->>'num_transactions')::integer
        WHERE business_id=v_business AND date=v_date RETURNING id INTO v_id;
    ELSE
        INSERT INTO public.pos_inputs (business_id,date,total_sales,cash_sales,
            card_sales,refunds,num_transactions)
        VALUES (v_business,v_date,(p_record->>'total_sales')::numeric,
            (p_record->>'cash_sales')::numeric,(p_record->>'card_sales')::numeric,
            (p_record->>'refunds')::numeric,(p_record->>'num_transactions')::integer)
        RETURNING id INTO v_id;
    END IF;
    RETURN v_id;
END $$;
-- Supabase puede conceder EXECUTE explícito mediante privilegios por defecto.
-- Revocar PUBLIC no elimina los grants propios de anon/authenticated.
REVOKE ALL ON FUNCTION public.upsert_pos_daily(jsonb) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.upsert_pos_daily(jsonb) TO service_role;
-- Los otros upserts sí tienen claves históricas únicas, comprobadas antes.
CREATE UNIQUE INDEX IF NOT EXISTS uq_cash_counts_business_date
    ON public.cash_counts (business_id,date);
CREATE UNIQUE INDEX IF NOT EXISTS uq_metric_status_business_date_metric
    ON public.metric_status (business_id,date,metric_name);
NOTIFY pgrst, 'reload schema';
COMMIT;
