import { useState } from "react";
import { Link } from "@tanstack/react-router";
import { Loader2, MoreVertical, Upload, FileText, Trash2 } from "lucide-react";
import type { PositionStageItem } from "@/shared/api";
import { formatStage } from "@/shared/lib/stage-utils";
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/shared/ui/dropdown-menu";
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
  const [stageError, setStageError] = useState<string | null>(null);
  const [removeDialogOpen, setRemoveDialogOpen] = useState(false);
  const [removeError, setRemoveError] = useState<string | null>(null);
  const [positionToRemove, setPositionToRemove] = useState<{
    id: number;
    title: string;
  } | null>(null);

  const handleStageChange = async (positionId: number, newStage: string) => {
    setUpdatingStage(positionId);
    setStageError(null);
    try {
      await updateStageMutation.mutateAsync({
        path: { candidate_id: candidateId, position_id: positionId },
        body: { stage: newStage },
      });
    } catch {
      setStageError("Failed to update stage. Please try again.");
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
    setRemoveError(null);
    try {
      await removeFromPosition.mutateAsync({
        path: {
          candidate_id: candidateId,
          position_id: positionToRemove.id,
        },
      });
      setRemoveDialogOpen(false);
      setPositionToRemove(null);
    } catch {
      setRemoveError("Failed to remove from position. Please try again.");
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
      {stageError && (
        <p className="text-sm text-destructive mb-2">{stageError}</p>
      )}
      <div className="border border-border/50 rounded-xl shadow-soft-xs overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Position</TableHead>
              <TableHead>Stage</TableHead>
              <TableHead className="w-12"></TableHead>
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
                          {formatStage(position.stage)}
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
                                {formatStage(position.stage)}
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
                                {formatStage(stage)}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-8 w-8">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem
                          onClick={() =>
                            onUploadClick(position.candidate_position_id)
                          }
                        >
                          <Upload className="h-4 w-4" />
                          Upload CV
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() =>
                            onTranscriptClick(position.candidate_position_id)
                          }
                        >
                          <FileText className="h-4 w-4" />
                          Add Transcript
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          variant="destructive"
                          onClick={() =>
                            handleRemoveClick(
                              position.position_id,
                              position.position_title,
                            )
                          }
                          disabled={removeFromPosition.isPending}
                        >
                          <Trash2 className="h-4 w-4" />
                          Remove from Position
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>

      <Dialog open={removeDialogOpen} onOpenChange={(open) => {
        setRemoveDialogOpen(open);
        if (!open) setRemoveError(null);
      }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Remove from Position</DialogTitle>
            <DialogDescription>
              Remove {candidateName} from {positionToRemove?.title}? This will
              delete their pipeline progress for this position.
            </DialogDescription>
          </DialogHeader>
          {removeError && (
            <p className="text-sm text-destructive">{removeError}</p>
          )}
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
