-- =============================================================================
-- MEPIA — Script consolidado para aplicar en Supabase SQL Editor
-- Consolidado histórico: no incluye el contrato posterior 011_full_pipeline_contract.sql.
-- No usar como actualización de una base existente: contiene semillas/conversiones.
-- La unificación de principal usa operations/unify_primary.sql y luego 011,
-- con inventario previo y autorización; ver docs/database_unification.md.
-- Ejecutar en orden. Si alguna tabla ya existe, los IF NOT EXISTS la saltan.
-- URL del proyecto: https://supabase.com/dashboard/project/iuhadbeahmssruwuawvu/sql
-- =============================================================================

-- ─────────────────────────────────────────────────────────────────────────────
-- PASO 1: Extensiones
-- ─────────────────────────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS vector;

-- ─────────────────────────────────────────────────────────────────────────────
-- PASO 2: Tablas base (001 + 002)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS businesses (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_name    TEXT NOT NULL,
    industry_sector  TEXT,
    currency         TEXT NOT NULL DEFAULT 'MXN',
    opening_date     DATE,
    operating_hours  JSONB DEFAULT '{"open": "08:00", "close": "22:00"}',
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS business_onboarding (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id                 UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    brand_voice                 TEXT,
    prohibited_recommendations  JSONB DEFAULT '[]',
    priority_focus              TEXT CHECK (priority_focus IN ('efficiency', 'quality', 'growth')),
    max_cash_discrepancy_pct    NUMERIC(5,4),
    max_cash_discrepancy_abs    NUMERIC(12,2),
    margin_warning_threshold    NUMERIC(5,4),
    margin_critical_threshold   NUMERIC(5,4),
    cost_spike_threshold_pct    NUMERIC(5,4),
    audit_rules                 JSONB DEFAULT '{}',
    completed_at                TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (business_id)
);

CREATE TABLE IF NOT EXISTS business_fixed_costs (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id             UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    concept                 TEXT NOT NULL,
    amount                  NUMERIC(12,2),
    expected_monthly_amount NUMERIC(12,2),
    tolerance_pct           NUMERIC(5,4) DEFAULT 0.05,
    recurrence              TEXT DEFAULT 'monthly',
    expense_behavior        TEXT CHECK (expense_behavior IN ('FIXED', 'VARIABLE', 'CAPEX')),
    is_active               BOOLEAN NOT NULL DEFAULT true,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS documents (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id         UUID NOT NULL REFERENCES businesses(id),
    storage_path        TEXT,
    filename            TEXT,
    document_type       TEXT CHECK (document_type IN ('PDF', 'XML', 'JPG')),
    ocr_status          TEXT DEFAULT 'pending' CHECK (ocr_status IN ('pending', 'processed', 'error')),
    ocr_confidence      NUMERIC(5,2),
    needs_human_review  BOOLEAN NOT NULL DEFAULT false,
    uploaded_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    extracted_data      JSONB
);

CREATE TABLE IF NOT EXISTS transactions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id         UUID NOT NULL REFERENCES businesses(id),
    document_id         UUID REFERENCES documents(id),
    type                TEXT CHECK (type IN ('ingreso', 'egreso')),
    category            TEXT CHECK (category IN ('venta', 'nomina', 'proveedor', 'impuesto')),
    amount              NUMERIC(12,2),
    tax_amount          NUMERIC(12,2),
    transaction_date    DATE,
    supplier_name       TEXT,
    concept             TEXT,
    document_reference  TEXT,
    expense_behavior    TEXT CHECK (expense_behavior IN ('FIXED', 'VARIABLE', 'CAPEX')),
    metadata            JSONB,
    raw_metadata        JSONB,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS pos_inputs (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id      UUID NOT NULL REFERENCES businesses(id),
    date             DATE NOT NULL,
    total_sales      NUMERIC(12,2),
    cash_sales       NUMERIC(12,2),
    card_sales       NUMERIC(12,2),
    refunds          NUMERIC(12,2) DEFAULT 0,
    num_transactions INT
);

CREATE TABLE IF NOT EXISTS cash_counts (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id      UUID NOT NULL REFERENCES businesses(id),
    date             DATE NOT NULL,
    initial_float    NUMERIC(12,2),
    actual_counted   NUMERIC(12,2),
    cash_payouts     NUMERIC(12,2) DEFAULT 0,
    recorded_by      TEXT
);

CREATE TABLE IF NOT EXISTS recipes (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id      UUID NOT NULL REFERENCES businesses(id),
    product_name     TEXT NOT NULL,
    sale_price       NUMERIC(12,2),
    ingredients      JSONB,
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS daily_context (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id      UUID NOT NULL REFERENCES businesses(id),
    date             DATE NOT NULL,
    tags             JSONB DEFAULT '{}',
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS metric_status (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id      UUID NOT NULL REFERENCES businesses(id),
    date             DATE NOT NULL,
    metric_name      TEXT NOT NULL,
    status           TEXT NOT NULL CHECK (status IN ('dormant', 'active', 'blocked')),
    missing_fields   JSONB DEFAULT '[]',
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS audit_results (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id           UUID,
    source_s3_result_id UUID REFERENCES audit_results(id) ON DELETE SET NULL,
    business_id      UUID REFERENCES businesses(id),
    date             DATE,
    pipeline_layer   TEXT CHECK (pipeline_layer IN ('sequential', 'parallel', 'loop')),
    node_id          TEXT,
    module           TEXT,
    archetype        TEXT,
    raw_result       JSONB,
    result_data      JSONB,
    copilot_phrase   TEXT,
    node_status      TEXT CHECK (node_status IN ('success', 'partial', 'failed', 'timeout', 'error')),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Compatibilidad con instalaciones creadas desde 001_init.sql. En esas bases,
-- CREATE TABLE IF NOT EXISTS no agrega las columnas del contrato actual.
ALTER TABLE audit_results
    ADD COLUMN IF NOT EXISTS run_id UUID,
    ADD COLUMN IF NOT EXISTS source_s3_result_id UUID,
    ADD COLUMN IF NOT EXISTS business_id UUID REFERENCES businesses(id),
    ADD COLUMN IF NOT EXISTS date DATE,
    ADD COLUMN IF NOT EXISTS pipeline_layer TEXT,
    ADD COLUMN IF NOT EXISTS node_id TEXT,
    ADD COLUMN IF NOT EXISTS result_data JSONB,
    ADD COLUMN IF NOT EXISTS node_status TEXT;

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

ALTER TABLE audit_results ALTER COLUMN module DROP NOT NULL;
ALTER TABLE audit_results DROP CONSTRAINT IF EXISTS audit_results_pipeline_layer_check;
ALTER TABLE audit_results ADD CONSTRAINT audit_results_pipeline_layer_check
    CHECK (pipeline_layer IS NULL OR pipeline_layer IN ('sequential', 'parallel', 'loop'));
ALTER TABLE audit_results DROP CONSTRAINT IF EXISTS audit_results_node_status_check;

-- Normaliza filas escritas por versiones anteriores antes de instalar el
-- constraint vigente. Si se agrega el constraint primero, PostgreSQL valida las
-- filas legacy y aborta al encontrar completed/complete/approved/rejected/pending.
-- pending representaba un handoff incompleto hacia N06, por eso pasa a partial.
-- Un valor desconocido se marca error para conservar la evidencia de la fila.
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

ALTER TABLE audit_results ADD CONSTRAINT audit_results_node_status_check
    CHECK (node_status IS NULL OR node_status IN ('success', 'partial', 'failed', 'timeout', 'error'));

CREATE TABLE IF NOT EXISTS circuit_breaker_state (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id          UUID NOT NULL REFERENCES businesses(id),
    date                 DATE NOT NULL,
    node_id              TEXT NOT NULL CHECK (node_id IN ('N07', 'N08', 'N09')),
    consecutive_failures INT NOT NULL DEFAULT 0,
    circuit_status       TEXT NOT NULL DEFAULT 'closed' CHECK (circuit_status IN ('closed', 'open')),
    opened_at            TIMESTAMPTZ,
    reset_by             UUID,
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS unit_conversions (
    id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_unit TEXT NOT NULL,
    to_unit   TEXT NOT NULL,
    factor    NUMERIC NOT NULL
);

INSERT INTO unit_conversions (from_unit, to_unit, factor) VALUES
    ('kg',     'g',      1000),
    ('L',      'ml',     1000),
    ('unidad', 'unidad', 1)
ON CONFLICT DO NOTHING;

-- ─────────────────────────────────────────────────────────────────────────────
-- PASO 3: Memoria semántica (003)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS mepia_memory (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id         UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    -- source_audit_run_id guarda el run_id como dato de trazabilidad (sin FK formal
    -- porque audit_results.run_id no es PK — puede haber N filas por run).
    source_audit_run_id UUID,
    content             TEXT NOT NULL,
    metadata            JSONB NOT NULL DEFAULT '{}',
    embedding           VECTOR(1536),
    status              TEXT NOT NULL DEFAULT 'pending_embed'
                            CHECK (status IN ('pending_embed', 'embedded', 'failed')),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ─────────────────────────────────────────────────────────────────────────────
-- PASO 4: Índices
-- ─────────────────────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_transactions_metadata         ON transactions USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_transactions_raw_metadata     ON transactions USING GIN (raw_metadata);
CREATE INDEX IF NOT EXISTS idx_documents_extracted           ON documents    USING GIN (extracted_data);
CREATE INDEX IF NOT EXISTS idx_transactions_business_date    ON transactions (business_id, transaction_date);
CREATE INDEX IF NOT EXISTS idx_transactions_expense_behavior ON transactions (business_id, expense_behavior);
CREATE INDEX IF NOT EXISTS idx_documents_review              ON documents    (needs_human_review) WHERE needs_human_review = true;
CREATE INDEX IF NOT EXISTS idx_daily_context_lookup          ON daily_context (business_id, date);
CREATE INDEX IF NOT EXISTS idx_metric_status_lookup          ON metric_status (business_id, date, status);
CREATE INDEX IF NOT EXISTS idx_recipes_business              ON recipes (business_id);
CREATE INDEX IF NOT EXISTS idx_audit_results_run             ON audit_results (run_id);
CREATE INDEX IF NOT EXISTS idx_audit_results_lookup          ON audit_results (business_id, date, pipeline_layer, node_id);
CREATE INDEX IF NOT EXISTS idx_audit_results_s3_lineage      ON audit_results (business_id, source_s3_result_id, node_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_circuit_breaker_lookup        ON circuit_breaker_state (business_id, date, node_id);
CREATE INDEX IF NOT EXISTS idx_circuit_breaker_open          ON circuit_breaker_state (node_id, circuit_status) WHERE circuit_status = 'open';
CREATE INDEX IF NOT EXISTS idx_onboarding_business           ON business_onboarding (business_id);
CREATE INDEX IF NOT EXISTS idx_fixed_costs_business_active   ON business_fixed_costs (business_id, is_active);
CREATE INDEX IF NOT EXISTS idx_memory_embedding              ON mepia_memory USING hnsw (embedding vector_cosine_ops) WHERE embedding IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_memory_business               ON mepia_memory (business_id);
CREATE INDEX IF NOT EXISTS idx_memory_business_created       ON mepia_memory (business_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_memory_pending                ON mepia_memory (status) WHERE status IN ('pending_embed', 'failed');
CREATE INDEX IF NOT EXISTS idx_memory_metadata               ON mepia_memory USING GIN (metadata);

-- ─────────────────────────────────────────────────────────────────────────────
-- PASO 5: Función RPC para búsqueda vectorial
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION match_mepia_memory(
    query_embedding    VECTOR(1536),
    business_id_filter UUID,
    match_count        INT DEFAULT 5
)
RETURNS TABLE (
    id         UUID,
    content    TEXT,
    metadata   JSONB,
    similarity FLOAT,
    created_at TIMESTAMPTZ
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        m.id,
        m.content,
        m.metadata,
        1 - (m.embedding <=> query_embedding) AS similarity,
        m.created_at
    FROM mepia_memory m
    WHERE
        m.business_id = business_id_filter
        AND m.status = 'embedded'
        AND m.embedding IS NOT NULL
    ORDER BY m.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- ─────────────────────────────────────────────────────────────────────────────
-- PASO 6: RLS — Row Level Security
-- ─────────────────────────────────────────────────────────────────────────────

ALTER TABLE businesses              ENABLE ROW LEVEL SECURITY;
ALTER TABLE business_onboarding     ENABLE ROW LEVEL SECURITY;
ALTER TABLE business_fixed_costs    ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents               ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions            ENABLE ROW LEVEL SECURITY;
ALTER TABLE pos_inputs              ENABLE ROW LEVEL SECURITY;
ALTER TABLE cash_counts             ENABLE ROW LEVEL SECURITY;
ALTER TABLE recipes                 ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_context           ENABLE ROW LEVEL SECURITY;
ALTER TABLE metric_status           ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_results           ENABLE ROW LEVEL SECURITY;
ALTER TABLE circuit_breaker_state   ENABLE ROW LEVEL SECURITY;
ALTER TABLE mepia_memory            ENABLE ROW LEVEL SECURITY;

-- service_role: acceso total (backend Python usa SUPABASE_SERVICE_ROLE_KEY)
DO $$
DECLARE
    tbl TEXT;
BEGIN
    FOREACH tbl IN ARRAY ARRAY[
        'businesses','business_onboarding','business_fixed_costs',
        'documents','transactions','pos_inputs','cash_counts',
        'recipes','daily_context','metric_status','audit_results',
        'circuit_breaker_state','mepia_memory'
    ]
    LOOP
        EXECUTE format(
            'DROP POLICY IF EXISTS service_role_all ON %I;
             CREATE POLICY service_role_all ON %I FOR ALL TO service_role USING (true) WITH CHECK (true);',
            tbl, tbl
        );
    END LOOP;
END $$;

-- anon: solo lectura en businesses y audit_results (frontend Next.js con anon key)
DROP POLICY IF EXISTS anon_read_businesses    ON businesses;
DROP POLICY IF EXISTS anon_read_audit_results ON audit_results;

-- La lectura del frontend requiere sesión y propiedad; se instala al final (010).

-- ─────────────────────────────────────────────────────────────────────────────
-- PASO 7: Seed — negocio de desarrollo
-- ─────────────────────────────────────────────────────────────────────────────

INSERT INTO businesses (id, business_name, industry_sector, currency, opening_date, operating_hours)
VALUES (
    'a0000000-0000-0000-0000-000000000001',
    'MEPIA Dev',
    'cafetería',
    'MXN',
    CURRENT_DATE,
    '{"open": "08:00", "close": "22:00"}'
)
ON CONFLICT (id) DO NOTHING;

-- UUID fijo para dev: a0000000-0000-0000-0000-000000000001
-- Ya está en .env.local como NEXT_PUBLIC_BUSINESS_ID=mepia-dev
-- Actualizar .env.local con este UUID si es necesario.
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
