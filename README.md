# MEPIA

Motor de evaluacion y chatbot de consulta fundamentada en resultados de MEPIA.

## Version de desarrollo actual

La rama `codex/chatbot-q4` contiene el grounding, las herramientas deterministas,
el nodo conversacional, los adaptadores Gemini/OpenAI y la evaluacion offline
del chatbot. El conjunto aceptado del Paso 4 cubre 28 casos, 36 partes y 22
partes respondibles: 548/548 controles y 36/36 revisiones independientes
favorables. Los informes anteriores, incluidos los fallidos, se conservan.

Las tres repeticiones adicionales de consistencia siguen pendientes. El Paso 5
(autenticacion, autorizacion por negocio, endpoint, historial e interfaz del
chatbot) no esta implementado. Esta publicacion no despliega produccion.

El estado detallado esta en [la bitacora](docs/chatbot_corrections.md),
[las incidencias](docs/chatbot_incidents.md) y
[el procedimiento de evaluacion](docs/chatbot_step4_eval.md).

## Pruebas locales

Desde la raiz del repositorio, en PowerShell, con Python 3.12 disponible:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r api/requirements-dev.txt
$env:RUN_SUPABASE_INTEGRATION='0'
$env:PYTHONDONTWRITEBYTECODE='1'
.\.venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider
```

La integracion Supabase requiere habilitacion explicita y se omite en esta
ejecucion. Las pruebas locales usan proveedores simulados; las evaluaciones
reales se ejecutan por separado.

## Evaluacion con Gemini

El ejecutor `scripts/medir_gemini.ps1` utiliza la carpeta del repositorio donde
esta guardado. Por defecto busca `.venv\Scripts\python.exe`; acepta
`-PythonPath` para utilizar otro entorno con las dependencias instaladas.

Comprobar el plan sin pedir clave ni realizar llamadas:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/medir_gemini.ps1 -DiagnosticoTanda4 -MostrarPlan
```

Ejecutar una repeticion de los dos casos del seguimiento:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/medir_gemini.ps1 -DiagnosticoTanda4 -ModeloJuez gemini-3.5-flash
```

Cada repeticion permite como maximo cuatro llamadas de generacion y una del
juez, sin reintentos. Pide la clave oculta y la usa temporalmente en ese proceso;
los informes solo contienen datos sinteticos. Seguir los criterios y la regla de
detencion del [plan de consistencia](docs/evaluations/chatbot_step4_consistency_plan_20261009.md).
El codigo de revision de una muestra aislada debe interpretarse con sus
conteos: el criterio global exige 36 partes.

El ejecutor local historico de `.test_tmp` permanece en la computadora y su
SHA en el plan original se conserva. `scripts/medir_gemini.ps1` es una copia
adaptada para ejecutar desde otras ubicaciones; no cambia el generador, el
juez, los fixtures ni los presupuestos. Archivos temporales, entornos virtuales
y claves no forman parte de la publicacion.
