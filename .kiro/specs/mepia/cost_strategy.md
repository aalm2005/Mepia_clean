# MEPIA — Estrategia de Costos de LLM

**Consulta de resultados — 19-oct-2026:** historial, recuperación, tendencias y
seguimiento de análisis guardados solo leen datos; no ejecutan modelos ni
recalculan el negocio. Crear un análisis nuevo conserva su recorrido y posible
consumo. [Contrato](analysis_history.md). La tabla inferior es la estimación
histórica V1 con sus supuestos, no gasto medido ni precios verificados en este
corte; no se revisaron tarifas ni proveedores reales en esta sincronización.

**Decisión fija — V1**
**Presupuesto máximo aprobado: $0.20 USD por auditoría completa**

---

## Justificación del Presupuesto

MEPIA actúa como CFO Forense para dueños de restaurantes, buscando fugas de margen
operativo que pueden representar miles de pesos mensuales. En este contexto:

- La **precisión es prioritaria** sobre el ahorro en tokens
- Un costo de < $0.20 USD por auditoría es altamente rentable frente al valor generado
- El presupuesto permite usar modelos de alta calidad donde importa, sin comprometer
  la calidad del reporte que lee el dueño del negocio

---

## Desglose por Nodo (Estimación V1)

| Nodo | Modelo | Tokens estimados | Costo estimado |
|------|--------|-----------------|----------------|
| S4 Forensic CFO | `gpt-4o` | ~2,000 tokens | ~$0.010 USD |
| N05 CEO Orchestrator | `gpt-4o` | ~3,000 tokens | ~$0.015 USD |
| N09 Copilot Phrase | `gpt-4o-mini` | ~1,000 tokens | ~$0.001 USD |
| N11 Consultor | `claude-3-5-sonnet-20241022` | ~6,000 tokens | ~$0.018 USD |
| N13 Revisor | `gpt-4o` | ~4,000 tokens × hasta 3 intentos | ~$0.060 USD (peor caso) |
| **Total peor caso** | | | **~$0.104 USD** |

> **Peor caso:** N13 rechaza el borrador 2 veces antes de activar el cortafuegos.
> En el caso promedio (aprobación en primer intento), N13 corre 1 sola vez → ~$0.064 USD total.

---

## Validación Matemática

```
Presupuesto aprobado:  $0.20 USD
Total peor caso:       $0.104 USD
Margen de seguridad:   $0.096 USD (48% del presupuesto disponible como buffer)
```

La arquitectura híbrida cumple el presupuesto con un **margen del 48%**, incluso
en el peor escenario posible (3 ejecuciones de N13).

---

## Decisiones de Arquitectura que Optimizan el Costo

| Decisión | Impacto en costo |
|----------|-----------------|
| `gpt-4o-mini` exclusivo para N09 | N09 es no crítico — ahorra ~$0.014 vs `gpt-4o` |
| `claude-3-5-sonnet` para N11 | Mejor calidad narrativa a menor costo que `gpt-4o` para texto largo |
| Cortafuegos en N13 (máx 2 reintentos) | Limita el peor caso a 3× el costo de N13 |
| N10 y N14 sin LLM (Python puro) | $0.00 en esos nodos |
| N12 skipped en V1 | Elimina un nodo LLM completo del pipeline |

---

## Precios de Referencia (Abril 2026)

> Precios aproximados usados para la estimación. Verificar en la documentación
> oficial de cada proveedor antes de proyecciones financieras.

| Modelo | Input (por 1M tokens) | Output (por 1M tokens) |
|--------|----------------------|------------------------|
| `gpt-4o` | ~$2.50 | ~$10.00 |
| `gpt-4o-mini` | ~$0.15 | ~$0.60 |
| `claude-3-5-sonnet-20241022` | ~$3.00 | ~$15.00 |

---

## Reglas de Monitoreo

1. Registrar `model_used` y `generation_duration_ms` en cada `audit_results` para
   auditar el costo real por run en producción
2. Si el costo promedio real supera $0.15 USD por auditoría → revisar si N13 está
   rechazando con frecuencia anormal (posible problema de prompt en N11)
3. Si el costo promedio real supera $0.20 USD → escalar como incidente de arquitectura

---

## Archivos relacionados
- `_index.md` — mapa de nodos; los modelos del motor se detallan en las specs de cada nodo
- `s4_auditoria_ia.md` — modelo S4
- `n05_ceo_orchestrator.md` — modelo N05
- `n09_gastos.md` — modelo N09
- `n11_consultor.md` — modelo N11 + temperatura dinámica
- `n13_revisor.md` — modelo N13 + lógica de cortafuegos
