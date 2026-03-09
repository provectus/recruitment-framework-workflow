import { Briefcase, Users, FileUp, Brain, ArrowDown } from "lucide-react";
import { Button } from "@/shared/ui/button";

interface HowItWorksStepProps {
  onNext: () => void;
  onBack: () => void;
}

const WORKFLOW_STEPS = [
  {
    icon: Briefcase,
    label: "Create a Position",
    description: "Define what you're hiring for",
  },
  {
    icon: Users,
    label: "Add Candidates",
    description: "Link candidates to open positions",
  },
  {
    icon: FileUp,
    label: "Upload Documents",
    description: "Attach CVs and interview transcripts",
  },
  {
    icon: Brain,
    label: "AI Evaluates",
    description: "Get rubric-based assessments automatically",
  },
] as const;

export function HowItWorksStep({ onNext, onBack }: HowItWorksStepProps) {
  return (
    <div className="flex flex-col space-y-6 py-4">
      <div className="text-center space-y-2">
        <h2 className="text-xl font-bold tracking-tight">How Lauter works</h2>
        <p className="text-sm text-muted-foreground">
          Four steps from candidate to decision
        </p>
      </div>

      <div className="space-y-2">
        {WORKFLOW_STEPS.map((step, index) => (
          <div key={step.label}>
            <div className="flex items-center gap-3 rounded-lg border border-border p-3">
              <div className="rounded-lg bg-primary/10 p-2 shrink-0">
                <step.icon className="h-5 w-5 text-primary" />
              </div>
              <div className="flex-1">
                <p className="font-medium text-sm">{step.label}</p>
                <p className="text-xs text-muted-foreground">{step.description}</p>
              </div>
              <span className="text-xs font-medium text-muted-foreground/60">
                {index + 1}
              </span>
            </div>
            {index < WORKFLOW_STEPS.length - 1 && (
              <div className="flex justify-center py-1">
                <ArrowDown className="h-3 w-3 text-muted-foreground/40" />
              </div>
            )}
          </div>
        ))}
      </div>

      <p className="text-xs text-muted-foreground text-center italic">
        Hiring managers: you'll review AI-generated evaluations for your positions
      </p>

      <div className="flex gap-2">
        <Button variant="outline" onClick={onBack} className="flex-1">
          Back
        </Button>
        <Button onClick={onNext} className="flex-1">
          Continue
        </Button>
      </div>
    </div>
  );
}
