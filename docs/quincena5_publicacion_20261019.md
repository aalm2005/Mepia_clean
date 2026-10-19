# MEPIA — Publicación de la quincena 5

Fecha: 19 de octubre de 2026. Rama: `codex/quincena-5`.
Base: `f9cfddc84721a9ea32f8e56ba804f0ed8dc77f09` (`codex/chatbot-q4`).
Estado de este registro preparatorio: sin commit ni push todavía.

## Contenido

- Configuración inicial automática y ajustes avanzados opcionales, con sesión y
  propiedad verificadas, tolerancias corregidas y sin inventar gastos (INC-044/045).
- Contratos y documentación de la unificación con MEPIA principal; migración 011
  y operación de unificación como fuentes versionadas. Este push no aplica SQL
  ni cambia servicios externos (INC-046/047 conservadas).
- Guardado terminal N14 y seguimiento del análisis avanzado (INC-048/049).
- Dashboard con decimales textuales, fecha de documentos, selección de corrida
  dentro de la sesión/negocio y recuperación por linaje S3 explícito (INC-050–053).
- PDF/XML ficticios, scripts seguros de preparación y guía de demostración.
- INC-054: PDF binarios y paquete con bytes conservados; evita conversiones de
  checkout en Windows que alteraban SHA-256 y podían afectar deduplicación.
- Pruebas, bitácoras, especificaciones y reportes actualizados; evidencia histórica
  conservada. El código del chatbot mantiene consulta de solo lectura.

## Verificación del 19-oct

- 226 pruebas y 41 subpruebas aprobadas; dos advertencias de deprecación FastAPI;
  36.57 s, código 0. DB y proveedores simulados, sin modelos reales.
- Fechas: 11/11. Presentación: 16/16. TypeScript: código 0.
- Auditoría inicial: 745 archivos candidatos, 72 documentos, 418 enlaces locales
  sin faltantes; 443 evidencias históricas intactas; sin secretos, correos
  personales o archivos grandes detectados. Se vuelve a revisar el contenido
  preparado para commit antes de publicarlo.
- Integridad Git: inicialmente los filtros modificaban los dos PDF y el XML
  comprobados (3/3). Tras `.gitattributes` y volver a preparar el índice: cuatro
  fuentes intactas y 8/8 comparaciones de blobs/checkout aprobadas. Los dos PDF,
  XML y oráculo JSON se leyeron correctamente. Revisión del índice: código 0.
  Se conservan las ejecuciones previas fallidas; no se modificaron los artefactos.
- Edge 23/23 del 15-oct: evidencia anterior conservada; no repetida el 19-oct.
- La reanudación encontró incompleto un reporte privado temporal de auditoría;
  se conservó y regeneró. Los archivos públicos no tenían bytes nulos y todos
  sus JSON eran válidos. No se modifica el producto por esta interrupción.

## Alcance y pendientes

El ensayo real de los documentos del 14-oct y su respuesta nueva del chatbot no
se han confirmado. Siguen la evaluación funcional/humana restante del Paso 5,
tutorial guiado, adaptación móvil completa y controles de producción (incluida
la autorización de recursos legados de INC-023). No se declara producción lista.
Las 54 incidencias conservan 51 resueltas, dos mitigadas y una pendiente externa.
INC-054 se detectó y resolvió al validar la integridad del paquete para publicar;
los estados previos se conservan con su alcance histórico.

La carpeta privada `.test_tmp`, los archivos de claves y las dependencias locales
quedan excluidos. Para otra computadora se sigue la
[guía de instalación](mepia_setup_video.md) y se configura su entorno privado.
[Guía de ensayo](demo_video_paso_a_paso.md).

[Evidencia de publicación](evaluations/quincena5_publicacion_20261019.json).
