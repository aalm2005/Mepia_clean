# Auditoría del suplemento de fase 2 — 12-oct-2026

Una llamada del juez 3.8, cero generaciones y cero reintentos; otro HTTP 503,
UNAVAILABLE y pista sanitizada de capacidad en el primer lote. Cero juicios y
nueve pendientes; otros dos lotes no llamados. La pista no confirma la causa.
Fuente, plan, intento y ejecutores ligados por SHA; resumen recalculado idéntico,
diez huellas, 264 originales y 322 protegidos de la auditoría anterior, más cinco archivos intactos.
334 evidencias previas a esta auditoría conservadas byte por byte.

Consolidado `chatbot_step4_policy_refusal_phase2_judge_recovery_retry3_20261012_094039_328ff3d4_combined`: diez generaciones contadas una vez, cuatro llamadas
históricas del juez, cuatro 503 preservados en attempts, cero favorables/adversos
y nueve pendientes. El campo total_api_calls del consolidado cuenta solo juez.
Generación original mantiene 116/116 y cobertura 3/3; fase 1 recuperada y su
timeout conservados. Cero API al auditar y consolidar, suite no repetida.

20/22 API adicionales usadas (14 gen/6 juez), dos llamadas sin usar; historial
44 API (30 gen/14 juez). El siguiente intento necesita tres lotes de 2/3/4,
cero generaciones: preparar un nuevo plan con máximo 23 bajo la autorización
vigente del usuario para continuar intentos; no volver a pedir autorización
para este alcance. Conservar todos los fallos y criterios. Reemplazo sin contar,
Paso 4 abierto; INC-20260930-013 abierta e INC-20260930-016 pendiente externo.
Rama codex/chatbot-q4, HEAD 6fa66bcc6a731a3f06df79edb5a4bf62e3c8e03c, sin commit; ningún despliegue ni cambio de producto.

Fe de erratas ligada a INC-20260930-014: el plan histórico retry3 guardó
14 generación/4 juez/19 API antes del intento, una suma incoherente. Los
informes e intentos ligados demuestran 14 generación/5 juez/19 API previas
y 14 generación/6 juez/20 API posteriores. Los límites ejecutables usaban
el total real y permanecieron correctos; se conserva el plan histórico y
se corrige explícitamente el desglose en esta auditoría y el próximo plan.
