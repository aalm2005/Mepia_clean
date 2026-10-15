# Propuesta para continuar el seguimiento — 11-oct-2026

Estado: propuesta no autorizada. Plan original y sus 0/3 ejecuciones sin
errores permanecen intactos. No se habilita ningun ejecutor ni llamada API.

## Ajuste propuesto

Aceptar como primera repeticion de calidad la generacion `58b2769d`, cuyos
45/45 controles, cobertura 2/2 y tres respuestas ahora tienen 3/3 juicios
independientes favorables ligados al mismo informe. Conservar el 503 inicial
como error de disponibilidad del juez. Esta excepcion corresponde solo al
error observado en la revision independiente de la primera repeticion.
No declarar tres ejecuciones sin errores de servicio ni demostrar estabilidad
del proveedor. Los criterios de respaldo, pregunta atendida, alcance,
no calculo, aislamiento, metadatos y cobertura no cambian.

## Trabajo restante

Completar solo las posiciones 2 y 3, mismos dos casos/modelos/traza, maximo
4 generaciones y una llamada del juez en cada una: **10 API como maximo**,
usando el presupuesto restante ya autorizado. Cero presupuesto nuevo pedido
por esta propuesta y cero reintentos automaticos; detener ante cualquier nuevo
fallo, revision pendiente o juicio adverso y auditar antes de continuar.
Exigir 45/45 controles, cobertura 2/2 y 3/3 juicios favorables por repeticion.
No trasladar juicios entre informes ni contar el reintento del juez como otra
generacion. Tras tres generaciones distintas aprobadas, documentar cierre del
seguimiento de calidad y conservar por separado el historial de disponibilidad.

Historial actual 14 API. Maximo acumulado tras las dos restantes: 24,
incluida la llamada suplementaria fuera del plan original ya utilizada.
No se regenera el conjunto aceptado de 28 casos/36 partes ni se reinicia otra
serie de tres. El codigo y el plan original quedan intactos.

Auditoria de recuperacion: `chatbot_step4_consistency_judge38_run1_retry1_audit_20261011.json` y Markdown.
Informe de origen SHA-256 `3fee617c3430197b01292e06aef4adb26c45c758566ad8780bdc413927f1ff06`.
La continuidad requiere aceptar explicitamente este cambio del criterio;
sin esa aceptacion permanecen bloqueadas las posiciones 2/3 y sus diez API.
