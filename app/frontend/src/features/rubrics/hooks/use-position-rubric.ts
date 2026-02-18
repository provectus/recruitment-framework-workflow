import { useQuery } from "@tanstack/react-query";
import { getPositionRubricApiPositionsPositionIdRubricGetOptions } from "@/shared/api/@tanstack/react-query.gen";

export function usePositionRubric(positionId: number) {
  return useQuery({
    ...getPositionRubricApiPositionsPositionIdRubricGetOptions({
      path: { position_id: positionId },
    }),
  });
}
