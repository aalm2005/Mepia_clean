# N15 — Saludos acotados

**Publicación verificada — 15-oct-2026:** acceso por pestaña, Dashboard como
inicio y saludos del chat publicados en `codex/chatbot-q4`, commit
`49a5d05184a6e3f50c4353cafd84092df1e9b285`. Push normal código 0 y hash remoto
coincidente. INC-042/043 resueltas localmente y publicadas; INC-041 sigue pendiente
externa. [Evidencia de publicación](../../../docs/evaluations/github_access_greetings_verified_20261015.json).
Este registro se guarda en un commit documental posterior. Las menciones previas
«sin commit/push» describen su validación original. Producción sin cambios.


Extensión de experiencia del Paso 5, 15-oct-2026; INC-20261015-043.
Rama `codex/chatbot-q4`, base `6d7cabc`, sin commit/push.

## Contrato

`ChatAnswerPart.kind` admite `greeting`. Es una bienvenida fija de interfaz,
con `status=ok`, `generation_status=fallback` y sin datos, evidencia, claims,
faltantes, incidencias de generación ni diagnósticos. No admite texto libre ni
afirmaciones del negocio. No cambia los esquemas del redactor/revisor ni la
política factual de [N15](n15_chat_consulta.md).

## Aceptación

- WHEN el fragmento completo normalizado coincide con un saludo admitido THEN
  publica la bienvenida sin clasificar/redactar/revisar con IA.
- WHEN el saludo acompaña una consulta THEN responde las partes factuales con
  sus fuentes y conserva las negativas de cálculo o dominio correspondientes.
- WHEN se solicita un cálculo en el mismo fragmento THEN prevalece el rechazo.
- WHEN el negocio del paquete no coincide THEN rechaza antes del saludo.
- WHEN la API recibe un saludo THEN sigue exigiendo sesión y propiedad; conserva
  los accesos de evidencia y el historial protegidos existentes.
- WHEN la interfaz presenta un saludo THEN omite aviso amarillo y fuentes;
  las consultas factuales conservan ambos controles cuando correspondan.
- WHEN hay un turno exclusivamente social THEN se conserva en el historial
  visible, pero se excluye del contexto del redactor para preservar referencias.

La fecha sigue siendo opcional: filtra resultados existentes; vacía elige la
S3 utilizable más reciente. El catálogo conceptual no necesita un análisis.
Fuentes conserva el linaje/fecha del resultado o las rutas del catálogo.

Implementación y límites: [registro de saludos](../../../docs/chatbot_greetings.md).
Verificación local: 112 pruebas/41 subpruebas, dos advertencias, código 0;
Edge 25/25 y cero errores; helper 3/3 y tipos código 0. INC-043 resuelta
localmente; no se atribuyen pruebas con cuentas ni Gemini reales.
