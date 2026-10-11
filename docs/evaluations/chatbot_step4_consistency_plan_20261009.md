# Prueba dirigida de consistencia — 9-oct-2026

Estado: **preparada; pendiente de ejecución**.

Tres ejecuciones nuevas, una por vez, de dos casos sintéticos:
`same_day_result_and_report` y `arithmetic_division`.
Por ejecución: 3 partes, 2 respondibles; máximo 4 generaciones Lite y
1 juez Flash independiente. Total máximo: **12 generación + 3 juez = 15 API**.
Sin reintentos; espera configurada 60 s. El diagnóstico anterior y la tanda
completa aprobada no se cuentan entre las tres nuevas.

Ejecuta este comando una vez y conserva su salida; repetir hasta tres veces
solo si la ejecución anterior no presenta fallos, pendientes o errores:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Documentos\PROYECTO INTEGRADOR 2\chatbot_paso4_continuacion\.test_tmp\medir_gemini.ps1" -DiagnosticoTanda4 -ModeloJuez gemini-3.5-flash
```

Exigir en las tres: cero fallos mecánicos, cobertura 2/2, juicios 3/3 favorables,
cero pendientes/errores/contradicciones. Detenerse ante un fallo y analizar su
traza antes de más llamadas. No sustituir un fallo por otra ejecución favorable.
El código `revision=1` aislado es esperable por el gate de 36 partes; consultar
los contadores y el JSON del juez para evaluar esta muestra dirigida.

La traza no es juicio independiente. Las tres nuevas respuestas deben tener
sus propios hashes/digests/revisiones; no se incorporan al consolidado global.
La configuración y los SHA previos están en el JSON del plan. Si cambian,
revisar la comparabilidad. Tres éxitos no demuestran la causa histórica ni
constituyen una garantía de consistencia futura.

El conjunto global aprobado conserva 28 casos/36 partes, 22/22 cobertura,
548/548 controles y 36/36 juicios favorables. La causa del rechazo anterior
sigue sin determinarse. Seguimiento adicional pendiente antes de Paso 5.

Preparación: sintaxis PowerShell y plan existentes correctos, cero API.
Solo documentación y plan; último resultado general: 230 aprobadas,
una integración opt-in omitida/119 subpruebas; suite no repetida.
Rama `codex/chatbot-q4`, HEAD `7c2d307123f90bacb94f6223e3ea89cd53e71088`, sin commit.
