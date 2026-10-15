# Saludos del chatbot — 15-oct-2026

Corrección del Paso 5 solicitada por el usuario, independiente de la mejora
pospuesta de configuración inicial. Rama `codex/chatbot-q4`, base
`6d7cabc1c1cdb8889649900bec496e5156a2368a`; sin commit ni push.

## Comportamiento

«Hola», «Hola MEPIA», «Buenos días», «Buenas tardes/noches» y las variantes
acotadas en el código reciben una bienvenida breve que invita a consultar.
Antes, «Hola» producía `outside/outside_domain`: fue un error de clasificación,
no una excepción demostrada del servicio. Se registra en INC-20261015-043.

La nueva parte `kind=greeting`, `status=ok` contiene exclusivamente el saludo
fijo. Mantiene `generation_status=fallback`, con datos, evidencia, afirmaciones,
faltantes y diagnósticos vacíos. Es una interacción social, no una respuesta
factual ni generación validada. No se envía al clasificador/redactor/revisor;
un saludo aislado no consume llamadas de generación. La API conserva la
autenticación, propiedad, consulta de evidencia e historial existentes.

En una consulta mixta se procesan las partes restantes normalmente. «Hola y
calcula 10+10» saluda y rechaza el cálculo; «Hola, calcula 10+10» conserva el
rechazo. Un saludo no autoriza preguntas ajenas al dominio ni nuevas cifras.
Las consultas factuales mantienen redacción libre, fuentes y guardas vigentes.

La interfaz omite el aviso amarillo de explicación no validada y el apartado
de fuentes únicamente para el saludo. El historial visible conserva el turno;
el contexto del redactor omite los turnos exclusivamente sociales para que una
continuación como «¿Qué significa eso?» conserve la referencia anterior.

## Fecha y fuentes

La fecha opcional filtra resultados existentes de ese día. Vacía, selecciona
la ejecución S3 utilizable más reciente por fecha y creación. No ejecuta un
análisis nuevo ni es necesaria para definir un concepto del catálogo.

«Fuentes y trazabilidad» permite revisar el análisis o definición que respalda
una respuesta; conserva fecha y linaje exactos. El título y el selector de
fecha permanecen sin cambios. Simplificar esos textos es una propuesta, no un
cambio implementado en esta corrección.

## Verificación

- Reproducción previa: «Hola» devuelve `outside/outside_domain`, código 0.
- Regresión: **112 passed, 2 warnings, 41 subtests passed in 9.07s**, código 0.
- Edge: **25/25**, cero errores de página, código 0; servicios locales simulados.
- Helper de restauración del workspace: **3/3**, código 0.
- TypeScript sin emisión ni caché incremental: **código 0**.
- Servidor local del chat 8016 reiniciado, **OpenAPI HTTP 200**. No se prueba una
  nueva pregunta autenticada con la cuenta del usuario. El reinicio descarta el
  historial temporal del proceso anterior; recargar el cliente inicia uno nuevo.

INC-043 resuelta localmente; 43 incidencias: 40 resueltas, dos mitigadas y una
pendiente externa (041), cero abiertas. Las cifras anteriores permanecen como
históricos de su ejecución. No se repite el build de producción ni la evaluación
real Gemini. [Informe verificable](evaluations/chatbot_greetings_20261015.json).

Datos/Auth/proveedor simulados; cero llamadas nuevas a Gemini, cambios de SQL,
cuentas o producción. La evaluación real pendiente por INC-041 no se repite.
