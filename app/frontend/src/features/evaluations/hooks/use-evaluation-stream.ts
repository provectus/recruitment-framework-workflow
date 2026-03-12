import { useCallback, useEffect, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { listEvaluationsApiEvaluationsCandidatePositionIdGetQueryKey } from "@/shared/api/@tanstack/react-query.gen";
import { getEvaluationStepLabel } from "@/shared/lib/evaluation-utils";

interface StatusChangeEvent {
  evaluation_id: number;
  step_type: string;
  status: string;
}

const MAX_RETRIES = 3;
const BASE_DELAY_MS = 1000;

export function useEvaluationStream(
  candidatePositionId: number,
  enabled: boolean
) {
  const queryClient = useQueryClient();
  const esRef = useRef<EventSource | null>(null);
  const retriesRef = useRef(0);
  const retryTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const invalidateEvaluations = useCallback(() => {
    queryClient.invalidateQueries({
      queryKey: listEvaluationsApiEvaluationsCandidatePositionIdGetQueryKey({
        path: { candidate_position_id: candidatePositionId },
      }),
    });
  }, [queryClient, candidatePositionId]);

  const cleanup = useCallback(() => {
    if (retryTimeoutRef.current !== null) {
      clearTimeout(retryTimeoutRef.current);
      retryTimeoutRef.current = null;
    }
    esRef.current?.close();
    esRef.current = null;
  }, []);

  useEffect(() => {
    if (!enabled) {
      cleanup();
      retriesRef.current = 0;
      return;
    }

    function connect() {
      cleanup();

      const url = `/api/evaluations/${candidatePositionId}/stream`;
      const es = new EventSource(url, { withCredentials: true });
      esRef.current = es;

      es.addEventListener("status_change", (event: MessageEvent) => {
        retriesRef.current = 0;

        let data: StatusChangeEvent;
        try {
          data = JSON.parse(event.data) as StatusChangeEvent;
        } catch {
          return;
        }

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

        if (retriesRef.current < MAX_RETRIES) {
          const delay = BASE_DELAY_MS * Math.pow(2, retriesRef.current);
          retriesRef.current += 1;
          retryTimeoutRef.current = setTimeout(connect, delay);
        }
      };

      es.addEventListener("done", () => {
        es.close();
        esRef.current = null;
        retriesRef.current = 0;
        invalidateEvaluations();
      });
    }

    connect();

    return () => {
      cleanup();
      retriesRef.current = 0;
    };
  }, [candidatePositionId, enabled, invalidateEvaluations, cleanup]);
}
