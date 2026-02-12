export const VALID_TRANSITIONS: Record<string, string[]> = {
  new: ["screening", "rejected"],
  screening: ["technical", "rejected"],
  technical: ["offer", "rejected"],
  offer: ["hired", "rejected"],
  hired: [],
  rejected: [],
};

export function getValidNextStages(currentStage: string): string[] {
  return VALID_TRANSITIONS[currentStage] ?? [];
}

export const STAGE_LABELS: Record<string, string> = {
  new: "New",
  screening: "Screening",
  technical: "Technical",
  offer: "Offer",
  hired: "Hired",
  rejected: "Rejected",
};
