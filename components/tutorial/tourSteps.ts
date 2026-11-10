// Pasos del tutorial guiado de MEPIA.
// Para cambiar textos u orden, edita solo este arreglo.
// `ruta`: página donde se muestra el paso.
// `elemento`: selector del elemento a resaltar (sin él, el globo sale centrado).
// `seccionConfig`: en Configuración, a qué sección (1-4) mover el formulario antes de mostrar el paso.

export type PasoTutorial = {
  ruta: string;
  elemento?: string;
  titulo: string;
  texto: string;
  seccionConfig?: 1 | 2 | 3 | 4;
  sinResultado?: string;
};

export const PASOS_TUTORIAL: PasoTutorial[] = [
  // ── Bienvenida ──────────────────────────────────────────────────────────
  {
    ruta: "/dashboard",
    titulo: "Bienvenido a MEPIA",
    texto: "Te vamos a mostrar en pocos pasos cómo usar MEPIA: subes los documentos de tu restaurante, el sistema los analiza y tú revisas los resultados.",
  },
  {
    ruta: "/dashboard",
    elemento: '[data-tour="nav"]',
    titulo: "Menú principal",
    texto: "Desde aquí te mueves entre las secciones. Vamos a recorrerlas en el orden en que normalmente se usan.",
  },
  {
    ruta: "/dashboard",
    elemento: '[data-tour="negocio"]',
    titulo: "Tu negocio",
    texto: "Aquí aparece el negocio con el que estás trabajando. Todo lo que subas y analices queda ligado a él.",
  },

  // ── 1. Documentos ───────────────────────────────────────────────────────
  {
    ruta: "/upload",
    elemento: '[data-tour="nav-upload"]',
    titulo: "Paso 1: Documentos",
    texto: "Todo empieza aquí. Subes la información del día para que MEPIA la analice.",
  },
  {
    ruta: "/upload",
    elemento: '[data-tour="advanced-config-link"]',
    titulo: "Configuración opcional",
    texto: "MEPIA ya trae valores recomendados, así que puedes empezar sin configurar nada. Si quieres ajustar costos, umbrales o reglas, entra aquí.",
  },
  {
    ruta: "/upload",
    elemento: '[data-tour="enfoque"]',
    titulo: "Enfoque del análisis",
    texto: "Elige en qué quieres que se enfoque el análisis. Esto cambia el tono y las prioridades de las recomendaciones.",
  },
  {
    ruta: "/upload",
    elemento: '[data-tour="fecha"]',
    titulo: "Fecha a auditar",
    texto: "Indica qué día quieres revisar. Si la dejas vacía y las ventas tienen una fecha clara, MEPIA la toma de ahí; si no, te pedirá elegirla.",
  },
  {
    ruta: "/upload",
    elemento: '[data-tour="archivos"]',
    titulo: "Sube tus archivos",
    texto: "A la izquierda, el ticket del punto de venta (PDF). A la derecha, las facturas de proveedor (PDF o XML). Puedes arrastrarlos o hacer clic.",
  },
  {
    ruta: "/upload",
    elemento: '[data-tour="analizar"]',
    titulo: "Inicia el análisis",
    texto: "Cuando tengas los archivos, presiona aquí. MEPIA extrae los datos, calcula los indicadores y usa IA para interpretarlos.",
  },

  // ── 2. Dashboard ────────────────────────────────────────────────────────
  {
    ruta: "/dashboard",
    elemento: '[data-tour="historial"]',
    titulo: "Elige un análisis guardado",
    texto: "El historial distingue fecha, hora de guardado y referencia. Puedes elegir otra corrida sin ejecutar IA. Si hay varias del mismo día, se muestran por separado.",
  },
  {
    ruta: "/dashboard",
    elemento: '[data-tour="estado"]',
    titulo: "Paso 2: Dashboard",
    texto: "Aquí ves si el análisis se está cargando, si terminó o si falló. Si todavía no hay resultados, el Dashboard te indica cómo obtenerlos.",
  },
  {
    ruta: "/dashboard",
    elemento: '[data-tour="kpis"]',
    titulo: "Indicadores clave",
    sinResultado: "Los indicadores aparecen cuando el análisis seleccionado conserva valores calculados. Revisa el estado que se señala aquí o elige otro análisis en el historial.",
    texto: "Aquí aparecen los indicadores que pudo calcular el análisis elegido, con su valor y unidad. Si faltan datos, MEPIA lo explica; no todos los análisis incluyen los mismos indicadores.",
  },
  {
    ruta: "/dashboard",
    elemento: '[data-tour="hallazgos"]',
    titulo: "Hallazgos",
    sinResultado: "Los hallazgos aparecen al abrir un análisis que los conserve. Revisa el estado que se señala aquí o elige otro análisis en el historial.",
    texto: "Cada resultado viene con una explicación en lenguaje sencillo, para que sepas qué significa y qué hacer.",
  },

  {
    ruta: "/dashboard",
    elemento: '[data-tour="tendencias"]',
    titulo: "Compara fechas",
    sinResultado: "Para comparar fechas necesitas resultados del mismo indicador y unidad en al menos dos días. Empieza por elegir un análisis guardado.",
    texto: "La tendencia necesita al menos dos fechas con el mismo indicador y unidad. Varias corridas de un día no se suman; los datos ausentes se muestran como faltantes.",
  },

  // ── 3. Salud y Reportes ─────────────────────────────────────────────────
  {
    ruta: "/salud",
    elemento: '[data-tour="nav-salud"]',
    titulo: "Paso 3: Salud del Negocio",
    texto: "Aquí ves las métricas operativas con más detalle y en gráficas.",
  },
  {
    ruta: "/reportes",
    elemento: '[data-tour="nav-reportes"]',
    titulo: "Reportes",
    texto: "El reporte de la auditoría con los hallazgos y anomalías detectadas.",
  },

  // ── 4. Chat IA ──────────────────────────────────────────────────────────
  {
    ruta: "/chat",
    elemento: '[data-tour="nav-chat"]',
    titulo: "Paso 4: Chat IA",
    texto: "¿Tienes dudas sobre tus resultados? Pregúntale al asistente.",
  },
  {
    ruta: "/chat",
    elemento: '[data-tour="pregunta"]',
    titulo: "Haz tu pregunta",
    texto: "Pregunta por un indicador disponible o por un concepto, por ejemplo: «¿Qué significa la conciliación de caja?». Revisa la fecha y las fuentes citadas: el chat no adopta automáticamente la corrida elegida en el Dashboard.",
  },

  // ── 5. Configuración ────────────────────────────────────────────────────
  {
    ruta: "/onboarding",
    elemento: '[data-tour="nav-onboarding"]',
    titulo: "Paso 5: Configuración",
    texto: "MEPIA arranca con una configuración predeterminada recomendada, así que no necesitas llenar nada para empezar. Aquí la puedes ajustar cuando quieras.",
  },
  {
    ruta: "/onboarding",
    elemento: '[data-tour="advanced-config-tabs"]',
    titulo: "Cuatro secciones",
    texto: "La configuración se divide en Identidad, Umbrales, Costos y Reglas. Vamos a verlas una por una.",
    seccionConfig: 1,
  },
  {
    ruta: "/onboarding",
    elemento: '[data-tour="advanced-config-brand"]',
    titulo: "Identidad",
    texto: "Describe el tono y los valores de tu negocio, indica qué recomendaciones no quieres recibir y elige tu foco principal: eficiencia, calidad o crecimiento.",
    seccionConfig: 1,
  },
  {
    ruta: "/onboarding",
    elemento: '[data-tour="advanced-config-thresholds"]',
    titulo: "Umbrales",
    texto: "Define cuándo algo se considera un problema: la diferencia máxima de caja (en % y en pesos), los márgenes de advertencia y crítico, y qué tanto puede subir un costo antes de alertarte.",
    seccionConfig: 2,
  },
  {
    ruta: "/onboarding",
    elemento: '[data-tour="advanced-config-costs"]',
    titulo: "Costos",
    texto: "Registra tus gastos del mes, como renta o nómina: concepto, monto, cuánto pueden variar y si son fijos, variables o inversión.",
    seccionConfig: 3,
  },
  {
    ruta: "/onboarding",
    elemento: '[data-tour="advanced-config-rules"]',
    titulo: "Reglas",
    texto: "Elige qué situaciones son alerta roja inmediata, cuáles son normales en tu negocio y deben ignorarse, y cada cuánto se hace la auditoría.",
    seccionConfig: 4,
  },
  {
    ruta: "/onboarding",
    elemento: '[data-tour="config-guardar"]',
    titulo: "Guardar cambios",
    texto: "Cuando edites tus ajustes, este botón los guarda. El tutorial solo te muestra dónde está: no lo pulsa ni envía cambios por ti.",
    seccionConfig: 4,
  },

  // ── Cierre ──────────────────────────────────────────────────────────────
  {
    ruta: "/dashboard",
    elemento: '[data-tour="ayuda"]',
    titulo: "¡Listo!",
    texto: "Ese es el flujo completo. Si quieres repetir el tutorial, presiona este botón cuando quieras.",
  },
];
