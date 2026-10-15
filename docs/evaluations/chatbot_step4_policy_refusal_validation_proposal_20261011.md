# Propuesta de medicion de la aclaracion de negativas — 11-oct-2026

Estado: propuesta no autorizada. El presupuesto anterior se agoto (24 API
historicas en el seguimiento). No se inicia ninguna llamada ni se permite
reutilizar ejecutores ligados al codigo anterior.

## Cambio preparado y comprobado localmente

`agents/chat_response.py` aclara al revisor que una negativa
calculation/not_allowed respaldada por una fuente policy en
/status/explanation tiene respaldo en la restriccion del chat y no requiere
evidencia de negocio. Debe vetar calculos, ofertas de hacerlos, hechos
inventados o contradicciones. El veto y la clasificacion de respaldo como
fallo siguen intactos. Solo cambia esa guia de revision; no cambian escritor,
datos, esquema o politica base. Alcance comprobado en 28 fixtures/54 callbacks:
seis casos afectados, cero API. 48 pruebas y 23 subpruebas aprobadas en 3.89 s.
Estos resultados no demuestran todavia mejora con Gemini real.

## Dos fases propuestas (maximo 18 llamadas adicionales)

1. Repetir solo same_day_result_and_report y arithmetic_division con traza:
   maximo cuatro generaciones y un juez (5 API), exigir 45/45 controles,
   cobertura 2/2 y 3/3 juicios independientes favorables. Auditar antes de fase 2.
2. Evaluar las otras cinco preguntas cuyo prompt de revision cambio:
   explicit_calculation, implicit_calculation, mixed, question_injection y
   result_and_projection. Nueve partes/tres respondibles, maximo diez
   generaciones y tres llamadas del juez (13 API), cuatro partes por llamada
   sin dividir preguntas. Todos los controles y juicios deben aprobarse.

Modelos: generador gemini-3.5-flash-lite y juez gemini-3.8-flash; timeout 60 s,
cero reintentos automaticos, detener ante cualquier fallo o revision pendiente.
No regenerar los 28 casos ni reiniciar otra serie de tres. Historial maximo
42 API si se consumen las 18 propuestas; todo error permanece registrado.

## Criterio de sustitucion propuesto

Si ambas fases pasan, la nueva generacion de la fase 1 sustituye a la tercera
fallida para el seguimiento de calidad. Se conservan las dos generaciones
anteriores aprobadas y se declara que usaron la guia de revision anterior;
la redaccion del escritor y sus datos no cambiaron. No afirmar tres exitos
con la guia nueva, disponibilidad sin errores, ni transferir juicios a otro
informe. La tercera fallida queda archivada con su fallo y sus tres revisiones
historicas pendientes; los nuevos informes requieren sus propios juicios.
El conjunto historico de 28 casos conserva su evidencia original. La version
nueva se mide en los seis casos afectados y el control adicional de informe.
Este ajuste de continuidad y presupuesto requiere aceptacion explicita.

SHA nuevo de chat_response.py: `39efe9fff20a11d03bbcd98b29da9984072550216e98ab3f46b29f9fce7d514b`.
Rama codex/chatbot-q4, HEAD 6fa66bc, sin commit. Paso 4 sigue sin cierre.
