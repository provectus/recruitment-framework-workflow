import type { EvaluationResponse } from "@/shared/api";

export const STEP_ORDER = [
  "cv_analysis",
  "screening_eval",
  "technical_eval",
  "recommendation",
  "feedback_gen",
] as const;

export type StepType = (typeof STEP_ORDER)[number];

export type StepMap = Partial<Record<StepType, EvaluationResponse>>;

export function buildStepMap(evaluations: EvaluationResponse[]): StepMap {
  const map: StepMap = {};
  for (const ev of evaluations) {
    const step = ev.step_type as StepType;
    if (STEP_ORDER.includes(step)) {
      const existing = map[step];
      if (!existing || ev.version > existing.version) {
        map[step] = ev;
      }
    }
  }
  return map;
}

export function firstSentence(text: string | undefined | null, maxLen = 120): string {
  if (!text) return "—";
  const match = text.match(/^.+?\.\s/);
  const sentence = match ? match[0].trim() : text;
  return sentence.length > maxLen ? sentence.slice(0, maxLen) + "…" : sentence;
}

interface CvSummary {
  metric: string;
  oneLiner: string;
}

export function getCvAnalysisSummary(result: Record<string, unknown> | null): CvSummary {
  if (!result) return { metric: "—", oneLiner: "—" };
  const skills = result.skills_match as Array<{ present: boolean }> | undefined;
  const present = skills?.filter((s) => s.present).length ?? 0;
  const total = skills?.length ?? 0;
  return {
    metric: `${present}/${total} skills`,
    oneLiner: firstSentence(result.overall_fit as string),
  };
}

interface ScreeningSummary {
  metric: string;
  oneLiner: string;
}

export function getScreeningSummary(result: Record<string, unknown> | null): ScreeningSummary {
  if (!result) return { metric: "—", oneLiner: "—" };
  const strengths = result.strengths as string[] | undefined;
  const topics = result.key_topics as string[] | undefined;
  return {
    metric: strengths?.[0] ?? "—",
    oneLiner: topics?.[0] ?? "—",
  };
}

interface TechnicalSummary {
  metric: string;
  score: number | null;
  maxScore: number;
  oneLiner: string;
}

export function getTechnicalSummary(result: Record<string, unknown> | null): TechnicalSummary {
  if (!result) return { metric: "—", score: null, maxScore: 5, oneLiner: "—" };
  const score = result.weighted_total as number | undefined;
  const strengths = result.strengths_summary as string[] | undefined;
  return {
    metric: score != null ? `${score.toFixed(1)} / 5.0` : "—",
    score: score ?? null,
    maxScore: 5,
    oneLiner: strengths?.[0] ?? "—",
  };
}

interface RecommendationSummary {
  metric: string;
  verdict: string | null;
  confidence: string | null;
  oneLiner: string;
}

export function getRecommendationSummary(result: Record<string, unknown> | null): RecommendationSummary {
  if (!result) return { metric: "—", verdict: null, confidence: null, oneLiner: "—" };
  const verdict = result.recommendation as string | undefined;
  const confidence = result.confidence as string | undefined;
  const verdictLabel = verdict?.replace(/_/g, " ") ?? "—";
  const confLabel = confidence ?? "";
  return {
    metric: confLabel ? `${verdictLabel} · ${confLabel}` : verdictLabel,
    verdict: verdict ?? null,
    confidence: confidence ?? null,
    oneLiner: firstSentence(result.reasoning as string, 150),
  };
}

interface FeedbackSummary {
  metric: string;
  oneLiner: string;
}

export function getFeedbackSummary(result: Record<string, unknown> | null): FeedbackSummary {
  if (!result) return { metric: "—", oneLiner: "—" };
  const stage = result.rejection_stage as string | undefined;
  return {
    metric: stage ? `Stage: ${stage}` : "—",
    oneLiner: firstSentence(result.feedback_text as string),
  };
}

export function getStepSummary(stepType: string, result: Record<string, unknown> | null) {
  switch (stepType) {
    case "cv_analysis":
      return getCvAnalysisSummary(result);
    case "screening_eval":
      return getScreeningSummary(result);
    case "technical_eval":
      return getTechnicalSummary(result);
    case "recommendation":
      return getRecommendationSummary(result);
    case "feedback_gen":
      return getFeedbackSummary(result);
    default:
      return { metric: "—", oneLiner: "—" };
  }
}
