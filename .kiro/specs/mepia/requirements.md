# MEPIA — Requisitos y alcance vigente

Punto de entrada de Kiro; detalle por nodo en [_index.md](_index.md).
Estado al 19-oct-2026, avances locales sin commit sobre `5ae4c86`.

## Motor y datos

1. Ingesta: API estructurada, POS PDF, factura XML/PDF, recetas y conteos según
   sus contratos. La UI actual ofrece POS PDF y factura XML/PDF. Conectores
   externos requieren integración; daily_context está retirado del pipeline.
2. S2 verifica requisitos de cada métrica; faltantes quedan dormant. S3 calcula
   en Python y conserva cifra, unidad y estado; no delega cálculos a la IA.
3. S4 produce diagnóstico forense; N05 sintetiza hallazgos por arquetipo y guarda
   el resultado completo. N06/N09 profundizan si corresponde; N07/N08 omitidos v1.
4. N10/N11/N13/N14 construyen contexto, consultan, revisan y guardan el informe.
   N12 omitido v1. Un fallo de persistencia no acredita informe completado.
5. Memoria semántica persistente, conversación temporal e historial de auditorías
   son contratos separados. N15 consulta S3/N14 guardados por negocio/fecha/linaje.
6. Documentos crea configuración inicial si falta, sin inventar costos. El
   formulario avanzado es opcional; valores y tolerancias conservados al guardar.
7. POS de varias fechas conserva su fragmentación. Fecha del análisis vacía se
   infiere solo de ventas inequívocas; contradicciones requieren corrección.

## Acceso y resultados

8. Toda API debe validar sesión y autorización de negocio. Implementado para
   chat, ajustes y nuevas consultas históricas; permisos por recurso de endpoints
   legados pendientes antes de producción. Una guarda visual no sustituye servidor.
9. Historial propio con fecha, guardado, estado y referencia distinguible; elegir
   recupera resultados sin ejecutar motor, IA ni escrituras.
10. Prioridad de selección: run_id explícito, referencia de pestaña por
    usuario/negocio, último terminado guardado. Error explícito sin fallback para
    enlaces inválidos/ajenos. Dashboard, Salud, Reportes y chat conservan selección;
    cambio de negocio/logout elimina inmediatamente datos previos.
11. Tendencias con fechas ordenadas, una corrida terminada por día y únicamente
    indicadores de mismo significado/unidad. Cero válido se conserva; faltantes
    son huecos. Sin sumar repetidos, inventar ingresos/márgenes ni interpolar.
12. Estados separados de carga, vacío, falta de datos, error y evaluación sin
    anomalías. El último exige evidencia forense original suficiente. Español
    sencillo, sin prometer carga Excel/CSV inexistente.
13. PDF y paquete de demo preservan bytes en Windows; INC-054 conserva su cierre.

## Evidencia y pendientes

[Historial y criterios](analysis_history.md), [diseño](design.md),
[plan](tasks.md), [estado y pruebas](../../../docs/estado_actual_mepia.md).
Implementación local no certifica ensayo real, revisión humana, móvil completo,
tutorial ni preparación de producción. No se reabren correcciones terminadas.


[Versión anterior conservada](../../../docs/history/documentation_before_sync_20261019/.kiro/specs/mepia/requirements.md). Sus estados y cifras describen su fecha original.
