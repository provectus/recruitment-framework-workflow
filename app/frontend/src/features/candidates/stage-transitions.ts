export { STAGE_LABELS } from "@/shared/lib/stage-utils";

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
