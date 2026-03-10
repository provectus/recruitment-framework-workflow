const STEP_LABELS: Record<string, string> = {
  cv_analysis: "CV Analysis",
  screening_eval: "Screening Evaluation",
  technical_eval: "Technical Evaluation",
  recommendation: "Recommendation",
  feedback_gen: "Feedback Draft",
} as const;

const STATUS_VARIANTS: Record<string, "default" | "secondary" | "destructive"> =
  {
    pending: "secondary",
    running: "default",
    completed: "default",
    failed: "destructive",
  } as const;

const STATUS_LABELS: Record<string, string> = {
  pending: "Pending",
  running: "Running",
  completed: "Completed",
  failed: "Failed",
} as const;

export function getEvaluationStepLabel(stepType: string): string {
  return STEP_LABELS[stepType] ?? stepType;
}

export function getEvaluationStatusVariant(
  status: string
): "default" | "secondary" | "destructive" {
  return STATUS_VARIANTS[status.toLowerCase()] ?? "default";
}

export function formatEvaluationStatus(status: string): string {
  return STATUS_LABELS[status.toLowerCase()] ?? status;
}
