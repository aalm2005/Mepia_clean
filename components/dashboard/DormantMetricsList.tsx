interface DormantMetricsListProps {
  metrics: Array<{ metric: string; missing: string[] }>;
  blocked?: Array<{ metric: string; reason: string }>;
  available?: boolean;
}

export function DormantMetricsList({ metrics, blocked = [], available }: DormantMetricsListProps) {
  return (
    <div className="glass p-panel flex flex-col gap-3">
      <h2 className="text-label uppercase tracking-widest text-muted">
        INDICADORES PENDIENTES
      </h2>

      {available === undefined ? (
        <p className="text-zinc-500 text-sm">Aquí verás qué datos faltan después del análisis.</p>
      ) : !available ? (
        <p className="text-zinc-500 text-sm">Este análisis no conserva el detalle de los datos faltantes.</p>
      ) : metrics.length === 0 && blocked.length === 0 ? (
        <p className="text-zinc-500 text-sm">Todas las métricas activas</p>
      ) : (
        <ul className="flex flex-col gap-3">
          {metrics.map((item) => (
            <li key={item.metric} className="flex flex-col gap-1">
              <span className="text-sm text-zinc-400">{item.metric}</span>
              {item.missing.length > 0 && (
                <ul className="flex flex-col gap-0.5">
                  {item.missing.map((field) => (
                    <li
                      key={field}
                      className="text-xs text-zinc-600 font-mono before:content-['·'] before:mr-1.5"
                    >
                      {field}
                    </li>
                  ))}
                </ul>
              )}
            </li>
          ))}
          {blocked.map(item => <li key={item.metric} className="text-sm text-zinc-400">
            {item.metric}: requiere revisión de documentos.
          </li>)}
        </ul>
      )}
    </div>
  );
}
