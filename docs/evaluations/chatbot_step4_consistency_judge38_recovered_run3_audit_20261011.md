# Auditoria del fallo de repeticion 3

## Tercera repeticion detenida — 11-oct-2026

`chatbot_step4_gemini_batch4_diagnostic_20261012_052919_6ff8abfb` hizo 4 gen/1 juez: cobertura 2/2, 44/45 controles, un fallo
`provider_generation` en `arithmetic_division`. El borrador negaba realizar
calculos y citaba `/status/explanation`; su texto y solicitud de revision
son identicos a los de las dos repeticiones anteriores aprobadas internamente.
Esta vez el revisor marco `supported=false` y `follows_policy=false`, con
`calculation_performed=false` e `in_domain=true`; veto de una negativa correcta.
El modelo no devolvio una razon que explique esos booleanos.

La guarda respeto el veto y publico una negativa segura de respaldo, sin
claims ni calculos. Se conserva como fallo de generacion; no se elimina ni
se reclasifica como aprobacion. Ticket e informe siguen cubiertos. El juez
externo 3.8 recibio 503/UNAVAILABLE con pista de capacidad: tres revisiones
pendientes, cero juicios favorables/adversos. Este codigo 1 incluye fallos
reales y no se atribuye exclusivamente al gate global de 36 partes.

Auditoria de fuente/plan/runner/registro/fixture/diez huellas correcta;
replay local de cuatro salidas reproduce casos, controles y digests, y el
resumen semantico se recalcula identico. Comparacion completa de solicitudes
de negativa entre las tres ejecuciones: mismo input/borrador, juicios internos
distintos. 256 originales protegidos intactos; cero API en auditoria.
Diagnostico local, no juicio independiente sobre estas tres respuestas nuevas.

Serie detenida con 2/3 aprobadas para calidad. Diez de diez API restantes
usadas: historial 24 (16 gen/8 juez), sin llamadas adicionales autorizadas.
INC-20260930-013 reabierta solo para este seguimiento por inestabilidad de
revision interna; INC-20260930-016 pendiente externo por nuevo 503. Conjunto
offline historico aceptado 36/36, 22/22 y 548/548 preservado; Paso 4 no cerrado.
21 incidencias: 19 resueltas, una abierta y una pendiente externa. No se
reinicia otra serie ni se modifica el criterio para ocultar este fallo.
Codigo y suite sin cambios al auditar; ultima general 230 aprobadas, una
integracion opt-in omitida y 119 subpruebas en 92.27 s. Rama `codex/chatbot-q4`, HEAD
`6fa66bcc6a731a3f06df79edb5a4bf62e3c8e03c`, sin commit. Sigue tratar el rechazo interno antes de nuevas pruebas.
