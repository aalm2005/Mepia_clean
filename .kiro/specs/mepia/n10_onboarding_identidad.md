# N10 — Onboarding de Identidad del Negocio

**Integración local — 15-oct-2026:** ajustes automáticos incorporados y
INC-044/045 resueltas. 151 pruebas/41 subpruebas, Edge N10 14/14 y general 25/25,
build/tipos código 0. Usuario confirma acceso a Documentos y ajustes avanzados.
Rama `codex/chatbot-q4`, HEAD `f9cfddc`, cambio sin commit/push.
[Contrato, evidencia y límites](../../../docs/onboarding_defaults_integration.md).
El análisis real con archivos nuevos requiere el perfil completo y claves del
motor; no se valida por estas pruebas de configuración.

**Capa:** Transversal (prerequisito de Layer 3) | **Endpoint:** `POST /business/{id}/onboarding`
**Archivo de implementación:** `api/onboarding.py`; router registrado por `api.main` y `api.chat_app`
**Depende de:** `businesses` (debe existir), `mepia_memory` (escribe chunk `node_origin: "onboarding"`)
**Bloquea:** Layer 3 requiere onboarding; la ingesta de documentos no lo requiere

---

## Responsabilidad

Inyectar el "Lente del CEO" en `mepia_memory` y registrar los parámetros de auditoría
del negocio. Este endpoint es un prerequisito para Layer 3, pero no para subir documentos.
Si el usuario no configuró los parámetros avanzados antes del primer análisis, la interfaz
guarda automáticamente valores recomendados. Los usuarios pueden personalizarlos después.

Defaults iniciales usados por la interfaz:

| Parámetro | Valor |
|---|---:|
| Discrepancia máxima de caja | 2% o $150 MXN |
| Margen warning | 15% |
| Margen crítico | 8% |
| Incremento de costo | 10% |
| Foco | Eficiencia |
| Frecuencia | Diaria |
| Costos esperados | Ninguno; no se inventan montos |

No es solo un registro de marca — es la configuración del motor de auditoría.

---

## Endpoint

### `POST /business/{business_id}/onboarding`

**Path param:** `business_id` — UUID del negocio ya creado en `businesses`.
GET/POST/PUT requieren `Authorization: Bearer <JWT>`. El servidor verifica firma,
claims, vigencia y `owner_id` antes de acceder a la configuración. No acepta
identidad/negocio en el body Python. El proxy Next recibe `business_id` para
construir el path y lo retira del body reenviado; nunca infiere autorización
del selector. Respuestas correctas con `Cache-Control: private, no-store`.

**Request body — `OnboardingIdentityPayload`:**

```python
class AuditTolerances(BaseModel):
    """Umbrales que el CFO Forense usa para clasificar anomalías."""
    max_cash_discrepancy_pct: float = Field(
        gt=0, le=1,
        description="Diferencia máxima aceptable entre POS y caja física. Ej: 0.02 = 2%"
    )
    max_cash_discrepancy_abs: Decimal = Field(
        ge=0,
        description="Diferencia absoluta máxima en MXN. Ej: 150.00"
    )
    # Regla: se usa el umbral que sea MÁS PERMISIVO (OR, no AND)
    # Si diff < 2% O diff < $150 → no es anomalía crítica

    margin_warning_threshold: float = Field(
        gt=0, le=1,
        description="Margen neto mínimo esperado. Por debajo → warning. Ej: 0.15 = 15%"
    )
    margin_critical_threshold: float = Field(
        gt=0, le=1,
        description="Margen neto crítico. Por debajo → alerta roja. Ej: 0.08 = 8%"
    )

    cost_spike_threshold_pct: float = Field(
        gt=0, le=1,
        description="Incremento de costo que dispara alerta. Ej: 0.10 = 10% sobre período anterior"
    )


class ExpectedCostStructure(BaseModel):
    """Estructura de costos fijos esperada — base para detectar desviaciones."""
    concept: str
    expected_monthly_amount: Decimal = Field(ge=0)
    tolerance_pct: float = Field(
        ge=0, le=1,
        description="Variación aceptable sobre el monto esperado. Ej: 0.05 = ±5%"
    )
    expense_behavior: Literal["FIXED", "VARIABLE", "CAPEX"]


class AuditRules(BaseModel):
    """Reglas de auditoría específicas del negocio."""
    red_alert_triggers: list[str] = Field(
        description=(
            "Condiciones que siempre generan alerta roja, sin importar umbrales. "
            "Ej: ['caja_negativa', 'ventas_cero_dia_laboral', 'proveedor_no_registrado']"
        )
    )
    ignored_anomaly_types: list[str] = Field(
        default=[],
        description=(
            "Tipos de anomalía que el negocio acepta como normales. "
            "Ej: ['cost_spike'] si el negocio tiene precios de insumos muy volátiles."
        )
    )
    audit_frequency: Literal["daily", "weekly"] = "daily"


class BrandIdentity(BaseModel):
    """Identidad de marca — el 'Lente del CEO' que N11 usa para el tono del reporte."""
    brand_voice: str = Field(
        max_length=500,
        description=(
            "Descripción del tono y valores del negocio. "
            "Ej: 'hospitalidad invisible, espacio seguro, sin fricción'"
        )
    )
    prohibited_recommendations: list[str] = Field(
        description=(
            "Tipos de recomendaciones que contradicen la identidad. "
            "Ej: ['fidelización ostentosa', 'marketing agresivo', 'mecánicas de casino']"
        )
    )
    priority_focus: Literal["efficiency", "quality", "growth"] = Field(
        description="Foco principal del dueño — mapea al CEO Archetype"
    )


class OnboardingIdentityPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    brand_identity: BrandIdentity
    audit_tolerances: AuditTolerances
    expected_cost_structure: list[ExpectedCostStructure] = Field(default_factory=list)
    audit_rules: AuditRules
```

**Response 201 — Creado:**
```json
{
  "business_id": "uuid-v4",
  "onboarding_status": "complete",
  "memory_chunk_id": "uuid-v4",
  "audit_config_stored": true,
  "completed_at": "2024-01-15T10:00:00Z"
}
```

**Códigos de error:**

| HTTP | Condición |
|------|-----------|
| 401  | Sesión ausente, inválida o vencida; sin acceso a DB |
| 403  | Negocio ajeno, inexistente o sin propietario; sin acceso a ajustes |
| 409  | Onboarding ya completado — usar `PUT` para actualizar |
| 422  | Validación Pydantic fallida (ej. `max_cash_discrepancy_pct > 1`) |
| 503  | Fallo de verificación de propiedad o almacenamiento; mensaje saneado |

---

### `PUT /business/{business_id}/onboarding`

Actualiza la configuración de onboarding. Mismo body que `POST`.
Crea un nuevo chunk en `mepia_memory` (el anterior queda como historial).
N10 Context Builder siempre recupera el más reciente (`ORDER BY created_at DESC LIMIT 1`).

---

### `GET /business/{business_id}/onboarding/status`

Verifica si el onboarding está completo antes de disparar Layer 3.

**Response 200:**
```json
{
  "business_id": "uuid-v4",
  "onboarding_complete": true,
  "completed_at": "2024-01-15T10:00:00Z",
  "has_brand_identity": true,
  "has_audit_tolerances": true,
  "has_cost_structure": true,
  "settings": {
    "brand_identity": {},
    "audit_tolerances": {},
    "expected_cost_structure": [],
    "audit_rules": {}
  }
}
```

Cuando no existe configuración, `settings` es `null`. La interfaz puede usar ese estado
para crear defaults sin bloquear la ingesta. Si hay configuración, `settings` devuelve los
valores persistidos para precargar el formulario y evitar que una edición reemplace
accidentalmente ajustes anteriores por defaults. Repetir POST sobre ajustes
existentes devuelve 409 sin sustituirlos; PUT es una actualización explícita.

`settings.expected_cost_structure` es la forma del **formulario**:
`amount_per_month` corresponde a `expected_monthly_amount` del POST/PUT y
`tolerance_pct` es un porcentaje visible (`0.5` = 0.5%). El guardado divide
siempre entre 100 (`0.5 → 0.005`); API de escritura/DB usan decimal 0–1. Los
porcentajes de `audit_tolerances` siguen en decimal; no confundir ambos contratos.
Con costos vacíos, onboarding puede estar completo y `has_cost_structure` ser
false: no se inventa información para completar métricas.

---

## Bloqueo de Layer 3

**Regla de negocio crítica:** Si `onboarding_complete: false`, el endpoint
`POST /api/audit/layer3/run` debe retornar HTTP 412 (Precondition Failed).

```python
# En build_initial_state() — verificación previa al grafo
onboarding = await db.fetchone(
    "SELECT id FROM mepia_memory "
    "WHERE business_id = :bid AND metadata->>'node_origin' = 'onboarding' "
    "ORDER BY created_at DESC LIMIT 1",
    {"bid": business_id}
)
if not onboarding:
    raise HTTPException(
        status_code=412,
        detail={
            "error": "onboarding_required",
            "message": "El negocio no tiene configuración de auditoría. "
                       "Completar POST /business/{id}/onboarding antes de ejecutar Layer 3.",
            "setup_url": f"/business/{business_id}/onboarding"
        }
    )
```

---

## Persistencia

El onboarding escribe en tres tablas:

**1. `business_onboarding`:** upsert por negocio con identidad, tolerancias,
reglas y fechas. **2. `mepia_memory`:** inserción directa de un chunk con
`status="pending_embed"`. El siguiente bloque ilustra su contenido conceptual;
la ruta no llama a `MemoryService.store_memory()` ni genera embeddings al guardar:

```python
MemoryChunk(
    business_id=business_id,
    source_audit_run_id=None,      # nullable — onboarding no tiene run previo
    node_origin="onboarding",
    date=today.isoformat(),
    content=f"""
        IDENTIDAD DE MARCA:
        {payload.brand_identity.brand_voice}

        PROHIBIDO EN RECOMENDACIONES:
        {', '.join(payload.brand_identity.prohibited_recommendations)}

        FOCO PRINCIPAL: {payload.brand_identity.priority_focus}

        UMBRALES DE AUDITORÍA:
        - Discrepancia caja máxima: {payload.audit_tolerances.max_cash_discrepancy_pct*100}%
          o ${payload.audit_tolerances.max_cash_discrepancy_abs} MXN (el más permisivo)
        - Margen warning: {payload.audit_tolerances.margin_warning_threshold*100}%
        - Margen crítico: {payload.audit_tolerances.margin_critical_threshold*100}%
        - Spike de costo: {payload.audit_tolerances.cost_spike_threshold_pct*100}%

        ALERTAS ROJAS AUTOMÁTICAS:
        {', '.join(payload.audit_rules.red_alert_triggers)}
    """,
    archetype=None,                # identidad fija, independiente del arquetipo
    quality_approved=True
)
```

**3. `business_fixed_costs` — estructura de costos esperada:**
Cada `ExpectedCostStructure` se persiste como fila en `business_fixed_costs`
con `is_active: true`. Las filas anteriores se marcan `is_active: false`.

---

## Acceptance Criteria

- WHEN `POST /business/{id}/onboarding` con payload válido → chunk en `mepia_memory` con `node_origin: "onboarding"`, HTTP 201
- WHEN `POST /api/audit/layer3/run` sin onboarding previo → HTTP 412 con `error: "onboarding_required"`
- WHEN `PUT /business/{id}/onboarding` → nuevo chunk en `mepia_memory`, filas anteriores en `business_fixed_costs` marcadas `is_active: false`
- WHEN `max_cash_discrepancy_pct > 1` → HTTP 422
- WHEN `expected_cost_structure` vacío u omitido → se acepta y no se crean costos estimados
- WHEN sesión inválida → 401 antes de DB; negocio ajeno/inexistente/sin dueño → 403 antes de ajustes
- WHEN se abre Documentos sin ajustes → formulario de carga visible y POST automático de defaults
- WHEN ya hay ajustes → se conservan al volver a Documentos; POST repetido da 409 sin cambios
- WHEN se abre/guarda tolerancia 0%, 0.1%, 0.5%, 1%, 5% o 100% sin editar → se conserva el decimal persistido
- WHEN se inicia el análisis sin onboarding → la interfaz guarda los defaults y reintenta el análisis
- WHEN `margin_critical_threshold >= margin_warning_threshold` → HTTP 422

---

## Edge Cases

- Negocio nuevo sin transacciones: onboarding válido, Layer 3 puede ejecutarse pero `time_series.periodos` estará vacío
- `red_alert_triggers` vacío: permitido — el negocio no tiene reglas adicionales
- Onboarding actualizado durante un run activo de Layer 3: el run usa el chunk anterior (el que estaba al momento de `build_initial_state`)

---

## Archivos relacionados de este nodo
- `n10_context_builder.md` — consume el chunk de onboarding vía SQL directo
- `mem_memory_layer.md` — `MemoryService.store_memory()` + `MemoryChunk`
- `db_schema.md` — `mepia_memory`, `business_fixed_costs`
- `_glossary.md` — `OnboardingPayload` (actualizar con `OnboardingIdentityPayload`)
- `api_layer3.md` — bloqueo HTTP 412 si onboarding incompleto
