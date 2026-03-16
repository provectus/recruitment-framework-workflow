import { createFileRoute, Outlet, redirect, useNavigate } from "@tanstack/react-router";
import { useEffect } from "react";
import { useAuth } from "@/features/auth";
import { Sidebar } from "@/widgets/sidebar";
import { useOnboardingWizard, OnboardingContext } from "@/features/onboarding";
import { OnboardingWizard } from "@/widgets/onboarding";

export const Route = createFileRoute("/_authenticated")({
  beforeLoad: ({ context, location }) => {
    if (!context.auth.isLoading && !context.auth.isAuthenticated) {
      throw redirect({
        to: "/login",
        search: { redirect: location.href, error: undefined },
      });
    }
  },
  component: AuthenticatedLayout,
});

function AuthenticatedLayout() {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const wizard = useOnboardingWizard();

  useEffect(() => {
    if (!isAuthenticated) {
      navigate({ to: "/login", search: { redirect: undefined, error: undefined } });
    }
  }, [isAuthenticated, navigate]);

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
