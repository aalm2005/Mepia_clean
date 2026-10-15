# Auditoría de recuperación de fase 1 — 12-oct-2026

Una llamada suplementaria del juez Gemini 3.8, cero generaciones/reintentos:
3/3 juicios independientes favorables, cuatro criterios verdaderos por parte,
cero errores nuevos, fallos, pendientes o contradicciones. Fuente y tres digests
coincidentes; resumen semántico recalculado idéntico. Código de revisión 1 solo
por el criterio global de 36 partes frente a las tres de esta muestra.

La generación mantiene 45/45 controles y cobertura 2/2. Su auditoría previa
y replay de traza permanecen ligados por SHA; no se repite la generación ni
el replay. Diez huellas de código, 264 originales del plan y 274 de la auditoría
previa coincidentes; 286 archivos previos a esta auditoría preservados.

Consolidado `chatbot_step4_policy_refusal_phase1_judge_recovery_20261012_072935_21c041e7_combined`: cuatro generaciones contadas una sola vez, dos llamadas
históricas del juez y seis API de fase 1. Conserva el APITimeoutError original
por separado en attempts y los tres juicios favorables; el campo total_api_calls
del consolidado cuenta solo las dos llamadas del juez. Cero API al consolidar.

Recuperación de fase 1 aceptada para calidad bajo la autorización del usuario;
se puede habilitar fase 2 con máximo diez generaciones/tres juez (trece API),
sin reintentos y con detención ante fallos. Seis de 19 API adicionales usadas;
historial del seguimiento 30 (20 generación/10 juez). Dos éxitos anteriores y
un éxito con la guía nueva conservados por separado. El reemplazo de la tercera
generación fallida aún requiere fase 2 aprobada; no declarar tres repeticiones
exitosas con la guía nueva ni cerrar Paso 4. El timeout sigue siendo un fallo
histórico de disponibilidad, sin causa de servicio ni estabilidad demostradas.

INC-20260930-013 abierta; INC-20260930-016 mitigada para esta recuperación.
Rama codex/chatbot-q4, HEAD 6fa66bcc6a731a3f06df79edb5a4bf62e3c8e03c, sin commit. Cero API durante la auditoría;
suite y código de producto sin cambios.
