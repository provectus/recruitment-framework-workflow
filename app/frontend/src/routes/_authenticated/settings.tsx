import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Loader2, Plus, Trash2 } from "lucide-react";
import type { AxiosError } from "axios";
import { useTeams, useCreateTeam, useDeleteTeam } from "@/features/settings";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { Separator } from "@/shared/ui/separator";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/shared/ui/dialog";
import { Alert } from "@/shared/ui/alert";

export const Route = createFileRoute("/_authenticated/settings")({
  component: SettingsPage,
});

function SettingsPage() {
  const { data, isLoading } = useTeams();
  const teams = data ?? [];
  const createTeam = useCreateTeam();
  const deleteTeam = useDeleteTeam();

  const [teamName, setTeamName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [teamToDelete, setTeamToDelete] = useState<{
    id: number;
    name: string;
  } | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const handleAddTeam = (e: React.FormEvent) => {
    e.preventDefault();
    if (!teamName.trim()) return;

    createTeam.mutate(
      { body: { name: teamName.trim() } },
      {
        onSuccess: () => {
          setTeamName("");
          setError(null);
        },
        onError: (err) => {
          const axiosError = err as AxiosError;
          if (axiosError.response?.status === 409) {
            setError("A team with this name already exists.");
          } else {
            setError("Failed to create team. Please try again.");
          }
        },
      }
    );
  };

  const handleDeleteTeam = () => {
    if (!teamToDelete) return;

    deleteTeam.mutate(
      { path: { team_id: teamToDelete.id } },
      {
        onSuccess: () => {
          setTeamToDelete(null);
          setDeleteError(null);
        },
        onError: (err) => {
          const axiosError = err as AxiosError;
          if (axiosError.response?.status === 409) {
            setDeleteError(
              "This team is assigned to positions and cannot be removed."
            );
          } else {
            setDeleteError("Failed to delete team. Please try again.");
          }
          setTeamToDelete(null);
        },
      }
    );
  };

  return (
    <div className="p-6 max-w-4xl">
      <h1 className="text-2xl font-semibold">Settings</h1>

      <Separator className="my-6" />

      <section>
        <h2 className="text-lg font-semibold mb-4">Teams</h2>

        <form onSubmit={handleAddTeam} className="flex gap-2 mb-6">
          <div className="flex-1">
            <Label htmlFor="team-name" className="sr-only">
              Team name
            </Label>
            <Input
              id="team-name"
              placeholder="Enter team name"
              value={teamName}
              onChange={(e) => {
                setTeamName(e.target.value);
                setError(null);
              }}
              disabled={createTeam.isPending}
            />
          </div>
          <Button
            type="submit"
            disabled={!teamName.trim() || createTeam.isPending}
          >
            {createTeam.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Plus className="h-4 w-4" />
            )}
            Add
          </Button>
        </form>

        {error && (
          <Alert variant="destructive" className="mb-4">
            {error}
          </Alert>
        )}

        {deleteError && (
          <Alert variant="destructive" className="mb-4">
            {deleteError}
          </Alert>
        )}

        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : teams.length > 0 ? (
          <div className="space-y-2">
            {teams.map((team) => (
              <div
                key={team.id}
                className="flex items-center justify-between p-3 border rounded-lg"
              >
                <span className="font-medium">{team.name}</span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() =>
                    setTeamToDelete({ id: team.id, name: team.name })
                  }
                >
                  <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-muted-foreground text-sm">No teams yet.</p>
        )}
      </section>

      <Dialog open={!!teamToDelete} onOpenChange={() => setTeamToDelete(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Remove team</DialogTitle>
            <DialogDescription>
              Are you sure you want to remove the team "{teamToDelete?.name}"?
              This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setTeamToDelete(null)}
              disabled={deleteTeam.isPending}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeleteTeam}
              disabled={deleteTeam.isPending}
            >
              {deleteTeam.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : null}
              Remove
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
