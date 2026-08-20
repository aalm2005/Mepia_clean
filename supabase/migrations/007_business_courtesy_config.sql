-- Config Tipo B: cortesia permitida por responsable (items gratis para uso
-- personal/regalo del empleado, autorizados por el dueño -- no cuenta como
-- anomalia hasta que se exceda). Default de fabrica: 1 item, valuado al
-- producto mas caro del catalogo de recetas del negocio (o $100 MXN si el
-- negocio no tiene catalogo de precios configurado todavia).
CREATE TABLE IF NOT EXISTS business_courtesy_config (
    business_id UUID NOT NULL REFERENCES businesses(id),
    activo BOOLEAN NOT NULL DEFAULT true,  -- apagar = tratar toda cortesia como excedente (comportamiento previo a esta funcion)
    items_permitidos_por_persona INT NOT NULL DEFAULT 1,
    monto_por_item NUMERIC(10,2) DEFAULT NULL,  -- NULL = usar producto mas caro
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (business_id)
);

ALTER TABLE business_courtesy_config ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_all" ON business_courtesy_config
    FOR ALL USING (true) WITH CHECK (true);
