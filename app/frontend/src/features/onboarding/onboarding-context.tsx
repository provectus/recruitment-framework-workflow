import { createContext, useContext } from "react";

interface OnboardingContextValue {
  openWizard: () => void;
}

export const OnboardingContext = createContext<OnboardingContextValue | null>(null);

export function useOpenOnboarding(): () => void {
  const ctx = useContext(OnboardingContext);
  if (!ctx) throw new Error("useOpenOnboarding must be used within OnboardingContext");
  return ctx.openWizard;
}
