import { Sparkles, ArrowRight, FileSearch, Scale } from "lucide-react";
import { Button } from "@/shared/ui/button";

interface WelcomeStepProps {
  onNext: () => void;
}

const VALUE_POINTS = [
  {
    icon: FileSearch,
    title: "Automate candidate evaluation",
    description: "AI analyzes CVs and transcripts against your rubrics",
  },
  {
    icon: ArrowRight,
    title: "Connect your hiring pipeline",
    description: "From CV upload to hiring decision in one place",
  },
  {
    icon: Scale,
    title: "Consistent decisions across teams",
    description: "Rubric-based assessments ensure fair, structured evaluation",
  },
] as const;

export function WelcomeStep({ onNext }: WelcomeStepProps) {
  return (
    <div className="flex flex-col items-center text-center space-y-6 py-4">
      <div className="rounded-full bg-primary/10 p-4">
        <Sparkles className="h-8 w-8 text-primary" />
      </div>

      <div className="space-y-2">
        <h2 className="text-2xl font-bold tracking-tight">Welcome to Lauter</h2>
        <p className="text-muted-foreground">
          Recruitment workflow automation for Provectus
        </p>
      </div>

      <div className="w-full space-y-4 text-left">
        {VALUE_POINTS.map((point) => (
          <div key={point.title} className="flex gap-3 items-start">
            <div className="rounded-lg bg-muted p-2 shrink-0">
              <point.icon className="h-5 w-5 text-muted-foreground" />
            </div>
            <div>
              <p className="font-medium text-sm">{point.title}</p>
              <p className="text-sm text-muted-foreground">{point.description}</p>
            </div>
          </div>
        ))}
      </div>

      <Button onClick={onNext} className="w-full">
        Let's get started
      </Button>
    </div>
  );
}
