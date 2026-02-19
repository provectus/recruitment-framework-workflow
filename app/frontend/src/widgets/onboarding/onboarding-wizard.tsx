import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/shared/ui/dialog";
import { Progress } from "@/shared/ui/progress";
import type { WizardStep } from "@/features/onboarding";
import { WelcomeStep } from "./steps/welcome-step";
import { HowItWorksStep } from "./steps/how-it-works-step";
import { CreateTeamStep } from "./steps/create-team-step";
import { CreatePositionStep } from "./steps/create-position-step";
import { ReadyStep } from "./steps/ready-step";

interface OnboardingWizardProps {
  isOpen: boolean;
  currentStep: WizardStep;
  activeSteps: WizardStep[];
  progressPercent: number;
  goNext: () => void;
  goBack: () => void;
  complete: () => void;
  close: () => void;
}

export function OnboardingWizard({
  isOpen,
  currentStep,
  activeSteps,
  progressPercent,
  goNext,
  goBack,
  complete,
  close,
}: OnboardingWizardProps) {
  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && close()}>
      <DialogContent className="sm:max-w-md" showCloseButton={false}>
        <DialogHeader className="sr-only">
          <DialogTitle>Getting Started</DialogTitle>
          <DialogDescription>Onboarding wizard for new users</DialogDescription>
        </DialogHeader>
        <div className="space-y-1 mb-2">
          <Progress value={progressPercent} />
          <p className="text-xs text-muted-foreground text-right">
            {activeSteps.indexOf(currentStep) + 1} of {activeSteps.length}
          </p>
        </div>

        {currentStep === "welcome" && <WelcomeStep onNext={goNext} />}
        {currentStep === "how-it-works" && (
          <HowItWorksStep onNext={goNext} onBack={goBack} />
        )}
        {currentStep === "create-team" && (
          <CreateTeamStep onNext={goNext} onBack={goBack} />
        )}
        {currentStep === "create-position" && (
          <CreatePositionStep onNext={goNext} onBack={goBack} />
        )}
        {currentStep === "ready" && <ReadyStep onComplete={complete} />}
      </DialogContent>
    </Dialog>
  );
}
