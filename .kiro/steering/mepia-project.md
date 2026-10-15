---
inclusion: always
---

# MEPIA — Mise En Place Artificial Intelligence

## Misión
Copiloto Financiero para dueños de restaurantes que automatiza la auditoría operativa y financiera mediante agentes de IA. El sistema no solo muestra datos: genera frases explicativas sobre la salud del negocio basadas en arquetipos de CEO.

---

## Stack Tecnológico

- **Frontend:** Next.js 15.5.27 (App Router) + Tailwind CSS + Recharts — diseño azul integrado del equipo
- **Backend/DB:** Supabase — Auth, Storage (PDFs), SQL (transacciones)
- **Agentes IA:** Python — LangChain/LangGraph para flujos multi-agente
- **Comunicación:** API REST entre Next.js y el backend Python (FastAPI)

---

## Arquitectura de Agentes

Tres patrones de flujo multi-agente:

1. **Secuencial** — ingesta → limpieza → análisis → insight
2. **Paralelo** — múltiples agentes analizando módulos simultáneamente (caja, gastos, salud)
3. **Loop** — agente de validación que itera hasta resolver discrepancias

### Módulos de Auditoría

| Módulo | Función del Agente |
|---|---|
| Conciliación de Caja | Compara tickets POS vs depósitos reportados |
| Gasto Operativo | Detecta incrementos anómalos en insumos |
| Salud del Negocio | Calcula margen neto y KPIs clave |

---

## Regla de Oro de UX — El Copiloto Habla

**Nunca mostrar solo gráficas o números crudos.**

Cada resultado de agente debe acompañarse de una frase explicativa generada por el Copiloto. El tono varía según el arquetipo del CEO detectado:

- **Operative Genius** — enfocado en eficiencia operativa y procesos
- **Product Purist** — obsesionado con calidad del producto y experiencia
- **Growth Hacker** — orientado a escala, métricas de crecimiento y recompra

### Formato de Output Estándar

La tabla de hallazgos actual renderiza cinco columnas; los indicadores y el chat
tienen sus propias vistas:

```
Módulo | Resultado Forense | Insight CEO | Nivel | Acción
```

Ejemplo ilustrativo:
- **Módulo:** Salud del Negocio
- **Resultado:** Margen de utilidad neta: 18%
- **Insight (Arquetipo Operativo):** "Eres eficiente, pero la inconsistencia en extracciones de espresso está afectando tu recompra."

---

## Ingesta de Documentos

- PDFs de POS y facturas se suben a Supabase Storage
- El agente de extracción usa parsing estructurado (tablas, totales, fechas)
- Los datos limpios se persisten en tablas SQL de Supabase para análisis histórico

---

## Convenciones de Código

- Componentes Next.js en `/app` con Server Components por defecto
- Tailwind: paleta azul de `tailwind.config.ts`; los alias `zinc`/`emerald` están remapeados. Rojo/ámbar conservan estados de alerta
- Python: cada agente es una clase independiente con método `.run(input) -> AgentResult`
- `AgentResult` conserva el contrato base; los nodos nuevos usan contratos propios (`CalcResult`, `AuditInsight`, `ChatAnswer`) del glosario
- Variables y comentarios en español cuando el contexto es de negocio; inglés para código técnico

---

## Estructura de Carpetas

Estado y recorrido completos al 15-oct-2026: [resumen actual](../../docs/estado_actual_mepia.md).
Login previo, negocio propio identificado automáticamente y Chat IA integrado;
tutorial guiado pendiente y adaptación móvil parcial. El árbol siguiente es un
resumen de carpetas, no un inventario exhaustivo de los nodos ya implementados.

```
mepia/
├── app/                  # Next.js App Router
│   ├── dashboard/        # Vista principal del Copiloto
│   └── upload/           # Ingesta de documentos
├── components/
│   └── AuditTable.tsx    # Tabla Módulo | Resultado | Insight
├── agents/               # Python — lógica de agentes
│   ├── base_agent.py
│   ├── cash_reconciliation.py
│   ├── operative_cost.py
│   └── business_health.py
├── api/                  # FastAPI — bridge Next.js ↔ Python
└── supabase/             # Migrations y tipos generados
```
