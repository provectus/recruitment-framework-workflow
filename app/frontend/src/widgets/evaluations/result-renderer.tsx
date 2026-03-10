import { CvAnalysisResult } from "./cv-analysis-result";
import { ScreeningEvalResult } from "./screening-eval-result";
import { TechnicalEvalResult } from "./technical-eval-result";
import { RecommendationResult } from "./recommendation-result";
import { FeedbackDraftResult } from "./feedback-draft-result";

interface ResultRendererProps {
  stepType: string;
  result: Record<string, unknown>;
}

export function ResultRenderer({ stepType, result }: ResultRendererProps) {
  switch (stepType) {
    case "cv_analysis":
      return (
        <CvAnalysisResult
          result={result as unknown as Parameters<typeof CvAnalysisResult>[0]["result"]}
        />
      );
    case "screening_eval":
      return (
        <ScreeningEvalResult
          result={result as unknown as Parameters<typeof ScreeningEvalResult>[0]["result"]}
        />
      );
    case "technical_eval":
      return (
        <TechnicalEvalResult
          result={result as unknown as Parameters<typeof TechnicalEvalResult>[0]["result"]}
        />
      );
    case "recommendation":
      return (
        <RecommendationResult
          result={result as unknown as Parameters<typeof RecommendationResult>[0]["result"]}
        />
      );
    case "feedback_gen":
      return (
        <FeedbackDraftResult
          result={result as unknown as Parameters<typeof FeedbackDraftResult>[0]["result"]}
        />
      );
    default:
      return (
        <pre className="text-xs bg-muted/40 rounded-lg p-4 overflow-auto whitespace-pre-wrap break-words">
          {JSON.stringify(result, null, 2)}
        </pre>
      );
  }
}
