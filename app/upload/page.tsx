import OnboardingGate from "@/components/upload/OnboardingGate";
import UploadForm from "@/components/upload/UploadForm";

export default function UploadPage() {
  return (
    <div className="min-h-[calc(100dvh-4rem)] px-6 py-12">
      <div className="max-w-3xl mx-auto">
        <OnboardingGate>
          <UploadForm />
        </OnboardingGate>
      </div>
    </div>
  );
}
