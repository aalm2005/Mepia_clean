# Ejecutar MEPIA en otra computadora para el video

**Nuevo corte local — 26-oct-2026:** hay [pruebas por secciones](plan_pruebas_mepia.md)
y [demostración sin API real](pruebas_mepia_20261026.md), con regresión 452/136,
demo API 15/15 y Edge general 26/26, historial 11/11, ajustes 14/14 y demo 5/5.
Son ejecuciones nuevas con datos/Auth/SDK simulados, distintas de las evidencias
fechadas inferiores. Los 30 casos manuales y la evaluación humana/proveedor/DB
real permanecen pendientes; no reabren pasos aceptados ni acreditan producción.

**Consulta sin nueva ejecución:** entrar a Dashboard recupera selección de la
pestaña o último análisis terminado; el historial permite elegir anteriores.
Dashboard/Salud/Reportes conservan la selección al visitar/recargar el chat.
Son lecturas protegidas, sin consumo de modelos. Una tendencia requiere dos
fechas con el mismo indicador/unidad; varias corridas de un día no bastan.
[Guía vigente y pendientes](actualizacion_documental_20261019.md).

**Registro de entorno del 15-oct-2026:** interfaz y servidor completo usan MEPIA principal con
claves modernas, ECC/ES256 y cuenta con negocio asignado. INC-046/047 resueltas;
login, Documentos y Chat IA confirmados por el usuario después del cambio.
OpenAI ya está configurado en esta computadora; Claude puede quedar vacío
porque existe respaldo OpenAI. INC-048/049 resueltas localmente. El ensayo real
de archivos/IA sigue pendiente: [pasos del usuario](demo_video_paso_a_paso.md).
Ver [evidencia y límites](database_unification.md).

Guía actualizada: 19-oct-2026; los registros de entorno del 15-oct son históricos. Esta guía describe la preparación necesaria; no certifica
que el análisis completo ya haya pasado un ensayo en la computadora del equipo.
La [integración de ajustes](onboarding_defaults_integration.md) está validada
localmente y confirmada por el usuario en sus pantallas.

## Qué debe recibir el compañero

1. La misma versión del código. Base publicada: `codex/quincena-5`,
   `5ae4c868be6843513a3b8a4f0be2962762c6442d`; ya incluye N10 y la unificación.
   Historial, tendencias y esta sincronización son avances locales sin commit.
   Clonar solo esa base no los incluye. Entregar una copia actualizada, sin
   secretos ni datos privados; una publicación exige una acción separada.
2. Node.js/npm y Python con el lanzador `py` disponibles en su terminal.
   Instalar las dependencias de este repositorio; no reutilizar `node_modules`,
   `.next` ni el entorno `.venv` de otra máquina.
3. Acceso al destino acordado **MEPIA principal**, con tablas, funciones y
   permisos y conexión verificados. La cuenta debe existir allí y tener un negocio
   asignado por `owner_id`. Usar otra cuenta exige asignarle su negocio.
4. Configuración privada local de Supabase y claves API con acceso/cuota para
   OpenAI y Gemini. Anthropic es primario opcional de N11; sin clave usa OpenAI. Gemini responde al chat; por sí sola no reemplaza
   las llamadas del motor a los otros proveedores. Una suscripción de una app
   de chat no configura estas claves dentro de MEPIA.
5. Internet y fecha/hora automáticas de Windows sincronizadas.

No enviar contraseñas/claves por el chat ni agregarlas a Git. La carpeta del
equipo revisada no tenía `.env.local`: faltaba la configuración pública de
login en sus archivos. Eso es una causa probable del fallo informado, pero no
demuestra la causa exacta sin su mensaje ni conocer su entorno externo.

## Primera instalación en Windows

Abrir **PowerShell** y colocarse en la carpeta donde están `package.json` y
`api`. Ejemplo; ajustar la ubicación a su computadora:

```powershell
Set-Location -LiteralPath 'C:\MEPIA'
node --version
py --version
npm ci
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r api/requirements.txt
```

`npm ci` respeta `package-lock.json`. Los requisitos Python usan rangos, no un
archivo de versiones totalmente fijadas: resolver un error de instalación antes
de continuar. No se ha probado una instalación limpia en su computadora.
Las pruebas locales de esta integración usaron Node.js 24.19.0 y Python 3.12.14;
son las versiones observadas, no una garantía sobre otras combinaciones.
No hace falta activar `.venv` si se usa la ruta del ejecutable como aquí.

Crear, **solo si no existen**, `.env.local` a partir de `.env.example` y
`api/.env` a partir de `api/.env.example`; conservar cualquier configuración
privada existente. Guardar los valores reales fuera del repositorio público:

| Archivo | Variables y propósito |
|---|---|
| `.env.local` | `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`: URL y clave pública moderna `sb_publishable_…` del proyecto principal; `AGENTS_API_URL=http://127.0.0.1:8016` |
| `api/.env` | `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`: conexión del servidor al mismo proyecto con clave moderna `sb_secret_…` |
| `api/.env` | `SUPABASE_JWT_ALGORITHM` según el proyecto destino validado; no copiar el algoritmo de otra base sin comprobarlo. MEPIA principal usa ES256; el ejemplo trae HS256 y debe ajustarse. `SUPABASE_JWT_SECRET` solo se necesita con HS256 |
| `api/.env` | `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`: análisis; `CHAT_GEMINI_API_KEY` y `CHAT_MODEL`: chat; `ENVIRONMENT=dev` |

Las API keys heredadas fueron desactivadas y su firma anterior revocada.
No copiar claves antiguas de otra carpeta: actualizar ambos archivos privados
con las modernas del mismo proyecto. La clave secreta del servidor y las de
modelos van únicamente en `api/.env`. Reiniciar
ambos procesos al modificar la configuración. La preparación del 15-oct registró OpenAI configurado y respaldo de N11
comprobado por simulación. No se inspeccionaron claves en esta revisión.
Configurar/verificar privadamente acceso y cuota en la computadora destino;
falta validar el recorrido real completo.

## Iniciar los procesos

**Terminal 1, servidor completo**, desde la raíz de MEPIA:

```powershell
.\.venv\Scripts\python.exe -B -m uvicorn api.main:app --host 127.0.0.1 --port 8016 --log-level warning --no-access-log
```

Este perfil incluye ingesta, análisis, ajustes y chat. El perfil
`api.chat_app:create_app --factory` sirve para acceso, ajustes, chat y
consulta de análisis guardados;
**no incluye la carga de documentos ni el análisis completo**. Iniciar solo uno
de los dos perfiles en el puerto 8016. En el registro del 15-oct quedó activo
`api.main:app` tras la unificación, junto con Next en 3016; su estado actual
no se comprueba en esta revisión documental. No se ejecutó
un análisis nuevo de IA para comprobar su arranque.

**Terminal 2, interfaz**, también desde la raíz:

```powershell
npm run dev -- --hostname 127.0.0.1 --port 3016
```

Dejar ambas terminales abiertas. Abrir [MEPIA](http://localhost:3016/) en Edge o
Chrome y entrar por el login general. `localhost` apunta a la computadora que
lo abre; ese enlace no conecta a los procesos de otro integrante.
Supabase está en la nube: si usan el mismo proyecto/negocio, comparten datos;
las cargas nuevas no quedan aisladas solo por ejecutarse en otra computadora.

**Memoria semántica, cuando se necesite:** el comando siguiente procesa una
tanda pendiente, usa OpenAI y actualiza la memoria compartida del proyecto.
No es un tercer servidor permanente ni un requisito del login/carga básica:

```powershell
.\.venv\Scripts\python.exe -m utils.embedding_worker
```

El guardado inicial deja su memoria en `pending_embed`. Ejecutar este proceso
solo como parte de un ensayo autorizado sobre el destino acordado si se quiere
preparar búsqueda semántica; la unificación no lo ejecutó. La ingesta y el motor corren en el
backend, sin levantar un proceso adicional de base de datos local.

## Cómo llegan los resultados al chat

El servidor completo guarda métricas S3 y el informe N14 disponible en
`audit_results`. Chat IA lee esos registros del mismo proyecto y negocio;
puede consultarlos después, aunque el motor ya esté detenido. Un resultado en
otro proyecto no se sincroniza solo. Las definiciones del catálogo pueden
responderse aunque falte un análisis del negocio.

No basta con ver un resultado en pantalla: comprobar que quedó guardado,
que la fecha es la correcta y que el chat cita esa evidencia. No presentar una
pregunta conceptual como prueba de consulta de resultados nuevos.

## Ensayo obligatorio antes de grabar archivos nuevos

1. Verificar que el servidor completo inició sin errores y que
   [su documentación](http://127.0.0.1:8016/docs) incluye `/ingest/pos`,
   `/ingest/factura` y `/orchestrator/run`. Que `/docs` abra no valida las claves.
2. Entrar, confirmar el nombre del negocio y abrir Documentos. La configuración
   inicial se aplica automáticamente; no hace falta inventar gastos ni llenar
   el formulario avanzado.
3. Elegir un POS PDF con texto extraíble y una factura CFDI XML o PDF compatible.
   Una imagen escaneada no garantiza extracción: el lector actual usa texto y
   reglas, sin un OCR general. Preparar datos de prueba representativos.
4. **Comprobar la fecha del análisis.** Inicia vacía y se infiere desde el lote
   de ventas; si no hay una fecha inequívoca, se pide elegirla. Una selección
   contradictoria detiene el análisis (INC-051 ya corregida).
5. Pulsar Analizar; corregir cualquier revisión humana que aparezca y continuar.
   Si una métrica necesita datos adicionales, puede quedar incompleta; subir
   solo facturas no garantiza indicadores de ventas, ni viceversa.
6. Comprobar que la corrida termina, que los resultados corresponden al negocio
   y fecha, y que se abre el Dashboard con su `run_id`. Guardar ese enlace para
   el ensayo. Sin selección se recupera el último análisis terminado del negocio;
   el historial permite elegir anteriores sin ejecutar modelos. Ver la validación
   local y sus límites en `analysis_history_dashboard_20261019.md`.
7. Abrir Chat IA y preguntar por un resultado realmente disponible de esa
   fecha, además de una pregunta conceptual. Verificar respuesta y fuentes.

El motor usa modelos indicados en el código, entre ellos `gpt-4o`,
`text-embedding-3-small` y, en consultoría avanzada, un primario Anthropic con
respaldo OpenAI. Tener una clave no demuestra acceso ni disponibilidad de esos
modelos: comprobarlo en el ensayo real, sin presentar un respaldo o error como
análisis validado. No se hicieron llamadas nuevas a modelos al preparar esta guía.

Si el ensayo falla, conservar el mensaje exacto y la etapa; no mostrar archivos
privados ni claves al compartir evidencia. Aún falta validar este recorrido
integral en la computadora de quien grabará. Los permisos pendientes del backend
legado mantienen este montaje limitado a desarrollo local/pruebas, sin publicarlo
en Internet. No ejecutar migraciones ni semillas a ciegas sobre el proyecto
compartido existente.

## Propuesta de recorrido de 3–5 minutos

Mostrar problema que resuelve MEPIA, login y negocio automático; Documentos con
ajustes iniciales y personalización opcional; carga/resultado del análisis que
haya aprobado el ensayo y una pregunta sencilla en Chat IA. En Q6, abre
**Tutorial** en la barra superior para mostrar la guía. La aceptación manual,
la adaptación móvil integral y las validaciones del Paso 5 y de producción
siguen pendientes. Si no se completa el ensayo, identificar claramente los
resultados previamente guardados y no presentarlos como una carga nueva exitosa.
