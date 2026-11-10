# Diseño Frontend — Secuencia de consulta y análisis

Vigente al 19-oct-2026. [Estados y errores](design_flows.md).

## Consultar resultados existentes

```mermaid
sequenceDiagram
    participant U as Usuario
    participant V as Dashboard / Salud / Reportes
    participant P as Proxy Next
    participant A as FastAPI
    participant D as Base MEPIA
    U->>V: Entrar con sesión y negocio propio
    V->>P: GET /api/analyses/{business_id}?page=0 + Bearer
    P->>A: GET /business/{business_id}/analyses + Bearer
    A->>D: Verificar propietario antes de auditorías
    D-->>V: Historial paginado N05
    alt run_id explícito o referencia recordada
        V->>P: GET /api/analyses/{business_id}/{run_id}
    else Sin selección
        V->>P: GET /api/analyses/{business_id}/latest
        P->>A: Último N05 terminado del negocio autorizado
        A-->>V: Corrida o ausencia/límite explícitos
        V->>P: GET resultado de la corrida recuperada
    end
    P->>A: Lectura protegida de resultado
    A->>D: N05 propio y S3 explícito compatible si aplica
    A-->>V: Resultado guardado; error claro si ausente/ajeno
    V->>P: GET /api/analyses/{business_id}/{run_id}/trends
    P->>A: Resultados comparables hasta fecha seleccionada
    A-->>V: Fechas ordenadas, una corrida por fecha y faltantes
    opt Escalación guardada
        V->>P: GET /api/analyses/{business_id}/{run_id}/layer3
        P->>A: Resolver padre guardado del N05 autorizado
        A-->>V: Estado avanzado, no inicio aún o fallo saneado
    end
    U->>V: Elegir otra corrida / navegar / recargar
    Note over V,D: Solo lecturas. No motor, generación ni escritura de resultados.
```

Cada GET verifica sesión y propietario. El enlace explícito inválido no dispara
fallback. Solo se repite la lectura del análisis mientras está running; el
seguimiento avanzado termina al completar/fallar. El cliente descarta respuestas
antiguas ante cambios de usuario, negocio o corrida.

## Crear un análisis nuevo

Login → negocio propio → Documentos → defaults si faltan → POS PDF/factura
XML/PDF → extracción/revisión → fecha coherente → POST `/api/audit` →
POST `/orchestrator/run` → ejecución y guardado → resultado con run_id → Dashboard.
El endpoint espera la ejecución N05; no se documenta como un 202 asíncrono inicial.
La escalación puede continuar su trabajo adicional y estado por separado.
Este recorrido puede escribir datos y consumir modelos; no se ejecutó durante
la sincronización documental. El ensayo real sigue pendiente.


[Versión anterior conservada](../../../docs/history/documentation_before_sync_20261019/.kiro/specs/mepia/design_flows_main.md). Sus estados y cifras describen su fecha original.
