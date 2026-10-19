/** El análisis es diario: las ventas mandan; las compras pueden ser de otros días. */
export function resolveAuditDate(selected: string, posDates: string[], invoiceDates: string[]): string {
  const valid = (value: string) => /^\d{4}-\d{2}-\d{2}$/.test(value)
    && !Number.isNaN(Date.parse(value)) && new Date(value).toISOString().slice(0, 10) === value;
  const sales = [...new Set(posDates.filter(valid))];
  const invoices = [...new Set(invoiceDates.filter(valid))];
  if (sales.length > 1) throw new Error("Los reportes de ventas son de días distintos. Analiza un día a la vez.");
  if (selected && !valid(selected)) throw new Error("Selecciona una fecha válida para el análisis.");
  if (selected && sales.length && selected !== sales[0]) {
    throw new Error(`La fecha elegida no coincide con las ventas (${sales[0]}). Revisa la fecha antes de analizar.`);
  }
  const date = selected || sales[0] || (invoices.length === 1 ? invoices[0] : "");
  if (!date) throw new Error("No pudimos determinar el día del análisis. Selecciona la fecha que deseas revisar.");
  return date;
}
