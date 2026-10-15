# MEPIA — Requirements

> Este archivo es el punto de entrada del spec para el panel de Kiro.
> La documentación detallada de requerimientos está distribuida en los archivos de nodo.
> Ver `_index.md` para el mapa completo del pipeline.

## Overview

MEPIA (Mise En Place Artificial Intelligence) es un copiloto financiero para dueños de restaurantes que automatiza la auditoría operativa y financiera mediante agentes de IA multi-capa.

## Requirements

### 1. Ingesta de documentos (S1)
- El sistema admite datos estructurados por API, POS PDF, facturas XML/PDF, recetas y conteos de caja
- La UI actual carga POS PDF y facturas XML/PDF; las conexiones POS externas requieren integración
- XML/API usan parseo estructurado; PDF usa extracción. Se persisten documentos y datos según el tipo
- `daily_context` está retirado del pipeline; los endpoints antiguos devuelven 410
- Ver spec detallado: `s1_ingesta.md`, `n01_pos_pdf_input.md`, `n02_facturas_input.md`, `n03_human_input_endpoints.md`

### 2. Validación de integridad (S2)
- El sistema debe validar que el set de datos por métrica esté completo antes de calcular
- Cada métrica tiene estado `dormant` (faltan datos) o `active` (set completo)
- Ver spec detallado: `s2_gatekeeper.md`

### 3. Motor de cálculo (S3)
- El sistema debe ejecutar cálculos financieros en Python puro sobre métricas `active`
- El output son números crudos sin interpretación (CalcResult[])
- Ver spec detallado: `s3_motor_calculo.md`

### 4. Auditoría forense IA (S4)
- El sistema debe generar un diagnóstico forense (fugas, discrepancias, techos) usando LLM
- El output es un ForensicReport sin recomendaciones directas
- Ver spec detallado: `s4_auditoria_ia.md`

### 5. CEO Orchestrator (N05)
- El sistema debe sintetizar el ForensicReport con memoria RAG y arquetipo CEO
- El output son AuditInsight[] con copilot_phrase personalizada por arquetipo
- Ver spec detallado: `n05_ceo_orchestrator.md`

### 6. Capa paralela y loop (N06–N14)
- El sistema debe ejecutar auditoría de gastos en paralelo (N09)
- El sistema debe construir contexto enriquecido, generar reporte y revisar calidad en loop
- Ver specs: `n06_orchestrator_adk.md`, `n09_gastos.md`, `n10_context_builder.md`, `n11_consultor.md`

### 7. Memoria transversal
- El sistema debe mantener memoria RAG persistente entre sesiones de auditoría
- Ver spec detallado: `mem_memory_layer.md`

### 8. Autenticación y Autorización
- Todos los endpoints del backend deben validar el JWT de sesión de Supabase Auth
- La autorización verifica que el `user_id` extraído del token tiene acceso al `business_id` solicitado
- El backend usa `SUPABASE_SERVICE_ROLE_KEY` (bypass RLS) — la autorización es responsabilidad del código Python
- Ver spec detallado: `_auth_strategy.md`

### 9. Onboarding de Identidad del Negocio
- Antes de ejecutar Layer 3, el negocio debe completar el onboarding de identidad
- El onboarding inyecta el "Lente del CEO" en `mepia_memory` y registra umbrales de auditoría
- Si el onboarding no está completo, `POST /api/audit/layer3/run` retorna HTTP 412
- Ver spec detallado: `n10_onboarding_identidad.md`

### 10. Ingesta de POS con múltiples días
- El endpoint `POST /ingest/pos` debe fragmentar PDFs multi-día y retornar un array de resultados
- Umbral de confianza OCR: 90% para totales y métodos de pago, 80% para líneas individuales
- Ver spec detallado: `n01_pos_pdf_input.md`

## Archivos de spec relacionados

- `_index.md` — mapa completo del pipeline y estado de cada nodo
- `_glossary.md` — contratos de datos y términos de dominio
- `db_schema.md` — schema de base de datos híbrido
- `_auth_strategy.md` — estrategia transversal de autenticación y autorización
- `n10_onboarding_identidad.md` — prerequisito de Layer 3: onboarding de identidad del negocio

### Experiencia y alcance vigentes — 15-oct-2026
- Login común e identificación automática del negocio propio implementados.
- Selector con una sola opción aún visible; simplificación pendiente.
- Chat IA integrado, de consulta y lenguaje cotidiano; validación del Paso 5 en curso.
- Tutorial didáctico pendiente, distinto de la configuración inicial existente.
- Adaptación móvil parcial; revisión integral de pantallas/dispositivos pendiente.
- Ver [flujo y estado actual](../../../docs/estado_actual_mepia.md).
