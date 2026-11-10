export const analysisStatus: Record<string,string> = {completed:"Completado",partial:"Completado con datos pendientes",
  escalated:"Completado con revisión avanzada",failed:"Fallido",running:"En proceso",unknown:"Estado no disponible"};
const names: Record<string, string> = {
  avg_ticket: "Ticket promedio",
  burn_rate: "Gasto operativo diario",
  cancellation_rate: "Tasa de cancelaciones",
  cash_reconciliation: "Diferencia de caja",
  category_mix: "Distribución de ventas por categoría",
  channel_mix: "Distribución de ventas por canal",
  commission_cost_ratio: "Comisiones de entrega sobre ventas",
  concentracion_ingresos: "Concentración de ingresos",
  conciliacion_caja: "Diferencia de caja",
  consistencia_precios: "Consistencia de precios",
  contribution_margin: "Margen de contribución",
  contribution_margin_by_channel: "Margen de contribución por canal",
  daily_break_even: "Punto de equilibrio diario",
  delivery_commission_cost: "Costo de comisiones de entrega",
  discount_rate: "Tasa de descuento",
  health_score: "Margen medio por producto",
  hourly_sales_pattern: "Ventas por hora del día",
  inflacion_precio: "Variación del precio de compra",
  inventory_variance: "Variación de inventario",
  inventory_variance_merma: "Merma de inventario",
  item_discount_split: "Descuentos por producto y ticket",
  labor_cost_ratio: "Costo laboral sobre ventas",
  loyalty_redemption_cost: "Costo de canjes de lealtad",
  margen_contribucion: "Margen de contribución",
  merma: "Merma",
  modifier_attach_rate: "Proporción de productos con extras",
  operative_cost_margin: "Gasto operativo diario",
  patron_horario_ventas: "Ventas por hora del día",
  payment_mix: "Distribución por forma de pago",
  price_consistency: "Consistencia de precios",
  price_inflation: "Variación del precio de compra",
  punto_equilibrio_diario: "Punto de equilibrio diario",
  reprint_rate: "Tasa de reimpresiones",
  revenue_concentration: "Concentración de ingresos",
  sales_by_branch: "Ventas por sucursal",
  sales_by_staff: "Ventas por integrante del personal",
  sales_per_labor_hour: "Ventas por hora trabajada",
  shift_cash_variance: "Diferencia de caja por turno",
  staff_courtesy_ratio: "Cortesías por encima del límite",
  stock_days_remaining: "Días de inventario restantes",
  tasa_descuento: "Tasa de descuento",
  ticket_promedio: "Ticket promedio",
  ticket_volume: "Cantidad de tickets",
  top_bottom_sellers: "Productos más y menos vendidos",
  ventas_por_staff: "Ventas por integrante del personal",
  ventas_por_sucursal: "Ventas por sucursal",
  volumen_tickets: "Cantidad de tickets",
  waste_analysis: "Análisis de merma",
  waste_cost: "Costo de merma registrada",
};
export function metricLabel(metric: string) { return names[metric] ?? metric.replaceAll("_", " "); }
export function analysisLabel(item: {run_id:string; date:string; created_at:string|null}) {
  const saved = item.created_at ? new Date(item.created_at) : null;
  return `Fecha analizada: ${item.date} · Guardado: ${saved && Number.isFinite(saved.getTime())
    ? saved.toLocaleString("es-MX",{year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit",second:"2-digit"})
    : "sin fecha de guardado"} · Ref. ${item.run_id.slice(0,8)}`;
}

export function missingDataLabel(field:string) {
  const labels:Record<string,string>={tickets:"Tickets de venta",pos_inputs:"Reportes de venta",cash_counts:"Conteos de caja",recipes:"Recetas y costos de productos",
    recipe_costs:"Costos de recetas",inventory:"Inventario",inventory_movements:"Movimientos de inventario",transactions:"Compras y gastos",
    staff:"Personal",branches:"Sucursales",discounts:"Descuentos",daily_sales:"Ventas de la fecha",sales:"Ventas",costs:"Costos"};
  return labels[field]??field.replaceAll("_"," ");
}
