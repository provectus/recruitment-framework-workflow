import { useState } from "react";
import { Loader2 } from "lucide-react";
import { useAddToPosition } from "@/features/candidates";
import { Button } from "@/shared/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/shared/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/ui/select";

interface AvailablePosition {
  id: number;
  title: string;
}

interface AddToPositionDialogProps {
  candidateId: number;
  candidateName: string;
  availablePositions: AvailablePosition[];
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function AddToPositionDialog({
  candidateId,
  candidateName,
  availablePositions,
  open,
  onOpenChange,
}: AddToPositionDialogProps) {
  const addToPosition = useAddToPosition(candidateId);
  const [selectedPositionId, setSelectedPositionId] = useState<string>("");
  const [addError, setAddError] = useState<string>("");

  const handleAdd = async () => {
    if (!selectedPositionId) return;

    setAddError("");
    try {
      await addToPosition.mutateAsync({
        path: { candidate_id: candidateId },
        body: { position_id: Number(selectedPositionId) },
      });
      onOpenChange(false);
      setSelectedPositionId("");
    } catch (err: unknown) {
      if (err && typeof err === "object" && "response" in err) {
        const axiosError = err as { response?: { status?: number } };
        if (axiosError.response?.status === 409) {
          setAddError("Candidate is already associated with this position.");
        } else {
          setAddError("Failed to add candidate to position.");
        }
      } else {
        setAddError("Failed to add candidate to position.");
      }
    }
  };

  const handleOpenChange = (nextOpen: boolean) => {
    if (!nextOpen) {
      setSelectedPositionId("");
      setAddError("");
    }
    onOpenChange(nextOpen);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add to Position</DialogTitle>
          <DialogDescription>
            Select a position to link {candidateName} to.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <Select
            value={selectedPositionId}
            onValueChange={setSelectedPositionId}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Select a position" />
            </SelectTrigger>
            <SelectContent>
              {availablePositions.map((position) => (
                <SelectItem key={position.id} value={String(position.id)}>
                  {position.title}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {addError && (
            <p className="text-sm font-medium text-destructive">{addError}</p>
          )}
        </div>
        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => handleOpenChange(false)}
          >
            Cancel
          </Button>
          <Button
            onClick={handleAdd}
            disabled={!selectedPositionId || addToPosition.isPending}
          >
            {addToPosition.isPending && (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            )}
            Add
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
