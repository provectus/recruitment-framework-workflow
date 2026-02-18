import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { Loader2, Archive } from "lucide-react";
import { usePosition, useArchivePosition } from "@/features/positions";
import { Button } from "@/shared/ui/button";
import { Badge } from "@/shared/ui/badge";
import { Card, CardContent } from "@/shared/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/shared/ui/dialog";
import { Skeleton } from "@/shared/ui/skeleton";
import { getStatusVariant, formatStatus } from "@/shared/lib/stage-utils";
import {
  PositionInfoCard,
  PositionCandidatesTable,
} from "@/widgets/positions";
import { RubricSummaryCard } from "@/widgets/rubrics";

export const Route = createFileRoute("/_authenticated/positions/$positionId")({
  component: PositionDetailPage,
});

function PositionDetailPage() {
  const navigate = useNavigate();
  const { positionId } = Route.useParams();
  const positionIdNum = Number(positionId);
  const { data: position, isLoading, error } = usePosition(positionIdNum);
  const archivePosition = useArchivePosition(positionIdNum);
  const [archiveDialogOpen, setArchiveDialogOpen] = useState(false);
  const [archiveError, setArchiveError] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div className="p-8 space-y-8">
        <div className="flex items-center justify-between">
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-10 w-28" />
        </div>
        <Card>
          <CardContent className="pt-6 space-y-4">
            <Skeleton className="h-6 w-full" />
            <Skeleton className="h-6 w-full" />
            <Skeleton className="h-6 w-3/4" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error || !position) {
    return (
      <div className="p-8">
        <Card>
          <CardContent className="pt-6">
            <p className="text-center text-muted-foreground">
              Position not found
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-semibold tracking-tight">{position.title}</h1>
          <Badge variant={getStatusVariant(position.status)}>
            {formatStatus(position.status)}
          </Badge>
        </div>
        <Button variant="outline" onClick={() => setArchiveDialogOpen(true)}>
          <Archive className="mr-2 h-4 w-4" />
          Archive
        </Button>
      </div>

      <PositionInfoCard
        positionId={positionIdNum}
        title={position.title}
        requirements={position.requirements}
        teamId={position.team_id}
        teamName={position.team_name}
        hiringManagerId={position.hiring_manager_id}
        hiringManagerName={position.hiring_manager_name}
        status={position.status}
        createdAt={position.created_at}
        updatedAt={position.updated_at}
      />

      <RubricSummaryCard positionId={positionIdNum} />

      <PositionCandidatesTable candidates={position.candidates} />

      <Dialog open={archiveDialogOpen} onOpenChange={(open) => {
        setArchiveDialogOpen(open);
        if (!open) setArchiveError(null);
      }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Archive Position</DialogTitle>
            <DialogDescription>
              Are you sure you want to archive &ldquo;{position.title}&rdquo;?
              It will be hidden from the positions list and dropdown menus.
            </DialogDescription>
          </DialogHeader>
          {archiveError && (
            <p className="text-sm text-destructive">{archiveError}</p>
          )}
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setArchiveDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={async () => {
                try {
                  setArchiveError(null);
                  await archivePosition.mutateAsync({
                    path: { position_id: positionIdNum },
                  });
                  setArchiveDialogOpen(false);
                  navigate({ to: "/positions" });
                } catch {
                  setArchiveError("Failed to archive position. Please try again.");
                }
              }}
              disabled={archivePosition.isPending}
            >
              {archivePosition.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Archive
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
