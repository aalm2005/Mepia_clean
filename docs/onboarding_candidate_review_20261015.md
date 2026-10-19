# Revisión de la candidata de configuración inicial — 15-oct-2026

**Actualización posterior a esta revisión:** INC-044/045 fueron corregidas e
integradas localmente el 15-oct-2026, sin commit/push. Ver
[integración y pruebas nuevas](onboarding_defaults_integration.md).
Este informe conserva el resultado original de la candidata antes de corregirla;
su JSON de revisión permanece intacto.

**Resultado: la propuesta permite empezar con ajustes iniciales, pero no se
aprueba su integración hasta corregir dos fallos comprobados.**

Revisión de la carpeta entregada por el usuario, sin `.git`, comparada con
`codex/chatbot-q4`, HEAD `f9cfddc84721a9ea32f8e56ba804f0ed8dc77f09`.
Se ejecutó una copia aislada; código de producto y carpeta original conservados.
Este informe y los registros asociados están sin commit/push.

## Hallazgos

1. **P1 — Se pueden consultar ajustes de otro negocio (INC-20261015-045).**
   Una cuenta sintética A consulta por el proxy Next los ajustes de un negocio B
   perteneciente a otra cuenta y recibe HTTP 200 con gastos y preferencias.
   Ubicación en la candidata: `api/main.py:472`, respuesta `settings`;
   `app/api/onboarding/route.ts` y middleware de identidad no comprueban propiedad.
   El control legado de autorización por recurso ya estaba pendiente; el nuevo
   detalle aumenta la información expuesta. El acceso anónimo por Next sí devuelve
   401 en el recorrido final. Exigir autorización del negocio en servidor y
   propagar la sesión necesaria antes de leer o modificar su configuración.

2. **P2 — Guardar sin editar altera porcentajes pequeños (INC-20261015-044).**
   Un gasto con tolerancia almacenada `0.005` se muestra como `0.5%`; guardar sin
   tocarlo almacena `0.5`, equivalente a `50%`. El GET nuevo convierte a porcentaje,
   pero `components/onboarding/OnboardingForm.tsx:87` solo divide entre 100 cuando
   el número supera 1. Unificar unidades y comprobar ida/vuelta de 0%, 0.1%, 0.5%,
   1%, 5% y 100%, incluyendo guardar sin modificar y editar el valor.

## Lo que sí funcionó

- Documentos muestra directamente ambos campos de carga y guarda la configuración
  automática cuando falta; el servidor acepta la lista de gastos vacía.
- No se inventan importes de renta, sueldos u otros gastos.
- Una configuración existente no se reemplaza por los ajustes iniciales; volver
  al formulario recupera las preferencias guardadas.
- El servidor rechaza límites de alerta contradictorios y el proxy bloquea al
  visitante sin sesión.

## Evidencia y límites

**13 controles completos: 11 aprobados y dos defectos; código 1 por los hallazgos.**
Edge sin errores de página. TypeScript sobre la carpeta original, sin emisión ni
caché incremental: código 0. Frontend/proxy y handlers N10 reales de la candidata,
con Auth y base de datos simulados. Cero llamadas reales a Supabase/IA; no se
ejecutó ingesta PDF/XML real ni el análisis financiero completo.

Se conservan dos intentos incompletos por supuestos del ejecutor sobre navegación
y caché; un tercero omitió middleware en la copia y produjo un falso positivo de
acceso anónimo. Se corrigió el ejecutor, se cotejó byte a byte el control original
y el cuarto recorrido confirmó exclusivamente los dos hallazgos anteriores.
705 archivos originales cotejados sin cambios; doce fuentes relevantes de la copia
y veinte huellas de código del producto actual comprobadas.

La candidata actualiza siete documentos de diseño/spec, pero falta registrar el
avance en continuidad/diseño maestro y sincronizar contratos/pruebas al corregirla.
45 incidencias: 40 resueltas, dos mitigadas, una pendiente externa y dos abiertas
en esta candidata; no se reabren las fases del chatbot ya aceptadas.

[Informe verificable](evaluations/onboarding_candidate_review_20261015.json).
