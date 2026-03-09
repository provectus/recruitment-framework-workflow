import { useState } from "react";
import { Loader2 } from "lucide-react";
import { useCreateTeam } from "@/features/settings";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";

interface CreateTeamStepProps {
  onNext: () => void;
  onBack: () => void;
}

export function CreateTeamStep({ onNext, onBack }: CreateTeamStepProps) {
  const [teamName, setTeamName] = useState("");
  const [error, setError] = useState("");
  const createTeam = useCreateTeam();

  const handleCreate = () => {
    const trimmed = teamName.trim();
    if (!trimmed) {
      setError("Team name is required");
      return;
    }
    setError("");
    createTeam.mutate(
      { body: { name: trimmed } },
      {
        onSuccess: () => onNext(),
        onError: () => setError("Failed to create team. Try again."),
      }
    );
  };

  return (
    <div className="flex flex-col space-y-6 py-4">
      <div className="text-center space-y-2">
        <h2 className="text-xl font-bold tracking-tight">Create your first team</h2>
        <p className="text-sm text-muted-foreground">
          Teams organize positions and hiring managers
        </p>
      </div>

      <div className="space-y-2">
        <Label htmlFor="onboarding-team-name">Team name</Label>
        <Input
          id="onboarding-team-name"
          placeholder="e.g. Engineering, Design, Product"
          value={teamName}
          onChange={(e) => {
            setTeamName(e.target.value);
            setError("");
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleCreate();
          }}
        />
        {error && <p className="text-sm text-destructive">{error}</p>}
      </div>

      <div className="flex gap-2">
        <Button variant="outline" onClick={onBack} className="flex-1">
          Back
        </Button>
        <Button
          variant="outline"
          onClick={onNext}
          className="flex-1"
        >
          Skip
        </Button>
        <Button
          onClick={handleCreate}
          disabled={createTeam.isPending}
          className="flex-1"
        >
          {createTeam.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
          Create & continue
        </Button>
      </div>
    </div>
  );
}
