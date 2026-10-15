import OnboardingForm from "@/components/onboarding/OnboardingForm";

export default function OnboardingPage() {
  return (
    <div className="min-h-[calc(100dvh-4rem)] px-6 py-12">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-forensic-lg font-semibold text-zinc-100 mb-2 uppercase tracking-widest">
          MEPIA — CONFIGURACIÓN INICIAL
        </h1>
        <p className="text-sm text-muted mb-10">
          Define el lente de auditoría de tu negocio
        </p>
        <OnboardingForm />
      </div>
    </div>
  );
}
