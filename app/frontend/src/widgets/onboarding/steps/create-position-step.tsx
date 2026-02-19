import { useState } from "react";
import { Loader2 } from "lucide-react";
import { useCreatePosition, useUsers } from "@/features/positions";
import { useTeams } from "@/features/settings";
import { useAuth } from "@/features/auth";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/ui/select";

interface CreatePositionStepProps {
  onNext: () => void;
  onBack: () => void;
}

export function CreatePositionStep({ onNext, onBack }: CreatePositionStepProps) {
  const { user } = useAuth();
  const { data: teams } = useTeams();
  const { data: users } = useUsers();
  const createPosition = useCreatePosition();

  const [title, setTitle] = useState("");
  const [teamId, setTeamId] = useState<number | null>(null);
  const [hiringManagerId, setHiringManagerId] = useState<number | null>(
    user?.id ?? null
  );
  const [error, setError] = useState("");

  const handleCreate = () => {
    if (!title.trim()) {
      setError("Position title is required");
      return;
    }
    if (!teamId) {
      setError("Please select a team");
      return;
    }
    if (!hiringManagerId) {
      setError("Please select a hiring manager");
      return;
    }
    setError("");
    createPosition.mutate(
      {
        body: {
          title: title.trim(),
          team_id: teamId,
          hiring_manager_id: hiringManagerId,
        },
      },
      {
        onSuccess: () => onNext(),
        onError: () => setError("Failed to create position. Try again."),
      }
    );
  };

  const teamList = teams ?? [];
  const userList = users ?? [];

  return (
    <div className="flex flex-col space-y-6 py-4">
      <div className="text-center space-y-2">
        <h2 className="text-xl font-bold tracking-tight">Create your first position</h2>
        <p className="text-sm text-muted-foreground">
          Positions define what you're hiring for
        </p>
      </div>

      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="onboarding-position-title">Position title</Label>
          <Input
            id="onboarding-position-title"
            placeholder="e.g. Senior Frontend Engineer"
            value={title}
            onChange={(e) => {
              setTitle(e.target.value);
              setError("");
            }}
          />
        </div>

        <div className="space-y-2">
          <Label>Team</Label>
          {teamList.length > 0 ? (
            <Select
              value={teamId?.toString()}
              onValueChange={(v) => {
                setTeamId(parseInt(v, 10));
                setError("");
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select a team" />
              </SelectTrigger>
              <SelectContent>
                {teamList.map((team) => (
                  <SelectItem key={team.id} value={team.id.toString()}>
                    {team.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          ) : (
            <p className="text-sm text-muted-foreground">
              No teams yet — go back and create one first
            </p>
          )}
        </div>

        <div className="space-y-2">
          <Label>Hiring manager</Label>
          <Select
            value={hiringManagerId?.toString()}
            onValueChange={(v) => {
              setHiringManagerId(parseInt(v, 10));
              setError("");
            }}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select hiring manager" />
            </SelectTrigger>
            <SelectContent>
              {userList.map((u) => (
                <SelectItem key={u.id} value={u.id.toString()}>
                  {u.full_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {error && <p className="text-sm text-destructive">{error}</p>}
      </div>

      <div className="flex gap-2">
        <Button variant="outline" onClick={onBack} className="flex-1">
          Back
        </Button>
        <Button variant="outline" onClick={onNext} className="flex-1">
          Skip
        </Button>
        <Button
          onClick={handleCreate}
          disabled={createPosition.isPending}
          className="flex-1"
        >
          {createPosition.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
          Create & continue
        </Button>
      </div>
    </div>
  );
}
