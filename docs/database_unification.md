# Unificación de MEPIA en la base principal

**Registro del corte anterior:** la preparación posterior resolvió localmente
INC-048/049 y confirmó OpenAI configurado; Claude es opcional mediante el respaldo
OpenAI existente. Las pruebas/conteos que siguen describen su corte original.
Ver [pasos y evidencia actuales](demo_video_paso_a_paso.md).

Estado: 15-oct-2026. Rama `codex/chatbot-q4`, HEAD de referencia
`f9cfddc84721a9ea32f8e56ba804f0ed8dc77f09`; cambios **sin commit/push**.
**Conexión, esquema y acceso unificados y verificados.** INC-046/047 resueltas
en sus alcances; INC-048 permanece abierta y el análisis nuevo completo pendiente.
[Informe verificable](evaluations/database_unification_20261015.json).

## Resultado y alcance

La interfaz y `api.main:app` usan MEPIA principal con las claves modernas
existentes. La cuenta creada personalmente por el usuario quedó vinculada a
MEPIA Dev, verificando la identidad confirmada y sin reemplazar otro propietario.
Se conservó la otra cuenta. El usuario confirmó login, negocio y apertura de
Documentos/Chat IA, también después del retiro de credenciales antiguas.

Se reactivó principal, se aplicaron 009/010 y 011 y se retiraron las credenciales
heredadas con autorización expresa. Son cambios reales en la base principal;
no hubo publicación de una web. MEPIA - PRUEBAS se conserva y no se copiaron sus
fixtures. Ambos proyectos siguen existiendo: esta instalación usa solo principal.

## Datos y contrato físico

| Comprobación | Resultado observado |
|---|---|
| Esquema | 15 tablas/131 columnas antes; 18 tablas/175 columnas después |
| Contraste estático | 658 referencias literales; cero tablas/columnas faltantes |
| Datos preservados | 58 auditorías, 21 documentos, 19 objetos Storage, 8 POS, 35 transacciones, una configuración, 12 costos fijos y dos memorias |
| Huellas anteriores | Auditorías y negocio coinciden excluyendo las columnas nuevas/propietario autorizado |
| Identidades | Dos cuentas después de la creación solicitada; cuenta anterior conservada |
| Históricos | Estados completed/pending preservados; linaje N14 desconocido permanece NULL |

`supabase/operations/unify_primary.sql` reúne 009/010 en una transacción: linaje,
propiedad, índices y lectura autenticada por dueño, retirando lectura anónima.
011 agrega eventos de turno, inventario y comisiones, campos auxiliares e índices
necesarios para los upserts. Los datos históricos desconocidos quedan NULL.
La segunda aplicación de 011 terminó correctamente: operación idempotente.

Existe un grupo POS histórico con varias filas del mismo negocio/fecha. Se
conservó completo: `upsert_pos_daily` bloquea por negocio/fecha y crea o actualiza
solo una fila inequívoca. Si hay varias, rechaza sin sobrescribirlas. Ingesta API
devuelve 409 por ambigüedad y 503 por fallo de guardado, deteniendo la persistencia
posterior. La RPC usa SECURITY INVOKER y EXECUTE solo para service_role; se
revocan explícitamente los grants predeterminados a anon/authenticated.

No ejecutar `APPLY_ALL.sql`, semillas o conversiones históricas como actualización
automática de una base existente. Su comentario remite al procedimiento revisado.

## Verificaciones realizadas

| Verificación | Resultado |
|---|---|
| Regresión local | 178 aprobadas, 41 subpruebas aprobadas, dos advertencias FastAPI, 12.67 s, código 0 |
| SQL real de contratos | 9/9: inserción/actualización/rechazo ambiguo, cinco contratos de upsert, RLS y restricción EXECUTE |
| SQL real de identidad | 4/4: propietario lee su negocio/auditorías; otra identidad no ve ninguno |
| Limpieza | Escrituras de ensayo dentro de BEGIN/ROLLBACK; tres tablas nuevas vacías y conteos anteriores iguales |
| Procesos | Servidor completo 8016 e interfaz 3016 reiniciados; diez comprobaciones de conexión/rutas/acceso aprobadas |
| Sin sesión | 401 en API/proxy de negocios; REST anónimo no devuelve negocios/auditorías |
| Grounding real | Una evidencia S3 y cuatro métricas existentes; falta N14 enlazado, sin inferir relaciones |
| Usuario | Login, negocio, Documentos y Chat IA confirmados antes y después del retiro de claves |

Las pruebas usan Auth/proveedores simulados salvo las lecturas/contratos SQL y
las confirmaciones indicadas. No hubo llamadas del agente a modelos. El build,
tipos y E2E completos del cierre anterior N10 conservan su evidencia; no se
atribuyen como ejecuciones nuevas de esta unificación.

Primer SQL: 7/8; los grants predeterminados permitían EXECUTE anónimo. Se corrigió
y repitió 9/9, incorporando también authenticated. Regresión inicial bloqueada
sin salida en sandbox e interrumpida; repetición fuera aprobada. Dos intentos del
ejecutor de runtime tenían expectativas incorrectas sobre rutas/redirecciones;
se corrigieron según el código. Ninguno se presenta como validación aprobada.

## Retiro de credenciales antiguas — INC-047

Se sanea el snapshot completo antes de recortar la salida, evitando repetir el
error que mostró parte de un token heredado. No se registra el valor en estos
documentos. La aplicación se cambió a las claves modernas ya existentes y se
validó antes de desactivar las antiguas. La revisión automática rechazó una
delegación inicial; se recibió autorización expresa posterior y entonces se actuó.

Desactivar las API keys produjo 401 en apikey, pero una prueba HEAD sin contenido
demostró que el token antiguo aún funcionaba como JWT. Con autorización específica
se revocó únicamente la firma anterior HS256. UI: Revoked; firma actual ECC/P-256
conservada. Verificación final: anon/service_role antiguos como apikey 401, token
antiguo como Bearer con apikey moderna 401 y clave moderna de servidor operativa.
El usuario confirmó de nuevo sus pantallas. No se cambiaron contraseñas.

Las otras copias deben actualizar `.env.local` y `api/.env` con las claves modernas
del mismo proyecto, mantener ES256 y reiniciar ambos procesos. Clave secreta solo
en el servidor; credenciales fuera de Git y de chats. Configuración anterior
respaldada en privado; las credenciales revocadas ya no sirven para volver atrás.

## Archivos y siguientes acciones

Producto: `agents/api_ingest.py`, `api/main.py`; pruebas de persistencia/HTTP.
SQL: operación de unificación, migración 011 y aviso en consolidado histórico.
Documentación: bitácoras, diseño maestro, estado actual, README, guía del video,
contratos de esquema/S1B/autenticación/N15 y tareas. El informe JSON conserva las
huellas de fuentes; la configuración privada permanece ignorada.

1. Atender INC-048: propagar el fallo de persistencia N14; una respuesta en memoria
   no garantiza que el informe pueda recuperarse desde chat.
2. Configurar OpenAI/Anthropic y ensayar archivos nuevos, persistencia S3/N14 y
   consulta posterior. Gemini está configurado para chat; no sustituye esas claves.
3. Preparar la computadora de grabación con código y configuración actualizados;
   no se ha probado una instalación limpia allí. Ver [guía](mepia_setup_video.md).
4. Continuar la evaluación funcional/humana restante del Paso 5, tutorial y móvil.
   Los permisos de endpoints legados mantienen el montaje limitado a local.

Commit, push, despliegue web y cambios posteriores de producción son acciones
separadas. Las pruebas históricas conservan sus entornos y no se reescriben.

## Revisión documental y de privacidad al cierre

725 archivos candidatos y 68 documentos revisados por el ejecutor local;
365 enlaces comprobados, cero rotos tras normalizar 25 rutas absolutas Windows.
437 artefactos históricos del inventario inicial conservan SHA-256. Cero
coincidencias de claves/correos personales y de tokens antiguos o sus sufijos
en archivos publicables. Configuración privada ignorada por Git; diff --check
código 0. Specs nuevas: 412 y 425 palabras. Son controles acotados, no una
certificación universal. Estados actuales corregidos; informes fechados y planes
que exigen PRUEBAS conservados como evidencia de su alcance original.
