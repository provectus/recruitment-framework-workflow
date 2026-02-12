export const STAGE_LABELS: Record<string, string> = {
  new: "New",
  screening: "Screening",
  technical: "Technical",
  offer: "Offer",
  hired: "Hired",
  rejected: "Rejected",
};

export function getStageVariant(
  stage: string
): "default" | "secondary" | "outline" | "destructive" {
  switch (stage.toLowerCase()) {
    case "new":
      return "default";
    case "screening":
      return "secondary";
    case "technical":
      return "outline";
    case "offer":
      return "default";
    case "hired":
      return "default";
    case "rejected":
      return "destructive";
    default:
      return "default";
  }
}

export function getStatusVariant(
  status: string
): "default" | "secondary" | "outline" | "destructive" {
  switch (status.toLowerCase()) {
    case "open":
      return "default";
    case "on_hold":
    case "on hold":
      return "secondary";
    case "closed":
      return "outline";
    default:
      return "default";
  }
}

export function formatStage(stage: string): string {
  return STAGE_LABELS[stage.toLowerCase()] || stage.charAt(0).toUpperCase() + stage.slice(1).toLowerCase();
}

export function formatStatus(status: string): string {
  switch (status.toLowerCase()) {
    case "open":
      return "Open";
    case "on_hold":
      return "On Hold";
    case "closed":
      return "Closed";
    default:
      return status;
  }
}
