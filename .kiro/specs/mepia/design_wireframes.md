# Diseño Frontend — Wireframes lógicos vigentes

Actualizado al 19-oct-2026. Los esquemas representan contenido y jerarquía,
no dimensiones exactas. [Componentes](design_components.md).

## Marco y vistas de resultados

```text
MEPIA | Dashboard | Documentos | Chat IA | Salud | Reportes | Configuración
Negocio autorizado                                      Cerrar sesión

Título de la vista / fecha del análisis / riesgo si está acreditado
Historial de análisis
[número · fecha analizada · guardado · estado · referencia breve] [cargar más]
Estado: buscando / cargando / completado / parcial / error
Informe avanzado: preparando / guardado / fallo (solo si corresponde)

Dashboard y Salud:
  Indicadores de la corrida: nombre real, cifra y unidad o faltante explicado
  Métricas calculadas: barras separadas por unidad
  Evolución de indicadores diarios: fechas ordenadas, una corrida por fecha
    o explicación de falta de fechas comparables

Hallazgos y acciones disponibles del análisis
Anomalías evaluadas / ausencia de evidencia / evaluación sin anomalías
Indicadores sin información suficiente y datos que faltan
```

Reportes comparte historial y hallazgos sin el bloque de métricas; no es una
promesa de presentar todo N14. La ausencia de resultados no produce cifras
ficticias ni el mensaje «Sin anomalías detectadas». Se conserva cero válido.
Las tendencias muestran huecos donde faltan datos, sin conectar ni sumar
corridas repetidas. Una fecha sola explica el requisito de dos fechas válidas.
No hay títulos fijos de ingresos o margen si esos datos no existen.

## Documentos

```text
Documentos de auditoría
Fecha: [vacía para inferir de ventas / selección compatible]
Enfoque: [Operative Genius | Product Purist | Growth Hacker]
[POS PDF] [Factura XML/PDF]
Estado de cada carga / revisión humana si corresponde
[Analizar archivos con Agentes IA]  ocupado durante la operación
[Personalizar configuración avanzada] opcional
```

Los valores iniciales se crean solo si faltan; costos sin inventar. No se
anuncian Excel/CSV ni un recorrido general de imágenes escaneadas.

## Acceso y chat

Sin sesión: MepiaLogin. Después: Dashboard como inicio, sin bienvenida separada.
Chat usa el mismo marco: nueva conversación/fecha, mensajes y fuentes, compositor
inferior. No pide otro login. Visitarlo y recargar conserva la referencia del
análisis al volver; las fuentes del chat siguen el contrato S3/N14.
Cambiar negocio o salir limpia inmediatamente la vista anterior.

Menú móvil y composiciones adaptables existentes; revisión integral de
dispositivos, tablas y formularios pendiente. El botón **Tutorial** está en la
barra superior. En móvil se muestra el ícono de ayuda con nombre accesible
«Ver tutorial».
[Onboarding](design_wireframes_onboarding.md), [flujos](design_flows.md),
[evidencia local](../../../docs/analysis_history_dashboard_20261019.md).


[Versión anterior conservada](../../../docs/history/documentation_before_sync_20261019/.kiro/specs/mepia/design_wireframes.md). Sus estados y cifras describen su fecha original.
