# Integración del frontend del equipo con Chat IA

**Acceso e inicio — 15-oct-2026, validado localmente; sin commit:** sesión por pestaña (recargar conserva; cerrar/abrir pide login), Dashboard como inicio y bienvenida eliminada. API con Bearer y verificación de servidor; cookies antiguas no autentican. [Contrato, pruebas y límites](mepia_access_navigation.md). INC-042 resuelta localmente: Edge 24/24, cero errores; build y tipos código 0. 42 incidencias: 39 resueltas, dos mitigadas y una pendiente externa. Los informes fechados anteriores no validan este cambio.

**Estado documental al 15-oct-2026:** consultar [flujo, avance y pendientes](estado_actual_mepia.md). La sesión identifica y carga el negocio autorizado automáticamente; el selector con un solo negocio aún puede simplificarse. Tutorial guiado pendiente y adaptación móvil parcial. Los registros y conteos fechados siguientes conservan su alcance histórico; la publicación de código no equivale a despliegue.

**Automatización del 14-oct-2026 (histórica, anterior al acceso por pestaña):** ejecutor por capas implementado.
Final local: 43 capas por caso aprobadas, cinco pendientes, cero fallidas,
código 0; no equivale a 43 casos funcionales completos. Regresión 154 pruebas
y 41 subpruebas, dos advertencias, 22.73 s, código 0. Edge sintético: 18
controles, cero errores, código 0; carga 70 POST simulados. Gemini real con
datos/Auth en memoria: siete de ocho casos con controles mecánicos aprobados,
C02 detenido por HTTP 429; 17/18 intentos, código 1, sin reintentos ni juez.
Ocho respuestas validadas para revisión humana, aún sin calificaciones.
INC-040 resuelta localmente, 035 actualizada/resuelta, 041 pendiente externo.
41 incidencias: 38 resueltas, dos mitigadas, una pendiente externa, cero
abiertas. Supabase/cuentas/producción y preview del usuario sin cambios;
sin commit/push. Los avisos siguientes conservan sus registros históricos;
el diseño v1 y su plantilla permanecen intactos, anteriores al ejecutor.
Sigue disponibilidad/C02, revisión humana y ampliar solo lo pendiente.
Ver [ejecutor, resultados y revisión](chatbot_step5_automation.md).

**Diseño original — 14-oct-2026 (histórico, previo al ejecutor):** preparados cinco conjuntos y
48 casos: datos/fuentes (12), lenguaje/límites (10), conversación/historial
(10), seguridad/fallos (10) y preparación para publicación (6). Todos pendientes
de ejecución; no se trasladan aprobaciones anteriores. Primera tanda propuesta:
D01/D03/D05/D06/L01/L07/C01/C02, nueve POST reales como máximo y hasta 18 intentos
Gemini. Plan completo: 36 POST, hasta 72 intentos, cero juez y cero reintentos
SDK; presupuesto habilitado cero. Rúbrica con dos lectores objetivo, oráculos
sintéticos, aislamiento/limpieza y plantilla vacía. Riesgo estático L02
(«qué son») pendiente de comprobar; no es una regresión demostrada. Sin cambios
de producto, modelo, SQL, usuarios, producción, commit o push. Acceso y evaluación
previos siguen cerrados en su alcance. Ejecución funcional amplia pendiente;
OpenAI y publicación separados. Ver [plan detallado](chatbot_step5_test_plan.md).

**Ajuste de lenguaje — 14-oct-2026 (registro anterior a la automatización):** el usuario pidió respuestas
comprensibles sin conocimientos financieros y para diversos niveles de lectura.
Se ajustó la guía común de composición: palabras cotidianas, frases cortas,
tono respetuoso, respuesta directa y breve por defecto; detalles técnicos según
la pregunta. Una definición sencilla omite fórmulas, insumos y alias no pedidos,
conservando condiciones esenciales. Redacción libre, fuentes, cifras/unidades,
alertas y prohibición de calcular intactas. Backend local reiniciado, código 0.
115 pruebas y 41 subpruebas aprobadas, dos advertencias, 11.09 s, código 0;
proveedores simulados. El usuario repitió ticket promedio en una conversación
nueva y confirmó «Sí, ahora es clara»; Next registra POST 200. Es confirmación
humana de legibilidad en esa consulta, no un juicio semántico independiente ni
una medida universal de comprensión. INC-039 resuelta en este alcance;
INC-035 actualizada por atasco del ejecutor en sandbox y ejecución posterior
aprobada fuera de él. 39 incidencias: 37 resueltas, dos mitigadas (023/031),
cero abiertas. Un archivo de producto modificado: `agents/chat_response.py`.
Sin preguntas del agente al modelo, SQL, datos/usuarios, producción, commit
ni push. Evidencias anteriores conservadas; general/build/E2E no repetidos.
Evidencia `docs/evaluations/chatbot_step5_plain_language_20261014.json`.

**Conexión Gemini — 14-oct-2026 (registro anterior al ajuste de lenguaje):** clave Gemini guardada de forma
privada y backend local reiniciado; `api/.env` ignorado por Git. El usuario
envió «¿Qué es el ticket promedio?» y confirmó respuesta; Next registra POST
200 después del 503 previo a configurar. El texto compartido explica el
concepto y fórmula metodológica, cita diez rutas del catálogo y no incluye
el aviso de explicación no validada. Por el contrato de publicación, esa
redacción y sus claims corresponden a generación validada; inferencia desde
la evidencia visible del usuario, sin inspeccionar su sesión ni el JSON real.
Conexión de Gemini `gemini-3.5-flash-lite` confirmada para esta consulta
conceptual; no sustituye la evaluación offline ni valida todos los recorridos
reales. Fecha 2099 comprobada por lectura en MEPIA - PRUEBAS: procede del
fixture histórico `chat_grounding_correction2_test`, conservado; no se corrigió
ni eliminó. Cero preguntas del agente al modelo; una pregunta real del usuario,
con el límite existente de dos intentos por petición, sin reintentos del SDK.
38 incidencias: 36 resueltas, dos mitigadas (023/031), cero abiertas;
INC-035/038 actualizadas y resueltas en su alcance. Sin cambio de código de
producto, SQL administrativo, usuarios/propiedad, producción, commit ni push.
Pruebas anteriores conservadas; no se repitieron suites/build.
Evidencia `docs/evaluations/chatbot_step5_gemini_activation_confirmation_20261014.json`.

La versión combinada quedó implementada y validada localmente el 14-oct-2026.
El diseño azul, bienvenida y gráficas recibidos conviven con el acceso único,
la sesión/negocio comunes y Chat IA de esta rama. No es un merge de ramas Git:
la entrega era una carpeta, y se combinaron archivos/rutas seleccionados.

| Área | Resultado combinado |
|---|---|
| Inicio y apariencia | Fondo animado, bienvenida y superficies azules recibidas |
| Navegación | MepiaShell único con Inicio, Dashboard, Documentos, Chat IA, Salud, Reportes y Configuración |
| Acceso | Login previo a MEPIA, cookies verificadas, negocios propios y logout existentes |
| Dashboard/Salud/Reportes | KPI/gráficas/tablas del equipo, unidades separadas y valores S3 conservados |
| Cambio de contexto | Cancela peticiones, limpia análisis y rechaza resultados de otro negocio/corrida |
| Formularios | Diseño recibido junto al negocio autorizado de esta aplicación |
| Backend y datos | API/grounding/cálculo/historial/SQL preservados; hook frontend adaptado por defecto demostrado |
| Dependencias | Next 15.5.27 conservado; Recharts 3.10.1 integrado con 39 entradas desde el lock/paquetes recibidos |

Respaldo privado previo verificado de 281 archivos (40 modificados y 241 nuevos),
sin archivos de configuración ignorados. Directorio recibido intacto, 391
evidencias históricas cotejadas por SHA. Cambios locales sin commit/push.

Validaciones ejecutadas: presentación 12/12; E2E final 15/15, cero errores de
página, código 0; build Next y tipos finales código 0. Los intentos 1–4 fallidos,
el intento 5 aprobado y la revisión visual posterior se conservan por separado.
El intento 6 añade la visibilidad real de bienvenida y es el recorrido final.
Las métricas/cuentas/servicios de esas pruebas son sintéticos, con destinos
externos bloqueados. No certifican respuestas reales ni el pipeline de auditoría.

Incidencias INC-20261014-034/035/036/037 resueltas en su alcance: presentación,
ejecutor local, estado del análisis y animación de bienvenida. INC-023/031
siguen mitigadas; una nueva auditoría del lock y permisos en endpoints legados
siguen pendientes antes de producción. El control visual de propiedad no
sustituye autorización en el servidor. npm install/ci no se ejecutó; integración
de paquetes y rangos comprobada con el lock recibido y compilación real.

Abrir [MEPIA local](http://localhost:3016/), usar el acceso único y abrir Chat IA
desde el menú. El perfil real local conserva el proyecto MEPIA - PRUEBAS; no
se modificaron usuarios, propiedad, SQL ni producción en esta unión. La cuenta
propia fue confirmada por el usuario en el flujo anterior el 13-oct. El 14-oct
confirmó el nuevo diseño, acceso único/menú y negocio visible después de
sincronizar Windows; Next listado 200. El POST 503 anterior al guardado queda conservado;
clave Gemini cargada, backend reiniciado y respuesta conceptual confirmada con POST 200.

La clave Gemini quedó configurada de forma privada y la consulta conceptual
con fuentes fue confirmada por el usuario, POST 200. Ampliar el recorrido real
de métricas/historial y la configuración de OpenAI siguen como trabajos separados. Evidencia completa en
[reporte de integración](evaluations/chatbot_step5_frontend_merge_20261014.json)
y [bitácora](chatbot_corrections.md).
