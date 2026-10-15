# Ejecución automatizada y revisión humana del Paso 5

**Acceso e inicio — 15-oct-2026, validado localmente; sin commit:** sesión por pestaña (recargar conserva; cerrar/abrir pide login), Dashboard como inicio y bienvenida eliminada. API con Bearer y verificación de servidor; cookies antiguas no autentican. [Contrato, pruebas y límites](mepia_access_navigation.md). INC-042 resuelta localmente: Edge 24/24, cero errores; build y tipos código 0. 42 incidencias: 39 resueltas, dos mitigadas y una pendiente externa. Los informes fechados anteriores no validan este cambio.

**Estado documental al 15-oct-2026:** consultar [flujo, avance y pendientes](estado_actual_mepia.md). La sesión identifica y carga el negocio autorizado automáticamente; el selector con un solo negocio aún puede simplificarse. Tutorial guiado pendiente y adaptación móvil parcial. Los registros y conteos fechados siguientes conservan su alcance histórico; la publicación de código no equivale a despliegue.

El ejecutor reúne la matriz técnica, las regresiones existentes y el recorrido
del navegador. Genera un informe por ejecución y una ficha para revisar claridad.
Separa las capas: datos/Auth simulados, proveedor real, interfaz y evaluación
humana. Un control automático aprobado no equivale a aprobar toda la experiencia.

El [plan de 48 casos](chatbot_step5_test_plan.md) y su JSON v1 conservan el diseño
original. La implementación y los resultados posteriores se registran aquí y
en la [bitácora](chatbot_corrections.md). No se trasladan a esta configuración
los juicios independientes del Paso 4 ni las pruebas de acceso real anteriores.

## Ejecución local sin consumo de Gemini

Desde la raíz del repositorio, con las dependencias de desarrollo instaladas:

```powershell
python -B -m tests.chat_step5_automation --mode simulated --cases all --output .test_tmp/paso5/ejecucion-01
```

Para incluir regresiones y navegador:

```powershell
$env:MEPIA_TEST_BROWSER = 'msedge'
# Si Playwright está en otro runtime, indicar MEPIA_PLAYWRIGHT_MODULE.
python -B -m tests.chat_step5_automation --mode simulated --cases all --with-regression --with-browser --output .test_tmp/paso5/ejecucion-02
```

`--node` permite indicar un ejecutable Node compatible. El navegador necesita
Playwright. `--browser-cache .test_tmp/paso5/cache-next` permite reutilizar solo
la caché privada de compilación. El ejecutor exige loopback, puertos libres
3015/8015 y caché dentro de `.test_tmp`; no usa el preview 3016/8016. La espera
de navegación de 90 segundos admite compilación fría; no es el objetivo de
latencia del producto. Al finalizar detiene únicamente sus procesos y retira
solo sus referencias de tipos en tsconfig y next-env, conservando el contenido previo y ediciones ajenas.

El backend usa el router, firma JWT local, herramientas, historial y adaptador
del producto con datos sintéticos en memoria. La ejecución simulada bloquea
conexiones externas y no lee claves del proveedor. La regresión ES256/JWKS usa
firmas criptográficas locales y descubrimiento simulado. El navegador bloquea
destinos externos y usa exclusivamente Auth/datos/proveedor sintéticos.

La matriz permite verificar automáticamente 41 capas del backend; C07/C08 se
completan en navegador. Las cinco verificaciones restantes de publicación,
rendimiento real y revisión humana mantienen sus prerrequisitos. Además pueden
quedar subcontroles específicos pendientes, por ejemplo fallo del upstream del
proxy, que el informe identifica; no se declara cobertura completa por una cifra
de capas aprobadas. P02 ejecuta 70 POST simulados en niveles de 5/10/20 usuarios
con valores distintos por actor para detectar cruces.

## Primera tanda con el proveedor real

```powershell
python -B -m tests.chat_step5_automation --mode gemini --cases first --max-model-calls 18 --output .test_tmp/paso5/gemini-01
```

La opción es explícita: ocho casos, hasta nueve POST y 18 intentos como máximo,
sin reintentos SDK ni juez. `--cases` también acepta IDs separados por comas;
valida selección, duplicados y techo antes de cargar credenciales. No reutiliza
el presupuesto del Paso 4. Cada intento queda anotado antes de invocar Gemini.

`api/.env` se lee solo en este modo para `CHAT_GEMINI_API_KEY` y `CHAT_MODEL`;
`--private-env` admite otro archivo privado. No se imprimen valores de claves.
El origen de Gemini lo fija el adaptador existente; no recibe endpoints del
usuario. Se usan auditorías y Auth sintéticos en memoria, incluso en este modo:
**es una validación de Gemini + contrato HTTP local, no de Supabase ni del
recorrido completo con una cuenta real**. Es una variante acotada del plan que
evita aprovisionar o cambiar negocios para medir el proveedor.

Ante el primer fallo se guarda el intento y se detienen los siguientes casos.
No repetir para obtener una respuesta favorable. El HTTP 200 con respaldo
seguro conserva los datos, pero no aprueba una generación que debía validarse.
El informe muestra el consumo real; un intento fallido también consume el techo.

La primera ejecución real del 14-oct consumió 17 intentos de 18: siete casos con
controles mecánicos aprobados y C02 detenido por `RateLimitError/http_429` al
componer su respuesta. Ocho respuestas anteriores validadas conservadas. No se
conoce la cuota exacta ni su restablecimiento; INC-20261014-041 pendiente externo.
El intento restante no alcanza para repetir composición y revisión. La próxima
repetición de C02 necesita verificar disponibilidad y registrar un presupuesto
acotado propio; no está programada automáticamente.

## Archivos que produce cada ejecución

- `report.json`: fuente de resultados, huellas de código/plan, modos, consumo,
  observaciones saneadas, fallos y capas pendientes.
- `report.md`: resumen legible por caso y alcance.
- `provider_attempts.jsonl`: solo en modo real; intentos iniciados y fecha UTC,
  sin solicitudes crudas, respuestas del SDK o secretos.
- `human_review.html` y `human_review.json`: ficha y plantilla ligadas al informe.
  Solo incluyen respuestas reales con todas sus partes validadas. La simulación
  deja la ficha vacía; un respaldo no se presenta como redacción validada.
- `regression.log`, `browser.log` y `browser/`: auxiliares privados cuando se
  piden esas capas. Los informes públicos incluyen resultados saneados, no logs
  completos ni datos de sesión.

Cada directorio de salida debe ser nuevo; el ejecutor rechaza sobrescribir un
run. Conserva los intentos fallidos. Código 0 significa que las capas solicitadas
y ejecutadas no fallaron; **no equivale a aprobación funcional ni publicación**.
Código 1 indica fallo de caso o suite; código 2, entrada/configuración inválida.
El JSON diferencia caso funcional pendiente y capa automática aprobada.

## Revisión humana de claridad

Abrir `human_review.html` de una ejecución real. Dos personas sin formación
financiera, R1 y R2, leen las mismas respuestas. Cada una puntúa de 0 a 2:
respuesta directa, palabras comunes, detalle/condiciones y tono respetuoso.
También indica si puede explicar la idea principal y su condición o límite.
No escribir nombres, contactos ni datos personales. Guardar descarga un JSON;
guardar no aprueba automáticamente.

Para validar una ficha completada, usando el informe exacto al que está ligada:

```powershell
python -B -m tests.chat_step5_automation --review ruta/revision-completada.json --report .test_tmp/paso5/gemini-01/report.json --output .test_tmp/paso5/revision-01
```

El importador exige las mismas respuestas/digests, dos lectores por respuesta,
cuatro calificaciones completas por lector, al menos 7/8 sin ceros y comprensión
confirmada. Rechaza respuestas omitidas o alteradas, una ficha en blanco y usar
una simulación como evidencia del modelo. Valida los juicios registrados; no
certifica la identidad del lector ni sustituye la revisión factual con fuentes.

La revisión de la primera tanda no cubre L02–L10 ni todos los públicos; ampliar
la muestra real sigue pendiente. P06 también exige terminar la revisión de uso
y presentación pertinente; una ficha clara no aprueba seguridad o despliegue.

## Controles previos a publicar

P01 necesita una muestra suficiente de latencias reales; no se generan peticiones
extra para completarla. P03 exige inventario y permisos de todas las rutas que
se expondrán. P04 exige build/tipos y auditoría del lock final, con INC-023 visible.
P05 depende de la topología de procesos/réplicas y el contrato de RAM temporal.
P06 requiere lectores reales. Permanecen separados del avance del ejecutor;
no hay despliegue, cambios de producción ni adopción de otro proveedor implícitos.

Verificación final (intento 6): 154 passed, 2 warnings, 41 subtests passed in 22.73s, código 0; 18/18 controles del navegador, cero errores. La comprobación posterior de include detectó un reordenamiento de Next; se extrajo una función compartida de limpieza, con tres pruebas Node aprobadas, y se comprobó sobre los archivos generados reales: recupera las dos huellas previas y preserva ediciones ajenas. No se repite todo el navegador tras extraer solamente esa función; la evidencia del flujo y la de limpieza se conservan por separado. Cero llamadas extra a Gemini. [Evidencia](evaluations/chatbot_step5_workspace_cleanup_20261014.json).
