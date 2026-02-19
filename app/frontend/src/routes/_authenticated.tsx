import { createFileRoute, Outlet, redirect } from "@tanstack/react-router";
import { Sidebar } from "@/widgets/sidebar";
import { useOnboardingWizard, OnboardingContext } from "@/features/onboarding";
import { OnboardingWizard } from "@/widgets/onboarding";

export const Route = createFileRoute("/_authenticated")({
  beforeLoad: ({ context, location }) => {
    if (context.auth.isLoading) return;
    if (!context.auth.isAuthenticated) {
      throw redirect({
        to: "/login",
        search: { redirect: location.href, error: undefined },
      });
    }
  },
  component: AuthenticatedLayout,
});

function AuthenticatedLayout() {
  const wizard = useOnboardingWizard();

  return (
    <OnboardingContext value={{ openWizard: wizard.open }}>
      <div className="flex h-[calc(100vh-49px)]">
        <Sidebar />
        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </div>
      <OnboardingWizard
        isOpen={wizard.isOpen}
        currentStep={wizard.currentStep}
        activeSteps={wizard.activeSteps}
        progressPercent={wizard.progressPercent}
        goNext={wizard.goNext}
        goBack={wizard.goBack}
        complete={wizard.complete}
        close={wizard.close}
      />
    </OnboardingContext>
  );
}
