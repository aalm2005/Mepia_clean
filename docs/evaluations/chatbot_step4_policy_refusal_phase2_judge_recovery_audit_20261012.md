# Auditoría del suplemento de fase 2 — 12-oct-2026

Una llamada del juez 3.8, cero generaciones y cero reintentos; otro HTTP 503,
UNAVAILABLE y pista sanitizada de capacidad en el primer lote. Cero juicios y
nueve pendientes; otros dos lotes no llamados. La pista no confirma la causa.
Fuente, plan, intento y ejecutores ligados por SHA; resumen recalculado idéntico,
diez huellas, 264 originales y 298 protegidos de la auditoría anterior intactos.
310 evidencias previas a esta auditoría conservadas byte por byte.

Consolidado `chatbot_step4_policy_refusal_phase2_judge_recovery_20261012_083847_c6d73947_combined`: diez generaciones contadas una vez, dos llamadas
históricas del juez, dos 503 preservados en attempts, cero favorables/adversos
y nueve pendientes. El campo total_api_calls del consolidado cuenta solo juez.
Generación original mantiene 116/116 y cobertura 3/3; fase 1 recuperada y su
timeout conservados. Cero API al auditar y consolidar, suite no repetida.

18/20 API adicionales usadas (14 gen/4 juez), dos llamadas sin usar; historial
42 API (30 gen/12 juez). El siguiente intento necesita tres lotes de 2/3/4,
cero generaciones: preparar un nuevo plan con máximo 21 bajo la autorización
vigente del usuario para continuar intentos; no volver a pedir autorización
para este alcance. Conservar todos los fallos y criterios. Reemplazo sin contar,
Paso 4 abierto; INC-20260930-013 abierta e INC-20260930-016 pendiente externo.
Rama codex/chatbot-q4, HEAD 6fa66bcc6a731a3f06df79edb5a4bf62e3c8e03c, sin commit; ningún despliegue ni cambio de producto.
