"""
S2 — Gatekeeper Agent
Valida que cada métrica tenga su set de datos completo antes de pasar a S3.
Spec: .kiro/specs/mepia/s2_gatekeeper.md
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Modelos de salida
# ---------------------------------------------------------------------------

class DormantMetric(BaseModel):
    metric: str
    missing: list[str]


class BlockedMetric(BaseModel):
    metric: str
    reason: str  # siempre "needs_human_review"


class GatekeeperResult(BaseModel):
    business_id: str
    date: str  # YYYY-MM-DD
    active_metrics: list[str]
    dormant_metrics: list[DormantMetric]
    blocked_metrics: list[BlockedMetric]


# ---------------------------------------------------------------------------
# Agente
# ---------------------------------------------------------------------------

class GatekeeperAgent:
    """
    Evalúa el catálogo de métricas para un business_id + date y persiste
    los resultados en metric_status.

    Recibe el cliente Supabase en el constructor (inyección de dependencias).
    Todas las consultas son síncronas.
    """

    METRICS = [
        "cash_reconciliation",
        "daily_break_even",
        "operative_cost_margin",
        "health_score",
        "inventory_variance",
        # --- 25 métricas nuevas de S3 (sesión de extensión, ver
        #     mepia_v4_metricas_diseno.md) -- agrupadas por requisito de datos
        #     compartido en 9 clusters, no una por una ---
        # Cluster A: transactions
        "avg_ticket", "channel_mix", "discount_rate",
        "hourly_sales_pattern", "sales_by_staff", "sales_by_branch",
        "top_bottom_sellers", "revenue_concentration", "category_mix",
        "modifier_attach_rate", "item_discount_split", "payment_mix",
        "staff_courtesy_ratio", "loyalty_redemption_cost",
        # Cluster B: transactions + recipes
        "price_consistency",
        # Cluster C: transactions + delivery_platform_config
        "delivery_commission_cost", "commission_cost_ratio",
        # Cluster D: transactions + recipes + delivery_platform_config
        "contribution_margin_by_channel",
        # Cluster E: transactions + shift_audit_events
        "ticket_volume",
        # Cluster E2: transactions + shift_audit_events + pos_inputs
        "cancellation_rate", "reprint_rate",
        # Cluster F: shift_audit_events
        "shift_cash_variance",
        # Cluster G: shift_audit_events + pos_inputs + business_fixed_costs
        "labor_cost_ratio",
        # Cluster H: shift_audit_events + pos_inputs
        "sales_per_labor_hour",
        # Cluster I: inventory_daily
        "waste_cost", "stock_days_remaining",
    ]

    def __init__(self, supabase_client: Any) -> None:
        self._db = supabase_client

    # ------------------------------------------------------------------
    # Punto de entrada principal
    # ------------------------------------------------------------------

    def evaluate(self, business_id: str, date: str) -> GatekeeperResult:
        """
        Evalúa todas las métricas para business_id + date.
        Escribe resultados en metric_status (upsert).
        Retorna GatekeeperResult.
        Nunca lanza excepciones — errores de DB se marcan como dormant.
        """
        # Resultados intermedios: metric_name → ("active"|"dormant"|"blocked", missing_list)
        results: dict[str, tuple[str, list[str]]] = {}

        # Evaluar en orden (health_score depende de las 3 anteriores)
        results["cash_reconciliation"] = self._eval_cash_reconciliation(business_id, date)
        results["daily_break_even"] = self._eval_daily_break_even(business_id, date)
        results["operative_cost_margin"] = self._eval_operative_cost_margin(business_id, date)
        results["health_score"] = self._eval_health_score(results)
        results["inventory_variance"] = self._eval_inventory_variance(business_id, date)

        # --- 25 métricas nuevas, por cluster (mismo resultado de cluster
        #     aplicado a todas las métricas que comparten ese requisito) ---
        cluster_a = self._eval_transactions_only(business_id, date)
        for m in (
            "avg_ticket", "channel_mix", "discount_rate", "hourly_sales_pattern",
            "sales_by_staff", "sales_by_branch", "top_bottom_sellers",
            "revenue_concentration", "category_mix", "modifier_attach_rate",
            "item_discount_split", "payment_mix", "staff_courtesy_ratio",
            "loyalty_redemption_cost",
        ):
            results[m] = cluster_a

        results["price_consistency"] = self._eval_transactions_and_recipes(business_id, date)

        cluster_c = self._eval_transactions_and_delivery_config(business_id, date)
        for m in ("delivery_commission_cost", "commission_cost_ratio"):
            results[m] = cluster_c

        results["contribution_margin_by_channel"] = (
            self._eval_contribution_margin_by_channel(business_id, date)
        )

        results["ticket_volume"] = self._eval_ticket_volume(business_id, date)

        cluster_e2 = self._eval_cancellation_reprint(business_id, date)
        for m in ("cancellation_rate", "reprint_rate"):
            results[m] = cluster_e2

        results["shift_cash_variance"] = self._eval_shift_cash_variance(business_id, date)
        results["labor_cost_ratio"] = self._eval_labor_cost_ratio(business_id, date)
        results["sales_per_labor_hour"] = self._eval_sales_per_labor_hour(business_id, date)

        cluster_i = self._eval_inventory_metrics(business_id, date)
        for m in ("waste_cost", "stock_days_remaining"):
            results[m] = cluster_i

        # Persistir en metric_status
        now_iso = datetime.now(timezone.utc).isoformat()
        for metric_name, (status, missing_list) in results.items():
            self._upsert_metric_status(
                business_id=business_id,
                date=date,
                metric_name=metric_name,
                status=status,
                missing_fields=missing_list,
                now_iso=now_iso,
            )

        return self._build_result(business_id, date, results)

    # ------------------------------------------------------------------
    # Método auxiliar de lectura
    # ------------------------------------------------------------------

    def get_status(self, business_id: str, date: str) -> GatekeeperResult:
        """Lee el estado actual desde metric_status sin re-evaluar."""
        try:
            rows = (
                self._db.table("metric_status")
                .select("*")
                .eq("business_id", business_id)
                .eq("date", date)
                .execute()
            )
        except Exception:
            # Si falla la lectura, retornar resultado vacío
            return GatekeeperResult(
                business_id=business_id,
                date=date,
                active_metrics=[],
                dormant_metrics=[],
                blocked_metrics=[],
            )

        results: dict[str, tuple[str, list[str]]] = {}
        for row in rows.data or []:
            metric_name = row["metric_name"]
            status = row["status"]
            missing_fields = row.get("missing_fields") or []
            results[metric_name] = (status, missing_fields)

        return self._build_result(business_id, date, results)

    # ------------------------------------------------------------------
    # Evaluadores por métrica
    # ------------------------------------------------------------------

    def _eval_cash_reconciliation(
        self, business_id: str, date: str
    ) -> tuple[str, list[str]]:
        """
        Requiere: pos_inputs del día + cash_counts del día,
        ambos sin documentos con needs_human_review=true.
        """
        try:
            pos = (
                self._db.table("pos_inputs")
                .select("id")
                .eq("business_id", business_id)
                .eq("date", date)
                .execute()
            )
            cash = (
                self._db.table("cash_counts")
                .select("id")
                .eq("business_id", business_id)
                .eq("date", date)
                .execute()
            )
            docs_review = (
                self._db.table("documents")
                .select("id")
                .eq("business_id", business_id)
                .eq("needs_human_review", True)
                .execute()
            )
        except Exception:
            return ("dormant", ["db_error"])

        has_pos = bool(pos.data)
        has_cash = bool(cash.data)
        has_review_docs = bool(docs_review.data)

        if has_review_docs:
            return ("blocked", [])

        missing: list[str] = []
        if not has_pos:
            missing.append("pos_inputs")
        if not has_cash:
            missing.append("cash_count")

        if missing:
            return ("dormant", missing)

        return ("active", [])

    def _eval_daily_break_even(
        self, business_id: str, date: str
    ) -> tuple[str, list[str]]:
        """
        Requiere: al menos 1 transaction del día con expense_behavior='FIXED' confirmado.
        """
        try:
            result = (
                self._db.table("transactions")
                .select("id")
                .eq("business_id", business_id)
                .eq("transaction_date", date)
                .eq("expense_behavior", "FIXED")
                .execute()
            )
        except Exception:
            return ("dormant", ["db_error"])

        if not result.data:
            return ("dormant", ["expense_behavior_confirmed"])

        return ("active", [])

    def _eval_operative_cost_margin(
        self, business_id: str, date: str
    ) -> tuple[str, list[str]]:
        """
        Requiere: al menos 1 transaction del día con expense_behavior IS NOT NULL.
        """
        try:
            result = (
                self._db.table("transactions")
                .select("id")
                .eq("business_id", business_id)
                .eq("transaction_date", date)
                .not_.is_("expense_behavior", "null")
                .execute()
            )
        except Exception:
            return ("dormant", ["db_error"])

        if not result.data:
            return ("dormant", ["expense_behavior_confirmed"])

        return ("active", [])

    def _eval_health_score(
        self,
        results: dict[str, tuple[str, list[str]]],
    ) -> tuple[str, list[str]]:
        """
        Requiere: cash_reconciliation, daily_break_even y operative_cost_margin en active.
        """
        dependencies = ["cash_reconciliation", "daily_break_even", "operative_cost_margin"]

        blocked_deps = [
            dep for dep in dependencies
            if results.get(dep, ("dormant", []))[0] == "blocked"
        ]
        if blocked_deps:
            return ("blocked", [])

        not_active = [
            dep for dep in dependencies
            if results.get(dep, ("dormant", []))[0] != "active"
        ]
        if not_active:
            return ("dormant", not_active)

        return ("active", [])

    def _eval_inventory_variance(
        self, business_id: str, date: str
    ) -> tuple[str, list[str]]:
        """
        Requiere: al menos 1 receta en recipes + pos_inputs del día.
        """
        try:
            recipes = (
                self._db.table("recipes")
                .select("id")
                .eq("business_id", business_id)
                .execute()
            )
            pos = (
                self._db.table("pos_inputs")
                .select("id")
                .eq("business_id", business_id)
                .eq("date", date)
                .execute()
            )
        except Exception:
            return ("dormant", ["db_error"])

        missing: list[str] = []
        if not recipes.data:
            missing.append("recipes")
        if not pos.data:
            missing.append("pos_inputs")

        if missing:
            return ("dormant", missing)

        return ("active", [])

    # ------------------------------------------------------------------
    # Clusters de las 25 métricas nuevas de S3
    # Un metodo por requisito de datos compartido, no uno por metrica --
    # ver mepia_v4_metricas_diseno.md para el mapeo completo de que
    # metrica cae en que cluster.
    # ------------------------------------------------------------------

    def _eval_transactions_only(
        self, business_id: str, date: str
    ) -> tuple[str, list[str]]:
        """Cluster A: requiere >=1 transaccion de venta ese dia."""
        try:
            result = (
                self._db.table("transactions")
                .select("id")
                .eq("business_id", business_id)
                .eq("transaction_date", date)
                .eq("type", "ingreso")
                .eq("category", "venta")
                .execute()
            )
        except Exception:
            return ("dormant", ["db_error"])
        if not result.data:
            return ("dormant", ["transactions"])
        return ("active", [])

    def _eval_transactions_and_recipes(
        self, business_id: str, date: str
    ) -> tuple[str, list[str]]:
        """Cluster B: transacciones + al menos 1 receta del negocio."""
        status, missing = self._eval_transactions_only(business_id, date)
        if status != "active":
            return (status, missing)
        try:
            recipes = (
                self._db.table("recipes")
                .select("id")
                .eq("business_id", business_id)
                .execute()
            )
        except Exception:
            return ("dormant", ["db_error"])
        if not recipes.data:
            return ("dormant", ["recipes"])
        return ("active", [])

    def _eval_transactions_and_delivery_config(
        self, business_id: str, date: str
    ) -> tuple[str, list[str]]:
        """Cluster C: transacciones + delivery_platform_config del negocio."""
        status, missing = self._eval_transactions_only(business_id, date)
        if status != "active":
            return (status, missing)
        try:
            config = (
                self._db.table("delivery_platform_config")
                .select("id")
                .eq("business_id", business_id)
                .execute()
            )
        except Exception:
            return ("dormant", ["db_error"])
        if not config.data:
            return ("dormant", ["delivery_platform_config"])
        return ("active", [])

    def _eval_contribution_margin_by_channel(
        self, business_id: str, date: str
    ) -> tuple[str, list[str]]:
        """Cluster D: transacciones + recipes + delivery_platform_config."""
        status, missing = self._eval_transactions_and_recipes(business_id, date)
        if status != "active":
            return (status, missing)
        try:
            config = (
                self._db.table("delivery_platform_config")
                .select("id")
                .eq("business_id", business_id)
                .execute()
            )
        except Exception:
            return ("dormant", ["db_error"])
        if not config.data:
            return ("dormant", ["delivery_platform_config"])
        return ("active", [])

    def _eval_ticket_volume(
        self, business_id: str, date: str
    ) -> tuple[str, list[str]]:
        """Cluster E: transacciones + shift_audit_events."""
        status, missing = self._eval_transactions_only(business_id, date)
        if status != "active":
            return (status, missing)
        try:
            shifts = (
                self._db.table("shift_audit_events")
                .select("id")
                .eq("business_id", business_id)
                .eq("date", date)
                .execute()
            )
        except Exception:
            return ("dormant", ["db_error"])
        if not shifts.data:
            return ("dormant", ["shift_audit_events"])
        return ("active", [])

    def _eval_cancellation_reprint(
        self, business_id: str, date: str
    ) -> tuple[str, list[str]]:
        """Cluster E2: transacciones + shift_audit_events + pos_inputs."""
        status, missing = self._eval_ticket_volume(business_id, date)
        if status != "active":
            return (status, missing)
        try:
            pos = (
                self._db.table("pos_inputs")
                .select("id")
                .eq("business_id", business_id)
                .eq("date", date)
                .execute()
            )
        except Exception:
            return ("dormant", ["db_error"])
        if not pos.data:
            return ("dormant", ["pos_inputs"])
        return ("active", [])

    def _eval_shift_cash_variance(
        self, business_id: str, date: str
    ) -> tuple[str, list[str]]:
        """Cluster F: solo shift_audit_events."""
        try:
            shifts = (
                self._db.table("shift_audit_events")
                .select("id")
                .eq("business_id", business_id)
                .eq("date", date)
                .execute()
            )
        except Exception:
            return ("dormant", ["db_error"])
        if not shifts.data:
            return ("dormant", ["shift_audit_events"])
        return ("active", [])

    def _eval_labor_cost_ratio(
        self, business_id: str, date: str
    ) -> tuple[str, list[str]]:
        """Cluster G: shift_audit_events + pos_inputs + business_fixed_costs
        (con al menos un concepto de nomina configurado)."""
        status, missing = self._eval_shift_cash_variance(business_id, date)
        if status != "active":
            return (status, missing)
        try:
            pos = (
                self._db.table("pos_inputs")
                .select("id")
                .eq("business_id", business_id)
                .eq("date", date)
                .execute()
            )
            nomina = (
                self._db.table("business_fixed_costs")
                .select("id")
                .eq("business_id", business_id)
                .ilike("concept", "%nómina%")
                .execute()
            )
        except Exception:
            return ("dormant", ["db_error"])
        missing_fields: list[str] = []
        if not pos.data:
            missing_fields.append("pos_inputs")
        if not nomina.data:
            missing_fields.append("business_fixed_costs_nomina")
        if missing_fields:
            return ("dormant", missing_fields)
        return ("active", [])

    def _eval_sales_per_labor_hour(
        self, business_id: str, date: str
    ) -> tuple[str, list[str]]:
        """Cluster H: shift_audit_events + pos_inputs (sin requerir nomina)."""
        status, missing = self._eval_shift_cash_variance(business_id, date)
        if status != "active":
            return (status, missing)
        try:
            pos = (
                self._db.table("pos_inputs")
                .select("id")
                .eq("business_id", business_id)
                .eq("date", date)
                .execute()
            )
        except Exception:
            return ("dormant", ["db_error"])
        if not pos.data:
            return ("dormant", ["pos_inputs"])
        return ("active", [])

    def _eval_inventory_metrics(
        self, business_id: str, date: str
    ) -> tuple[str, list[str]]:
        """Cluster I: inventory_daily (waste_cost, stock_days_remaining)."""
        try:
            inv = (
                self._db.table("inventory_daily")
                .select("id")
                .eq("business_id", business_id)
                .eq("date", date)
                .execute()
            )
        except Exception:
            return ("dormant", ["db_error"])
        if not inv.data:
            return ("dormant", ["inventory_daily"])
        return ("active", [])

    # ------------------------------------------------------------------
    # Persistencia
    # ------------------------------------------------------------------

    def _upsert_metric_status(
        self,
        business_id: str,
        date: str,
        metric_name: str,
        status: str,
        missing_fields: list[str],
        now_iso: str,
    ) -> None:
        """
        Upsert en metric_status.
        Usa on_conflict si el unique constraint existe; fallback a delete+insert.
        """
        row = {
            "business_id": business_id,
            "date": date,
            "metric_name": metric_name,
            "status": status,
            "missing_fields": missing_fields,
            "updated_at": now_iso,
        }
        try:
            self._db.table("metric_status").upsert(
                row,
                on_conflict="business_id,date,metric_name",
            ).execute()
        except Exception:
            # Fallback: delete + insert
            try:
                self._db.table("metric_status").delete().eq(
                    "business_id", business_id
                ).eq("date", date).eq("metric_name", metric_name).execute()
                self._db.table("metric_status").insert(row).execute()
            except Exception:
                # Si el fallback también falla, continuar sin persistir
                pass

    # ------------------------------------------------------------------
    # Constructor de resultado
    # ------------------------------------------------------------------

    @staticmethod
    def _build_result(
        business_id: str,
        date: str,
        results: dict[str, tuple[str, list[str]]],
    ) -> GatekeeperResult:
        active: list[str] = []
        dormant: list[DormantMetric] = []
        blocked: list[BlockedMetric] = []

        for metric_name, (status, missing_list) in results.items():
            if status == "active":
                active.append(metric_name)
            elif status == "dormant":
                dormant.append(DormantMetric(metric=metric_name, missing=missing_list))
            elif status == "blocked":
                blocked.append(BlockedMetric(metric=metric_name, reason="needs_human_review"))

        return GatekeeperResult(
            business_id=business_id,
            date=date,
            active_metrics=active,
            dormant_metrics=dormant,
            blocked_metrics=blocked,
        )