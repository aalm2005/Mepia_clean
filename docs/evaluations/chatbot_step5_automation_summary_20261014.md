# Resultado de la automatización del Paso 5 — 14-oct-2026

**Ejecutor implementado y validado localmente. Validación completa del modelo y
comprensión humana pendientes.**

| Capa | Resultado real de esta ejecución | Alcance |
|---|---|---|
| Matriz local final | 43 capas por caso aprobadas, cero fallidas, cinco pendientes; código 0 | Auth/datos/proveedor sintéticos; conserva subcontroles pendientes explícitos |
| Regresión | 154 pruebas, 41 subpruebas, dos advertencias; 26.49 s, código 0 | Ocho módulos, incluyendo errores/budgets/evidencia y ES256 local |
| Navegador | 18 controles, cero errores de página, código 0 | Edge sin interfaz visible, Auth/modelo sintéticos, destinos externos bloqueados |
| Carga | 70 POST simulados, valores distintos por actor | 5/10/20 usuarios; latencias exactas en el JSON |
| Gemini | Siete de ocho casos con controles mecánicos aprobados; C02 detenido, código 1 | Nueve POST locales, 17 de 18 intentos; Auth/DB en memoria |
| Claridad humana | Ocho respuestas reales validadas disponibles; cero fichas completadas | Dos lectores requeridos; no hay aprobación humana ni juez independiente |

C02 recibió HTTP 200 con respaldo seguro y diagnóstico saneado
`RateLimitError/http_429` al componer. No aprueba generación validada. Se detuvo
sin reintentos ni consumo adicional; queda un intento del techo inicial y no
alcanza para composición más revisión. INC-041 pendiente externo; disponibilidad
o cuota exacta no demostradas. Conservar respuestas anteriores, sin trasladarles
aprobaciones de lectura ni atribuir estabilidad general al proveedor.

La matriz encontró y corrigió dos formas conceptuales: «qué son» y la aclaración
«Explícame el método» con un selector previo inequívoco en la misma pregunta.
INC-040 resuelta en código y procesos de prueba, con regresiones de no cálculo.
El preview del usuario no se reinició. INC-035 actualizada/resuelta en este
ejecutor: espera para compilación fría, caché privada y limpieza de tipos propios.
41 incidencias: 38 resueltas, dos mitigadas (023/031), una pendiente externa (041),
cero abiertas. Los cinco intentos locales y el real detenido quedan conservados.

- [Ficha para dos lectores](chatbot_step5_human_review_20261014.html).
- [Plantilla de revisión ligada al informe](chatbot_step5_human_review_20261014.json).
- [Resultado real de Gemini](chatbot_step5_automation_gemini_attempt1_20261014.json).
- [Ejecución local final](chatbot_step5_automation_attempt5_20261014.json).
- [Consolidado y huellas](chatbot_step5_automation_summary_20261014.json).
- [Uso y límites del ejecutor](../chatbot_step5_automation.md).

Quedan la repetición acotada de C02 tras verificar disponibilidad, ampliar la
matriz real y revisión factual, dos lectores para claridad, subcontroles del
upstream del proxy y prerrequisitos P01/P03/P04/P05/P06. No se declara todo el
Paso 5 validado con Gemini ni listo para publicación. Supabase, datos/cuentas,
producción, commit y push intactos. Pasos 1–4 y acceso previo siguen cerrados
en su alcance. Rama codex/chatbot-q4, HEAD 6fa66bcc6a731a3f06df79edb5a4bf62e3c8e03c.
