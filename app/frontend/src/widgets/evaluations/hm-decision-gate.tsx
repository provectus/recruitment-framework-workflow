import { useState } from "react";
import type { EvaluationResponse } from "@/shared/api";
import { useUpdateStage } from "@/features/candidates";
import { Button } from "@/shared/ui/button";
import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/shared/ui/alert-dialog";
import { Loader2 } from "lucide-react";

interface HmDecisionGateProps {
  candidatePositionId: number;
  candidateId: number;
  positionId: number;
  evaluations: EvaluationResponse[];
  currentStage?: string;
}

type DecisionAction = {
  label: string;
  targetStage: string;
  variant: "default" | "destructive";
  title: string;
  description: string;
};

function useDecisionActions(
  evaluations: EvaluationResponse[],
  currentStage: string | undefined
): DecisionAction[] {
  const stepMap = new Map(evaluations.map((e) => [e.step_type, e]));
  const screeningEval = stepMap.get("screening_eval");
  const recommendation = stepMap.get("recommendation");

  const actions: DecisionAction[] = [];

  if (
    screeningEval?.status === "completed" &&
    currentStage === "screening"
  ) {
    actions.push({
      label: "Proceed to Technical",
      targetStage: "technical",
      variant: "default",
      title: "Proceed to Technical Interview",
      description:
        "This will move the candidate to the Technical Interview stage. The candidate will be notified and a technical interview will be scheduled.",
    });
    actions.push({
      label: "Reject",
      targetStage: "rejected",
      variant: "destructive",
      title: "Reject Candidate",
      description:
        "This will reject the candidate at the screening stage. The candidate will be notified that they will not be moving forward.",
    });
  }

  if (
    recommendation?.status === "completed" &&
    currentStage === "technical"
  ) {
    actions.push({
      label: "Hire",
      targetStage: "offer",
      variant: "default",
      title: "Extend Offer",
      description:
        "This will move the candidate to the Offer stage. An offer will be prepared and sent to the candidate.",
    });
    actions.push({
      label: "Reject",
      targetStage: "rejected",
      variant: "destructive",
      title: "Reject Candidate",
      description:
        "This will reject the candidate after the technical interview. The candidate will be notified that they will not be moving forward.",
    });
  }

  return actions;
}

interface ConfirmDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  action: DecisionAction;
  onConfirm: () => void;
  isPending: boolean;
}

function ConfirmDialog({
  open,
  onOpenChange,
  action,
  onConfirm,
  isPending,
}: ConfirmDialogProps) {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{action.title}</AlertDialogTitle>
          <AlertDialogDescription>{action.description}</AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={isPending}>Cancel</AlertDialogCancel>
          <Button
            variant={action.variant}
            onClick={onConfirm}
            disabled={isPending}
          >
            {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {action.label}
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

export function HmDecisionGate({
  candidateId,
  positionId,
  evaluations,
  currentStage,
}: HmDecisionGateProps) {
  const [pendingAction, setPendingAction] = useState<DecisionAction | null>(
    null
  );

  const updateStage = useUpdateStage(candidateId);
  const actions = useDecisionActions(evaluations, currentStage);

  if (actions.length === 0) {
    return null;
  }

  const handleConfirm = () => {
    if (!pendingAction) return;
    updateStage.mutate(
      {
        path: { candidate_id: candidateId, position_id: positionId },
        body: { stage: pendingAction.targetStage },
      },
      {
        onSuccess: () => {
          setPendingAction(null);
        },
        onError: () => {
          setPendingAction(null);
        },
      }
    );
  };

  return (
    <>
      <div className="flex items-center gap-2 pt-2">
        <span className="text-sm text-muted-foreground font-medium">
          HM Decision:
        </span>
        {actions.map((action) => (
          <Button
            key={action.targetStage}
            variant={action.variant}
            size="sm"
            onClick={() => setPendingAction(action)}
          >
            {action.label}
          </Button>
        ))}
      </div>

      {pendingAction && (
        <ConfirmDialog
          open={pendingAction !== null}
          onOpenChange={(open) => {
            if (!open) setPendingAction(null);
          }}
          action={pendingAction}
          onConfirm={handleConfirm}
          isPending={updateStage.isPending}
        />
      )}
    </>
  );
}
