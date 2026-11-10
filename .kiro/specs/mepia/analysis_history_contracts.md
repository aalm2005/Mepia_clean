# Contratos de lectura del historial

Proyecciones de `audit_results`, sin migración ni cambios en CalcResult.
Implementación: types/analysis.ts, types/audit.ts y api/analysis_history.py.

```typescript
interface AnalysisSummary {
  run_id: string;
  date: string;
  created_at: string | null;
  status: PipelineStatus | "unknown";
}
interface AnalysisTrend {
  business_id: string;
  run_id: string;
  periods: number;
  limited: boolean;
  ignored_results: number;
  policy: string;
  series: Array<{
    metric: string;
    unit: string;
    label: string;
    valid_periods: number;
    missing_periods: number;
    points: Array<{
      date: string;
      value: string | null;
      run_id: string | null;
    }>;
  }>;
}
```

date es la fecha analizada; created_at es el guardado y no sustituye esa fecha.
run_id identifica una corrida, incluso cuando varias comparten fecha.
El listado agrega next_page; latest agrega información de límite cuando aplica.
limited e ignored_results explican alcance/exclusiones, no resultados calculados.
PipelineStatus unknown representa solo lectura histórica sin estado acreditado.

`forensic_status_available` es booleano derivado en api/audit_results.py:
exige informe original con negocio, fecha, generated_at y anomalies, cálculo
finito válido y corrida terminada. Un fallback visual no acredita evaluación.
Es distinto de `metric_status_available`, disponibilidad del estado S2.
No se persiste ninguno como un nuevo resultado del motor.

CalcResult.value admite decimal textual, número o null. La presentación acepta
solo finitos/estados válidos; vacío, booleano y texto inválido no son cero.
Las tendencias comparan significado, unidad y ámbito exactos, con null para
ausencias o ambigüedad. Los porcentajes no se reescalan para visualización.

Las referencias de selección en sessionStorage identifican usuario, negocio y
corrida; no son resultados, autorización ni historial conversacional persistido.

[API](analysis_history.md), [tendencias](analysis_history_trends.md),
[estados visibles](analysis_history_ui.md), [glosario](_glossary.md).
