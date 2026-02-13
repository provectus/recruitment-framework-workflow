import { useState } from "react";
import { Link } from "@tanstack/react-router";
import { Loader2, Trash2, Upload, FileText } from "lucide-react";
import type { PositionStageItem } from "@/shared/api";
import { STAGE_LABELS } from "@/shared/lib/stage-utils";
import { useUpdateStage, useRemoveFromPosition } from "@/features/candidates";
import { Button } from "@/shared/ui/button";
import { Badge } from "@/shared/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/shared/ui/dialog";
import { getStageVariant } from "@/shared/lib/stage-utils";

interface CandidatePositionsTableProps {
  positions: PositionStageItem[];
  candidateId: number;
  candidateName: string;
  onUploadClick: (candidatePositionId: number) => void;
  onTranscriptClick: (candidatePositionId: number) => void;
}

export function CandidatePositionsTable({
  positions,
  candidateId,
  candidateName,
  onUploadClick,
  onTranscriptClick,
}: CandidatePositionsTableProps) {
  const updateStageMutation = useUpdateStage(candidateId);
  const removeFromPosition = useRemoveFromPosition(candidateId);

  const [updatingStage, setUpdatingStage] = useState<number | null>(null);
  const [removeDialogOpen, setRemoveDialogOpen] = useState(false);
  const [positionToRemove, setPositionToRemove] = useState<{
    id: number;
    title: string;
  } | null>(null);

  const handleStageChange = async (positionId: number, newStage: string) => {
    setUpdatingStage(positionId);
    try {
      await updateStageMutation.mutateAsync({
        path: { candidate_id: candidateId, position_id: positionId },
        body: { stage: newStage },
      });
    } catch (err) {
      console.error("Failed to update stage:", err);
    } finally {
      setUpdatingStage(null);
    }
  };

  const handleRemoveClick = (positionId: number, positionTitle: string) => {
    setPositionToRemove({ id: positionId, title: positionTitle });
    setRemoveDialogOpen(true);
  };

  const handleRemoveConfirm = async () => {
    if (!positionToRemove) return;
    try {
      await removeFromPosition.mutateAsync({
        path: {
          candidate_id: candidateId,
          position_id: positionToRemove.id,
        },
      });
      setRemoveDialogOpen(false);
      setPositionToRemove(null);
    } catch (err) {
      console.error("Failed to remove candidate from position:", err);
    }
  };

  if (positions.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-muted-foreground">
          No positions linked yet. Use &apos;Add to Position&apos; to link this
          candidate.
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="border rounded-lg">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Position</TableHead>
              <TableHead>Stage</TableHead>
              <TableHead className="w-32">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {positions.map((position) => {
              const validNextStages = position.valid_next_stages ?? [];
              const isUpdating = updatingStage === position.position_id;
              const isTerminal = validNextStages.length === 0;

              return (
                <TableRow key={position.position_id}>
                  <TableCell className="font-medium">
                    <Link
                      to="/positions/$positionId"
                      params={{
                        positionId: String(position.position_id),
                      }}
                      className="hover:underline"
                    >
                      {position.position_title}
                    </Link>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      {isUpdating ? (
                        <div className="flex items-center gap-2">
                          <Loader2 className="h-4 w-4 animate-spin" />
                          <span className="text-sm text-muted-foreground">
                            Updating...
                          </span>
                        </div>
                      ) : isTerminal ? (
                        <Badge variant={getStageVariant(position.stage)}>
                          {STAGE_LABELS[position.stage]}
                        </Badge>
                      ) : (
                        <Select
                          value={position.stage}
                          onValueChange={(value) =>
                            handleStageChange(position.position_id, value)
                          }
                          disabled={isUpdating}
                        >
                          <SelectTrigger className="w-[140px]">
                            <SelectValue>
                              <Badge
                                variant={getStageVariant(position.stage)}
                              >
                                {STAGE_LABELS[position.stage]}
                              </Badge>
                            </SelectValue>
                          </SelectTrigger>
                          <SelectContent>
                            {validNextStages.map((stage) => (
                              <SelectItem
                                key={stage}
                                value={stage}
                                className={
                                  stage === "rejected"
                                    ? "text-destructive"
                                    : ""
                                }
                              >
                                {STAGE_LABELS[stage]}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          onUploadClick(position.candidate_position_id)
                        }
                      >
                        <Upload className="h-4 w-4 mr-1" />
                        Upload CV
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          onTranscriptClick(position.candidate_position_id)
                        }
                      >
                        <FileText className="h-4 w-4 mr-1" />
                        Add Transcript
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() =>
                          handleRemoveClick(
                            position.position_id,
                            position.position_title,
                          )
                        }
                        disabled={removeFromPosition.isPending}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>

      <Dialog open={removeDialogOpen} onOpenChange={setRemoveDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Remove from Position</DialogTitle>
            <DialogDescription>
              Remove {candidateName} from {positionToRemove?.title}? This will
              delete their pipeline progress for this position.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setRemoveDialogOpen(false);
                setPositionToRemove(null);
              }}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleRemoveConfirm}
              disabled={removeFromPosition.isPending}
            >
              {removeFromPosition.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Remove
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
