"""Catalogo financiero permitido para el chatbot de MEPIA.

El catalogo describe el dominio del motor determinista; no implementa formulas
ni acepta operandos. Las relaciones matematicas se conservan unicamente como
texto explicativo para que el chatbot pueda interpretar resultados ya emitidos.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


MetricAvailability = Literal["pipeline", "engine_support"]


class MetricDefinition(BaseModel):
    """Contrato explicativo de una metrica calculada por el motor."""

    metric_id: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    definition: str = Field(min_length=1)
    interpretation: str = Field(min_length=1)
    formula_explanation: str = Field(min_length=1)
    inputs: list[str] = Field(min_length=1)
    units: list[str] = Field(min_length=1)
    aliases: list[str] = Field(default_factory=list)
    result_metric_names: list[str] = Field(min_length=1)
    result_metric_prefixes: list[str] = Field(default_factory=list)
    related_concepts: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    availability: MetricAvailability
    calculation_owner: Literal["deterministic_engine"] = "deterministic_engine"


class MetricConceptDefinition(BaseModel):
    """Concepto necesario para comprender una o mas metricas del motor."""

    term: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    definition: str = Field(min_length=1)
    aliases: list[str] = Field(default_factory=list)
    related_metrics: list[str] = Field(default_factory=list)


class ChatScopePolicy(BaseModel):
    """Frontera fija del Paso 2, consumible por capas posteriores."""

    knowledge_scope: Literal["engine_metric_domain"] = "engine_metric_domain"
    calculation_allowed: Literal[False] = False
    allowed_operations: list[str] = Field(
        default_factory=lambda: [
            "retrieve_existing_engine_results",
            "explain_engine_metrics",
            "paraphrase_verified_results",
        ]
    )
    prohibited_operations: list[str] = Field(
        default_factory=lambda: [
            "calculate",
            "recalculate",
            "aggregate",
            "derive_numeric_comparison",
            "project",
            "simulate",
        ]
    )


CHAT_SCOPE_POLICY = ChatScopePolicy()


def _metric(
    metric_id: str,
    display_name: str,
    definition: str,
    interpretation: str,
    formula_explanation: str,
    inputs: list[str],
    units: list[str],
    *,
    aliases: list[str] | None = None,
    result_names: list[str] | None = None,
    result_prefixes: list[str] | None = None,
    concepts: list[str] | None = None,
    limitations: list[str] | None = None,
    availability: MetricAvailability = "pipeline",
) -> MetricDefinition:
    return MetricDefinition(
        metric_id=metric_id,
        display_name=display_name,
        definition=definition,
        interpretation=interpretation,
        formula_explanation=formula_explanation,
        inputs=inputs,
        units=units,
        aliases=aliases or [],
        result_metric_names=result_names or [metric_id],
        result_metric_prefixes=result_prefixes or [],
        related_concepts=concepts or [],
        limitations=limitations or [],
        availability=availability,
    )


METRIC_CATALOG = (
    _metric(
        "cash_reconciliation", "Conciliacion de caja",
        "Diferencia entre el efectivo esperado por la operacion y el efectivo contado.",
        "Permite identificar faltantes o sobrantes de caja registrados por el motor.",
        "El motor contrasta efectivo contado con efectivo esperado.",
        ["cortes de caja", "movimientos y ventas en efectivo"], ["MXN"],
        aliases=["conciliacion de caja", "cash reconciliation"],
        result_names=["cash_reconciliation", "conciliacion_caja"],
        concepts=["efectivo_esperado", "diferencia_de_caja"],
    ),
    _metric(
        "daily_break_even", "Punto de equilibrio diario",
        "Venta diaria requerida para cubrir los costos considerados por el motor.",
        "Indica el nivel de venta en el que esos costos quedan cubiertos.",
        "El motor relaciona costos fijos diarios y margen de contribucion.",
        ["costos fijos", "margen de contribucion"], ["MXN"],
        aliases=["punto de equilibrio", "break even"],
        result_names=["daily_break_even", "punto_equilibrio_diario"],
        concepts=["costos_fijos", "margen_contribucion"],
    ),
    _metric(
        "operative_cost_margin", "Costo operativo diario",
        "Promedio diario de costos fijos y variables usado como aproximacion operativa.",
        "Expresa consumo monetario diario; pese al nombre historico, no es un margen porcentual.",
        "El motor promedia los costos operativos registrados en el periodo.",
        ["costos fijos", "costos variables", "periodo"], ["MXN/dia"],
        aliases=["costo operativo", "operative cost margin", "burn rate operativo"],
        result_names=["operative_cost_margin"], concepts=["burn_rate", "costos_operativos"],
        limitations=["El identificador legado dice margin, pero la salida es un costo diario, no un porcentaje."],
    ),
    _metric(
        "health_score", "Indicador de margen promedio",
        "Promedio monetario del margen de contribucion disponible por producto.",
        "Resume los margenes calculables; no es una puntuacion compuesta de salud del negocio.",
        "El motor promedia los margenes de contribucion monetarios de productos validos.",
        ["margenes de contribucion por producto"], ["MXN"],
        aliases=["health score", "salud del negocio", "margen promedio"],
        result_names=["health_score"], concepts=["margen_contribucion"],
        limitations=["No combina ventas, caja, inventario ni otras dimensiones de salud."],
    ),
    _metric(
        "inventory_variance", "Variacion de inventario por merma",
        "Resultados de merma por ingrediente generados dentro del analisis de inventario.",
        "Muestra desviaciones por ingrediente; no representa una unica variacion global.",
        "El motor compara consumo o existencia observada con lo esperado para cada ingrediente.",
        ["inventario", "consumo teorico", "movimientos o conteos"], ["unidad de inventario", "%", "MXN"],
        aliases=["variacion de inventario", "inventory variance"],
        result_names=["inventory_variance"], result_prefixes=["inventory_variance_"],
        concepts=["merma", "consumo_teorico"],
        limitations=["Puede producir varias salidas con prefijo inventory_variance_, una por resultado de merma."],
    ),
    _metric(
        "avg_ticket", "Ticket promedio",
        "Subtotal promedio de venta por ticket del periodo.",
        "Describe el importe medio antes de impuestos registrado en cada ticket.",
        "El motor divide la suma de subtotales entre el numero de tickets validos.",
        ["subtotales de tickets", "cantidad de tickets"], ["MXN"],
        aliases=["ticket promedio", "average ticket"],
        result_names=["avg_ticket", "ticket_promedio"], concepts=["ticket", "subtotal"],
    ),
    _metric(
        "channel_mix", "Mezcla de canales",
        "Distribucion de las ventas entre comedor, para llevar y delivery.",
        "Ayuda a entender que proporcion de la venta corresponde a cada canal.",
        "El motor compara la venta de cada canal con la venta total del periodo.",
        ["tickets", "canal de venta", "subtotales"], ["%"],
        aliases=["mix de canales", "mezcla de canales"], concepts=["canal_de_venta"],
    ),
    _metric(
        "discount_rate", "Tasa de descuento",
        "Peso de los descuentos aplicados sobre el subtotal de ventas.",
        "Muestra cuanto de la venta antes de descuentos fue reducido y puede desglosarse por responsable.",
        "El motor relaciona descuentos registrados con subtotales de venta.",
        ["descuentos", "subtotales", "responsable"], ["%"],
        aliases=["tasa de descuento", "discount rate"],
        result_names=["discount_rate", "tasa_descuento"], concepts=["descuento", "subtotal"],
    ),
    _metric(
        "hourly_sales_pattern", "Patron horario de ventas",
        "Distribucion de ventas por hora con periodos de mayor y menor actividad.",
        "Identifica horas pico y valle segun las ventas registradas.",
        "El motor agrupa los importes de venta por hora del dia.",
        ["fecha y hora de tickets", "ventas"], ["MXN por hora"],
        aliases=["patron horario", "horas pico", "hourly sales pattern"],
        result_names=["hourly_sales_pattern", "patron_horario_ventas"], concepts=["hora_pico", "hora_valle"],
    ),
    _metric(
        "sales_by_staff", "Ventas por personal",
        "Ventas y tickets atribuidos a cada cajero o mesero disponible.",
        "Permite observar la distribucion operativa por integrante sin inferir por si sola desempeno o causa.",
        "El motor agrupa ventas y tickets por identificador de personal.",
        ["tickets", "personal responsable", "ventas"], ["MXN", "tickets"],
        aliases=["ventas por personal", "ventas por staff"],
        result_names=["sales_by_staff", "ventas_por_staff"], concepts=["personal"],
        limitations=["Es informacion sensible y no demuestra causalidad ni calidad individual."],
    ),
    _metric(
        "sales_by_branch", "Ventas por sucursal",
        "Ventas agregadas por sucursal cuando el negocio tiene mas de una.",
        "Permite revisar la distribucion de ventas entre ubicaciones.",
        "El motor agrupa las ventas por sucursal.",
        ["tickets", "sucursal", "ventas"], ["MXN"],
        aliases=["ventas por sucursal", "sales by branch"],
        result_names=["sales_by_branch", "ventas_por_sucursal"], concepts=["sucursal"],
        limitations=["Solo es aplicable cuando existen datos de multiples sucursales."],
    ),
    _metric(
        "top_bottom_sellers", "Productos mas y menos vendidos",
        "Clasificacion de productos por cantidad vendida o ingreso.",
        "Presenta extremos del ranking observado sin recomendar automaticamente retirar o promover productos.",
        "El motor agrega ventas por producto y ordena los resultados.",
        ["lineas de ticket", "productos", "cantidades", "ingresos"], ["unidades", "MXN"],
        aliases=["mas vendidos", "menos vendidos", "top y bottom sellers"], concepts=["ranking_de_productos"],
    ),
    _metric(
        "revenue_concentration", "Concentracion de ingresos",
        "Proporcion del catalogo de productos que acumula la mayor parte del ingreso.",
        "Ayuda a reconocer dependencia de pocos productos y el patron de concentracion observado.",
        "El motor ordena ingresos por producto y determina cuantos acumulan el 80 por ciento.",
        ["ingresos por producto", "catalogo vendido"], ["%"],
        aliases=["concentracion de ingresos", "pareto de ventas"],
        result_names=["revenue_concentration", "concentracion_ingresos"], concepts=["concentracion", "pareto"],
    ),
    _metric(
        "category_mix", "Mezcla de categorias",
        "Distribucion de ventas por grupo o subgrupo de productos.",
        "Muestra el peso relativo de cada categoria en las ventas.",
        "El motor agrupa ventas por categoria y las compara con el total.",
        ["productos", "categorias", "ventas"], ["%"],
        aliases=["mix de categorias", "mezcla de categorias"], concepts=["categoria"],
    ),
    _metric(
        "modifier_attach_rate", "Tasa de modificadores",
        "Proporcion de lineas de venta que incluyen un modificador o extra.",
        "Refleja la adopcion observada de complementos registrados.",
        "El motor compara lineas con modificadores contra lineas elegibles.",
        ["lineas de ticket", "modificadores"], ["%"],
        aliases=["tasa de extras", "modifier attach rate"], concepts=["modificador"],
    ),
    _metric(
        "item_discount_split", "Distribucion de descuentos",
        "Separacion entre descuentos aplicados a articulos y descuentos aplicados al ticket.",
        "Indica donde se originaron los descuentos registrados.",
        "El motor clasifica y contrasta importes de descuento por nivel de aplicacion.",
        ["descuentos de articulos", "descuentos de ticket"], ["%", "MXN"],
        aliases=["descuento por articulo", "descuento por ticket"], concepts=["descuento"],
    ),
    _metric(
        "payment_mix", "Mezcla de metodos de pago",
        "Distribucion de cobros entre los metodos de pago registrados.",
        "Muestra la participacion de efectivo, tarjeta u otros medios disponibles.",
        "El motor agrupa cobros por metodo y los compara con el total cobrado.",
        ["pagos", "metodo de pago", "importe"], ["%", "MXN"],
        aliases=["mix de pagos", "metodos de pago"], concepts=["metodo_de_pago"],
    ),
    _metric(
        "staff_courtesy_ratio", "Proporcion de cortesias del personal",
        "Peso de las cortesias que exceden el permitido configurado por responsable sobre el subtotal de ventas.",
        "Permite observar el excedente no cubierto por la cortesia autorizada y su responsable.",
        "El motor descuenta el permitido por responsable y relaciona solo el excedente con el subtotal.",
        ["cortesias", "permitido configurado", "subtotales", "responsable"], ["%", "MXN"],
        aliases=["cortesias del personal", "staff courtesy ratio"], concepts=["cortesia"],
        limitations=["No establece por si sola si una cortesia fue correcta o indebida."],
    ),
    _metric(
        "loyalty_redemption_cost", "Costo de redenciones de lealtad",
        "Importe de beneficios de lealtad redimidos en el periodo.",
        "Muestra el costo registrado de redenciones y, cuando existe, su peso en ventas.",
        "El motor suma los importes de redencion registrados.",
        ["redenciones de lealtad", "importe", "ventas"], ["MXN", "%"],
        aliases=["costo de lealtad", "redenciones"], concepts=["redencion_de_lealtad"],
    ),
    _metric(
        "price_consistency", "Consistencia de precios",
        "Revision de diferencias entre precios observados y precios esperados por la configuracion disponible.",
        "Senala coincidencias o discrepancias que el motor encontro.",
        "El motor contrasta precios de venta con precios esperados de receta o configuracion.",
        ["precios observados", "precios esperados", "productos o recetas"], ["MXN", "conteo"],
        aliases=["consistencia de precios", "price consistency"],
        result_names=["price_consistency", "consistencia_precios"], concepts=["precio_esperado"],
    ),
    _metric(
        "delivery_commission_cost", "Costo de comisiones de delivery",
        "Costo estimado por comisiones de plataformas de entrega segun tasas configuradas.",
        "Muestra el importe de comisiones asociado a ventas de delivery.",
        "El motor aplica la tasa configurada de cada plataforma a sus ventas registradas.",
        ["ventas de delivery", "plataforma", "tasa configurada"], ["MXN"],
        aliases=["comision de delivery", "costo de delivery"], concepts=["comision_delivery"],
        limitations=["Depende de que las tasas de comision esten configuradas correctamente."],
    ),
    _metric(
        "commission_cost_ratio", "Proporcion del costo de comisiones",
        "Peso del costo de comisiones de delivery sobre el subtotal total del dia.",
        "Indica que parte de la venta total representa ese costo estimado.",
        "El motor relaciona las comisiones estimadas con el subtotal de todas las ventas.",
        ["costo de comisiones", "subtotal total"], ["%"],
        aliases=["ratio de comisiones", "commission cost ratio"], concepts=["comision_delivery", "subtotal"],
    ),
    _metric(
        "contribution_margin_by_channel", "Margen de contribucion por canal",
        "Margen de contribucion estimado para cada canal de venta.",
        "Permite comparar la contribucion observada de comedor, para llevar y delivery.",
        "El motor relaciona ventas y costos variables atribuibles dentro de cada canal.",
        ["ventas por canal", "costos variables", "comisiones"], ["ratio", "MXN"],
        aliases=["margen por canal", "contribution margin by channel"], concepts=["margen_contribucion", "canal_de_venta"],
        limitations=["La salida principal puede ser nula; el desglose util se encuentra en el contexto emitido por el motor."],
    ),
    _metric(
        "ticket_volume", "Volumen de tickets",
        "Cantidad de tickets registrados en el periodo o turno.",
        "Representa actividad transaccional, no ingreso monetario.",
        "El motor cuenta los tickets validos del alcance solicitado.",
        ["tickets", "fecha o turno"], ["tickets"],
        aliases=["cantidad de tickets", "volumen de tickets"],
        result_names=["ticket_volume", "volumen_tickets"], concepts=["ticket"],
    ),
    _metric(
        "cancellation_rate", "Tasa de cancelacion",
        "Proporcion de cancelaciones respecto de los tickets registrados.",
        "Muestra la frecuencia observada de cancelaciones y sus desgloses disponibles.",
        "El motor compara cancelaciones con el total de tickets.",
        ["cancelaciones", "tickets", "momento y responsable"], ["%"],
        aliases=["tasa de cancelaciones", "cancellation rate"], concepts=["cancelacion"],
    ),
    _metric(
        "reprint_rate", "Tasa de reimpresion",
        "Proporcion de reimpresiones respecto de los tickets registrados.",
        "Muestra la frecuencia observada de reimpresiones y sus responsables disponibles.",
        "El motor compara reimpresiones con el total de tickets.",
        ["reimpresiones", "tickets", "responsable"], ["%"],
        aliases=["tasa de reimpresiones", "reprint rate"], concepts=["reimpresion"],
    ),
    _metric(
        "shift_cash_variance", "Variacion de caja por turno",
        "Suma de faltantes y sobrantes registrados por turno.",
        "Permite localizar diferencias de caja en el turno correspondiente.",
        "El motor agrega las diferencias de cortes de caja por turno.",
        ["cortes de caja", "turnos", "diferencias"], ["MXN"],
        aliases=["diferencia de caja por turno", "shift cash variance"], concepts=["turno", "diferencia_de_caja"],
    ),
    _metric(
        "labor_cost_ratio", "Proporcion de costo laboral",
        "Peso del costo laboral estimado sobre las ventas del periodo.",
        "Indica cuanto representan los costos de personal frente a la venta observada.",
        "El motor relaciona costo laboral estimado con ventas.",
        ["horas trabajadas", "tarifas o costo laboral", "ventas"], ["%"],
        aliases=["ratio de costo laboral", "costo laboral sobre ventas"], concepts=["costo_laboral", "horas_trabajadas"],
    ),
    _metric(
        "sales_per_labor_hour", "Ventas por hora laboral",
        "Venta registrada por cada hora de trabajo registrada.",
        "Expresa productividad comercial por hora laboral sin explicar sus causas.",
        "El motor relaciona ventas con horas trabajadas.",
        ["ventas", "horas trabajadas"], ["MXN/hora"],
        aliases=["ventas por hora trabajada", "sales per labor hour"], concepts=["horas_trabajadas", "productividad_laboral"],
    ),
    _metric(
        "waste_cost", "Costo de merma",
        "Costo monetario de la merma registrada.",
        "Muestra el impacto monetario de desperdicios o perdidas capturados.",
        "El motor valora la cantidad de merma con el costo unitario disponible.",
        ["mermas registradas", "cantidades", "costos unitarios"], ["MXN"],
        aliases=["costo de merma", "waste cost"], concepts=["merma", "costo_unitario"],
    ),
    _metric(
        "stock_days_remaining", "Dias de inventario restantes",
        "Estimacion de dias que el inventario puede sostener el consumo reciente.",
        "La salida resume el ingrediente con menor cobertura disponible.",
        "El motor relaciona existencia actual con consumo teorico promedio reciente.",
        ["existencias", "consumo teorico reciente", "ingredientes"], ["dias"],
        aliases=["dias de inventario", "cobertura de inventario"], concepts=["consumo_teorico", "existencia_actual"],
        limitations=["El valor principal corresponde al minimo entre ingredientes calculables."],
    ),
    _metric(
        "contribution_margin", "Margen de contribucion por producto",
        "Importe o proporcion que queda despues de los costos variables atribuibles.",
        "Ayuda a entender cuanto contribuye un producto a cubrir costos fijos.",
        "El motor relaciona precio de venta y costos variables del producto.",
        ["precio de venta", "receta", "costos variables"], ["MXN", "%"],
        aliases=["margen de contribucion", "margen por producto"],
        result_names=["contribution_margin", "margen_contribucion"], concepts=["margen_contribucion", "costos_variables"],
        availability="engine_support",
    ),
    _metric(
        "waste_analysis", "Analisis de merma",
        "Desviacion de inventario o consumo para un ingrediente frente a lo esperado.",
        "Describe una merma individual que puede alimentar el analisis de inventario.",
        "El motor compara cantidades observadas y teoricas compatibles.",
        ["ingrediente", "inventario", "consumo teorico", "unidades"], ["unidad de inventario", "%", "MXN"],
        aliases=["analisis de merma", "merma"], result_names=["waste_analysis", "merma"],
        concepts=["merma", "consumo_teorico"], availability="engine_support",
    ),
    _metric(
        "burn_rate", "Consumo operativo diario",
        "Promedio diario de costos operativos registrados.",
        "Expresa cuanto costo consume la operacion por dia en el periodo analizado.",
        "El motor promedia costos fijos y variables del periodo.",
        ["costos fijos", "costos variables", "dias del periodo"], ["MXN/dia"],
        aliases=["burn rate", "ritmo de gasto"], concepts=["costos_operativos"], availability="engine_support",
    ),
    _metric(
        "price_inflation", "Inflacion de precio de ingrediente",
        "Cambio observado en el precio de compra de un ingrediente entre registros comparables.",
        "Permite reconocer aumentos o disminuciones historicas emitidas por el motor.",
        "El motor compara precios historicos compatibles del mismo ingrediente.",
        ["ingrediente", "historial de precios", "fechas", "unidades"], ["%", "MXN"],
        aliases=["inflacion de precio", "aumento de insumo"],
        result_names=["price_inflation", "inflacion_precio"], concepts=["precio_de_compra"],
        availability="engine_support",
    ),
)


CONCEPT_CATALOG = (
    MetricConceptDefinition(term="ticket", display_name="Ticket", definition="Registro de una transaccion de venta usado por las metricas del motor.", aliases=["comanda", "venta registrada"], related_metrics=["avg_ticket", "ticket_volume", "cancellation_rate", "reprint_rate"]),
    MetricConceptDefinition(term="subtotal", display_name="Subtotal", definition="Importe de venta antes de los ajustes que el motor distingue como impuestos u otros totales.", aliases=["venta antes de impuestos"], related_metrics=["avg_ticket", "discount_rate", "commission_cost_ratio"]),
    MetricConceptDefinition(term="margen_contribucion", display_name="Margen de contribucion", definition="Importe o proporcion que queda de una venta despues de costos variables atribuibles y que contribuye a cubrir costos fijos.", aliases=["margen de contribucion", "contribution margin"], related_metrics=["contribution_margin", "daily_break_even", "health_score", "contribution_margin_by_channel"]),
    MetricConceptDefinition(term="costos_fijos", display_name="Costos fijos", definition="Costos considerados por el motor que no dependen directamente del volumen vendido en el periodo.", aliases=["costo fijo"], related_metrics=["daily_break_even", "operative_cost_margin", "burn_rate"]),
    MetricConceptDefinition(term="costos_variables", display_name="Costos variables", definition="Costos que el motor atribuye a productos, ventas o volumen operativo.", aliases=["costo variable"], related_metrics=["contribution_margin", "contribution_margin_by_channel", "burn_rate"]),
    MetricConceptDefinition(term="costos_operativos", display_name="Costos operativos", definition="Costos fijos y variables incluidos por el motor para describir el consumo de la operacion.", aliases=["gastos operativos"], related_metrics=["operative_cost_margin", "burn_rate"]),
    MetricConceptDefinition(term="burn_rate", display_name="Consumo operativo diario", definition="Promedio diario de costos operativos; en MEPIA no significa automaticamente consumo de efectivo libre.", aliases=["ritmo de gasto", "burn rate"], related_metrics=["operative_cost_margin", "burn_rate"]),
    MetricConceptDefinition(term="efectivo_esperado", display_name="Efectivo esperado", definition="Efectivo que deberia resultar de los movimientos y ventas registrados para la conciliacion.", aliases=["caja esperada"], related_metrics=["cash_reconciliation"]),
    MetricConceptDefinition(term="diferencia_de_caja", display_name="Diferencia de caja", definition="Separacion entre el efectivo contado y el esperado; puede ser faltante o sobrante.", aliases=["faltante de caja", "sobrante de caja"], related_metrics=["cash_reconciliation", "shift_cash_variance"]),
    MetricConceptDefinition(term="merma", display_name="Merma", definition="Cantidad o costo de inventario desperdiciado, perdido o distinto de lo esperado por el motor.", aliases=["desperdicio", "waste"], related_metrics=["inventory_variance", "waste_analysis", "waste_cost"]),
    MetricConceptDefinition(term="consumo_teorico", display_name="Consumo teorico", definition="Consumo esperado derivado de las ventas y recetas disponibles para el motor.", aliases=["consumo esperado"], related_metrics=["inventory_variance", "waste_analysis", "stock_days_remaining"]),
    MetricConceptDefinition(term="existencia_actual", display_name="Existencia actual", definition="Cantidad de inventario disponible que el motor usa para estimar cobertura.", aliases=["stock actual"], related_metrics=["stock_days_remaining"]),
    MetricConceptDefinition(term="costo_unitario", display_name="Costo unitario", definition="Costo disponible de una unidad compatible de ingrediente usado para valorar merma.", aliases=["costo por unidad"], related_metrics=["waste_cost"]),
    MetricConceptDefinition(term="canal_de_venta", display_name="Canal de venta", definition="Origen operativo de la venta, como comedor, para llevar o delivery.", aliases=["canal"], related_metrics=["channel_mix", "contribution_margin_by_channel"]),
    MetricConceptDefinition(term="descuento", display_name="Descuento", definition="Reduccion registrada sobre un articulo o ticket que alimenta las metricas de descuentos.", aliases=["rebaja"], related_metrics=["discount_rate", "item_discount_split"]),
    MetricConceptDefinition(term="hora_pico", display_name="Hora pico", definition="Hora con actividad de ventas alta dentro del patron observado por el motor.", aliases=["horario pico"], related_metrics=["hourly_sales_pattern"]),
    MetricConceptDefinition(term="hora_valle", display_name="Hora valle", definition="Hora con actividad de ventas baja dentro del patron observado por el motor.", aliases=["horario valle"], related_metrics=["hourly_sales_pattern"]),
    MetricConceptDefinition(term="personal", display_name="Personal", definition="Cajero, mesero u otro responsable disponible en los registros usados por las metricas.", aliases=["staff", "empleado"], related_metrics=["sales_by_staff", "staff_courtesy_ratio"]),
    MetricConceptDefinition(term="sucursal", display_name="Sucursal", definition="Ubicacion operativa a la que el motor atribuye ventas cuando existe esa dimension.", aliases=["branch"], related_metrics=["sales_by_branch"]),
    MetricConceptDefinition(term="ranking_de_productos", display_name="Ranking de productos", definition="Orden de productos segun cantidades o ingresos observados por el motor.", aliases=["productos mas vendidos", "productos menos vendidos"], related_metrics=["top_bottom_sellers"]),
    MetricConceptDefinition(term="concentracion", display_name="Concentracion de ingresos", definition="Grado en que una parte del catalogo acumula la mayor parte de los ingresos observados.", aliases=["concentracion de ventas"], related_metrics=["revenue_concentration"]),
    MetricConceptDefinition(term="pareto", display_name="Referencia de Pareto", definition="Lectura de concentracion que identifica cuantos productos acumulan el 80 por ciento del ingreso en esta metrica.", aliases=["regla 80 20"], related_metrics=["revenue_concentration"]),
    MetricConceptDefinition(term="categoria", display_name="Categoria de producto", definition="Grupo o subgrupo usado por el motor para distribuir las ventas.", aliases=["familia de producto", "subcategoria"], related_metrics=["category_mix"]),
    MetricConceptDefinition(term="modificador", display_name="Modificador", definition="Extra o ajuste asociado a una linea de venta y registrado de forma identificable.", aliases=["extra", "complemento"], related_metrics=["modifier_attach_rate"]),
    MetricConceptDefinition(term="metodo_de_pago", display_name="Metodo de pago", definition="Medio registrado para cobrar una venta, como efectivo o tarjeta.", aliases=["forma de pago"], related_metrics=["payment_mix"]),
    MetricConceptDefinition(term="cortesia", display_name="Cortesia", definition="Importe dispensado como cortesia; la metrica resta primero el permitido configurado por responsable.", aliases=["cortesia de personal"], related_metrics=["staff_courtesy_ratio"]),
    MetricConceptDefinition(term="redencion_de_lealtad", display_name="Redencion de lealtad", definition="Uso registrado de un beneficio o saldo del programa de lealtad.", aliases=["canje de puntos", "redencion"], related_metrics=["loyalty_redemption_cost"]),
    MetricConceptDefinition(term="precio_esperado", display_name="Precio esperado", definition="Precio de referencia derivado de la configuracion o receta disponible para contrastar una venta.", aliases=["precio configurado"], related_metrics=["price_consistency"]),
    MetricConceptDefinition(term="comision_delivery", display_name="Comision de delivery", definition="Costo estimado de una plataforma de entrega segun sus ventas y la tasa configurada.", aliases=["comision de plataforma"], related_metrics=["delivery_commission_cost", "commission_cost_ratio", "contribution_margin_by_channel"]),
    MetricConceptDefinition(term="cancelacion", display_name="Cancelacion", definition="Anulacion registrada de un ticket, con el momento y responsable disponibles.", aliases=["ticket cancelado"], related_metrics=["cancellation_rate"]),
    MetricConceptDefinition(term="reimpresion", display_name="Reimpresion", definition="Nueva impresion registrada de un comprobante o ticket.", aliases=["ticket reimpreso"], related_metrics=["reprint_rate"]),
    MetricConceptDefinition(term="turno", display_name="Turno", definition="Periodo operativo al que pueden atribuirse ventas, trabajo o cortes de caja.", aliases=["shift"], related_metrics=["ticket_volume", "shift_cash_variance"]),
    MetricConceptDefinition(term="costo_laboral", display_name="Costo laboral", definition="Costo estimado del personal a partir de los datos laborales disponibles para el motor.", aliases=["costo de personal"], related_metrics=["labor_cost_ratio"]),
    MetricConceptDefinition(term="horas_trabajadas", display_name="Horas trabajadas", definition="Tiempo laboral registrado que el motor usa en metricas de costo o productividad.", aliases=["horas laborales"], related_metrics=["labor_cost_ratio", "sales_per_labor_hour"]),
    MetricConceptDefinition(term="productividad_laboral", display_name="Productividad laboral de ventas", definition="Relacion observada entre ventas y horas trabajadas; no prueba por si sola eficiencia causal.", aliases=["ventas por hora"], related_metrics=["sales_per_labor_hour"]),
    MetricConceptDefinition(term="precio_de_compra", display_name="Precio de compra", definition="Precio historico registrado de un ingrediente que puede compararse en unidades compatibles.", aliases=["precio de insumo"], related_metrics=["price_inflation"]),
    MetricConceptDefinition(term="estado_metrica", display_name="Estado de metrica", definition="Clasificacion emitida por el motor: ok, warning, critical, incomplete_data o unit_mismatch.", aliases=["semaforo", "status de metrica"], related_metrics=[]),
    MetricConceptDefinition(term="datos_incompletos", display_name="Datos incompletos", definition="Estado que indica que el motor no conto con la informacion necesaria para producir un valor confiable.", aliases=["incomplete data"], related_metrics=[]),
    MetricConceptDefinition(term="unidades_incompatibles", display_name="Unidades incompatibles", definition="Estado que indica que el motor no pudo comparar o convertir cantidades con unidades incompatibles.", aliases=["unit mismatch"], related_metrics=[]),
)


PIPELINE_METRIC_IDS = frozenset(
    item.metric_id for item in METRIC_CATALOG if item.availability == "pipeline"
)
ENGINE_SUPPORT_METRIC_IDS = frozenset(
    item.metric_id for item in METRIC_CATALOG if item.availability == "engine_support"
)
