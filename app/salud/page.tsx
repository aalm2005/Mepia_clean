"use client";
import {Suspense} from "react";
import AuditReportView from "@/components/dashboard/AuditReportView";
export default function SaludPage() {
  return <Suspense fallback={<p className="p-10 text-sm text-zinc-400">Cargando…</p>}><AuditReportView showMetrics health/></Suspense>;
}
