import OnboardingForm from "@/components/onboarding/OnboardingForm";
import Link from "next/link";

export default function OnboardingPage() {
  return (
    <div className="min-h-[calc(100dvh-4rem)] px-6 py-12">
      <div className="max-w-2xl mx-auto" data-tour="advanced-config">
        <h1 className="text-forensic-lg font-semibold text-zinc-100 mb-2 uppercase tracking-widest">
          MEPIA — AJUSTES AVANZADOS
        </h1>
        <p className="text-sm text-muted mb-3">
          Los valores actuales son defaults recomendados para que puedas empezar sin configurar nada.
        </p>
        <p className="text-sm text-muted mb-6">
          Estos parámetros avanzados se pueden ajustar cuando te familiarices con los conceptos de la plataforma.
        </p>
        <Link href="/upload" className="mb-8 inline-block text-sm text-accent hover:opacity-80">
          ← Volver a subir documentos
        </Link>
        <OnboardingForm />
      </div>
    </div>
  );
}
