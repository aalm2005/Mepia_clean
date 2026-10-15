"use client";

import { Suspense } from "react";
import AuditReportView from "@/components/dashboard/AuditReportView";

export default function DashboardPage() {
  return (
    <Suspense fallback={<div className="text-muted text-sm p-10">Cargando...</div>}>
      <AuditReportView showMetrics />
    </Suspense>
  );
}
