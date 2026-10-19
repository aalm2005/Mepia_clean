# Ejecutar MEPIA en otra computadora para el video

**Entorno verificado:** interfaz y servidor completo usan MEPIA principal con
claves modernas, ECC/ES256 y cuenta con negocio asignado. INC-046/047 resueltas;
login, Documentos y Chat IA confirmados por el usuario después del cambio.
OpenAI ya está configurado en esta computadora; Claude puede quedar vacío
porque existe respaldo OpenAI. INC-048/049 resueltas localmente. El ensayo real
de archivos/IA sigue pendiente: [pasos del usuario](demo_video_paso_a_paso.md).
Ver [evidencia y límites](database_unification.md).

Estado: 15-oct-2026. Esta guía describe la preparación necesaria; no certifica
que el análisis completo ya haya pasado un ensayo en la computadora del equipo.
La [integración de ajustes](onboarding_defaults_integration.md) está validada
localmente y confirmada por el usuario en sus pantallas.

## Qué debe recibir el compañero

1. La misma versión del código. Rama `codex/chatbot-q4`, HEAD de referencia
   `f9cfddc`; **N10 y la unificación actuales todavía no tienen commit/push**.
   Descargar solo ese HEAD no incluye estos cambios. Entregar una copia
   actualizada o publicar los cambios en una acción autorizada por separado.
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
ambos procesos al modificar la configuración. Las claves de OpenAI y Anthropic
se encontraban vacías en la revisión anterior. OpenAI ya se configuró; Claude
puede quedar vacío conservando la variable. Falta validar OpenAI/Gemini reales.

## Iniciar los procesos

**Terminal 1, servidor completo**, desde la raíz de MEPIA:

```powershell
.\.venv\Scripts\python.exe -B -m uvicorn api.main:app --host 127.0.0.1 --port 8016 --log-level warning --no-access-log
```

Este perfil incluye ingesta, análisis, ajustes y chat. El perfil
`api.chat_app:create_app --factory` sirve para acceso, ajustes y chat;
**no incluye la carga de documentos ni el análisis completo**. Iniciar solo uno
de los dos perfiles en el puerto 8016. En esta máquina quedó activo
`api.main:app` tras la unificación, junto con Next en 3016. No se ejecutó
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
4. **Cambiar la fecha del análisis para que coincida con los documentos.** La
   pantalla todavía inicia en `2024-01-15`; no asumir que la detecta sola.
5. Pulsar Analizar; corregir cualquier revisión humana que aparezca y continuar.
   Si una métrica necesita datos adicionales, puede quedar incompleta; subir
   solo facturas no garantiza indicadores de ventas, ni viceversa.
6. Comprobar que la corrida termina, que los resultados corresponden al negocio
   y fecha, y que se abre el Dashboard con su `run_id`. Guardar ese enlace para
   el ensayo; la recuperación automática del último análisis aún es limitada.
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
haya aprobado el ensayo; una pregunta sencilla en Chat IA. Cerrar explicando
lo pendiente: tutorial guiado, adaptación móvil completa y validaciones restantes
del Paso 5/producción. Si no se completa el ensayo, identificar claramente los
resultados previamente guardados y no presentarlos como una carga nueva exitosa.
