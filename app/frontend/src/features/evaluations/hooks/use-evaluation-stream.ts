import { useEffect, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { listEvaluationsApiEvaluationsCandidatePositionIdGetQueryKey } from "@/shared/api/@tanstack/react-query.gen";
import { getEvaluationStepLabel } from "@/shared/lib/evaluation-utils";

interface StatusChangeEvent {
  evaluation_id: number;
  step_type: string;
  status: string;
}

export function useEvaluationStream(
  candidatePositionId: number,
  enabled: boolean
) {
  const queryClient = useQueryClient();
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!enabled) {
      esRef.current?.close();
      esRef.current = null;
      return;
    }

    const url = `/api/evaluations/${candidatePositionId}/stream`;
    const es = new EventSource(url, { withCredentials: true });
    esRef.current = es;

    const invalidateEvaluations = () => {
      queryClient.invalidateQueries({
        queryKey: listEvaluationsApiEvaluationsCandidatePositionIdGetQueryKey({
          path: { candidate_position_id: candidatePositionId },
        }),
      });
    };

    es.addEventListener("status_change", (event: MessageEvent) => {
      const data = JSON.parse(event.data) as StatusChangeEvent;
      const stepLabel = getEvaluationStepLabel(data.step_type);

      if (data.status === "completed") {
        toast.success(`${stepLabel} completed`);
      } else if (data.status === "failed") {
        toast.error(`${stepLabel} failed`);
      }

      invalidateEvaluations();
    });

    es.onerror = () => {
      es.close();
      esRef.current = null;
      invalidateEvaluations();
    };

    es.addEventListener("done", () => {
      es.close();
      esRef.current = null;
      invalidateEvaluations();
    });

    return () => {
      es.close();
      esRef.current = null;
    };
  }, [candidatePositionId, enabled, queryClient]);
}
