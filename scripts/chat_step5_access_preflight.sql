-- Paso 5: inspección de solo lectura en MEPIA - PRUEBAS.
-- Confirmar el proyecto en el panel antes de ejecutar. No devuelve identidades,
-- correos, credenciales, textos de auditoría ni valores de métricas.
SELECT jsonb_build_object(
    'tables', (SELECT jsonb_agg(jsonb_build_object(
        'table', c.relname, 'rls_enabled', c.relrowsecurity))
        FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public' AND c.relname IN ('businesses', 'audit_results')),
    'columns', (SELECT jsonb_agg(jsonb_build_object(
        'table', table_name, 'column', column_name, 'type', data_type,
        'nullable', is_nullable))
        FROM information_schema.columns
        WHERE table_schema = 'public' AND (
            (table_name = 'businesses' AND column_name IN ('id', 'owner_id')) OR
            (table_name = 'audit_results' AND column_name IN ('id', 'business_id', 'source_s3_result_id')))),
    'owner_constraints', (SELECT coalesce(jsonb_agg(pg_get_constraintdef(c.oid)), '[]'::jsonb)
        FROM pg_constraint c
        WHERE c.conrelid = 'public.businesses'::regclass
          AND c.contype = 'f' AND pg_get_constraintdef(c.oid) LIKE '%owner_id%'),
    'owner_index', (SELECT coalesce(jsonb_agg(indexdef), '[]'::jsonb)
        FROM pg_indexes WHERE schemaname = 'public' AND tablename = 'businesses'
          AND indexname = 'idx_businesses_owner'),
    'policies', (SELECT jsonb_agg(jsonb_build_object(
        'table', tablename, 'name', policyname, 'roles', roles, 'command', cmd,
        'using', qual, 'with_check', with_check, 'permissive', permissive))
        FROM pg_policies WHERE schemaname = 'public'
          AND tablename IN ('businesses', 'audit_results')),
    'business_count', (SELECT count(*) FROM public.businesses),
    'businesses_with_owner', (SELECT count(*) FROM public.businesses b
        WHERE to_jsonb(b)->>'owner_id' IS NOT NULL),
    'audit_count', (SELECT count(*) FROM public.audit_results),
    'auth_user_count', (SELECT count(*) FROM auth.users)
) AS step5_access_preflight;
