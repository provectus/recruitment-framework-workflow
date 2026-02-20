import { useState, useCallback, useMemo } from "react";
import { useTeams } from "@/features/settings";
import { usePositions } from "@/features/positions";

const STORAGE_KEY = "lauter-onboarding-completed";

export type WizardStep = "welcome" | "how-it-works" | "create-team" | "create-position" | "ready";

const ALL_STEPS: WizardStep[] = [
  "welcome",
  "how-it-works",
  "create-team",
  "create-position",
  "ready",
];

function isOnboardingCompleted(): boolean {
  try {
    return localStorage.getItem(STORAGE_KEY) === "true";
  } catch {
    return false;
  }
}

function markOnboardingCompleted(): void {
  try {
    localStorage.setItem(STORAGE_KEY, "true");
  } catch {
    /* empty */
  }
}

export function useOnboardingWizard() {
  const [isOpen, setIsOpen] = useState(() => !isOnboardingCompleted());
  const [currentStep, setCurrentStep] = useState<WizardStep>("welcome");

  const { data: teams } = useTeams();
  const { data: positions } = usePositions({ limit: 1 });

  const hasTeams = (teams ?? []).length > 0;
  const hasPositions = (positions?.items ?? []).length > 0;

  const activeSteps = useMemo(() => {
    return ALL_STEPS.filter((step) => {
      if (step === "create-team" && hasTeams) return false;
      if (step === "create-position" && hasPositions) return false;
      return true;
    });
  }, [hasTeams, hasPositions]);

  const validStep = activeSteps.includes(currentStep)
    ? currentStep
    : activeSteps[0];

  if (validStep !== currentStep) {
    setCurrentStep(validStep);
  }

  const currentIndex = activeSteps.indexOf(validStep);
  const progressPercent = ((currentIndex + 1) / activeSteps.length) * 100;

  const goNext = useCallback(() => {
    const nextIndex = currentIndex + 1;
    if (nextIndex < activeSteps.length) {
      setCurrentStep(activeSteps[nextIndex]);
    }
  }, [currentIndex, activeSteps]);

  const goBack = useCallback(() => {
    const prevIndex = currentIndex - 1;
    if (prevIndex >= 0) {
      setCurrentStep(activeSteps[prevIndex]);
    }
  }, [currentIndex, activeSteps]);

  const complete = useCallback(() => {
    markOnboardingCompleted();
    setIsOpen(false);
    setCurrentStep("welcome");
  }, []);

  const open = useCallback(() => {
    setCurrentStep("welcome");
    setIsOpen(true);
  }, []);

  const close = useCallback(() => {
    setIsOpen(false);
    setCurrentStep("welcome");
  }, []);

  return {
    isOpen,
    currentStep: validStep,
    activeSteps,
    progressPercent,
    isFirstStep: currentIndex === 0,
    isLastStep: currentIndex === activeSteps.length - 1,
    goNext,
    goBack,
    complete,
    open,
    close,
  };
}
