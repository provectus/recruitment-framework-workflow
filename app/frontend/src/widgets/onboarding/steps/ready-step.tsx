import { useNavigate } from "@tanstack/react-router";
import { CheckCircle2 } from "lucide-react";
import { Button } from "@/shared/ui/button";

interface ReadyStepProps {
  onComplete: () => void;
}

export function ReadyStep({ onComplete }: ReadyStepProps) {
  const navigate = useNavigate();

  const handleGoToDashboard = () => {
    onComplete();
    navigate({ to: "/dashboard" });
  };

  const handleAddCandidate = () => {
    onComplete();
    navigate({ to: "/candidates" });
  };

  return (
    <div className="flex flex-col items-center text-center space-y-6 py-4">
      <div className="rounded-full bg-green-500/10 p-4">
        <CheckCircle2 className="h-8 w-8 text-green-500" />
      </div>

      <div className="space-y-2">
        <h2 className="text-xl font-bold tracking-tight">You're all set!</h2>
        <p className="text-sm text-muted-foreground">
          You can always re-open this guide from the help button in the sidebar
        </p>
      </div>

      <div className="w-full space-y-2">
        <Button onClick={handleAddCandidate} className="w-full">
          Add your first candidate
        </Button>
        <Button variant="outline" onClick={handleGoToDashboard} className="w-full">
          Go to Dashboard
        </Button>
      </div>
    </div>
  );
}
