import { Suspense } from "react";
import { MepiaLogin } from "@/components/auth/MepiaLogin";
export default function LoginPage() {
  return <Suspense fallback={<div className="grid min-h-dvh place-items-center text-zinc-400">Cargando…</div>}><MepiaLogin/></Suspense>;
}
