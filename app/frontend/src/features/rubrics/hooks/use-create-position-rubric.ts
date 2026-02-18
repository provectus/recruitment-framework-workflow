import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  createPositionRubricApiPositionsPositionIdRubricPostMutation,
  getPositionRubricApiPositionsPositionIdRubricGetQueryKey,
} from "@/shared/api/@tanstack/react-query.gen";

export function useCreatePositionRubric(positionId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    ...createPositionRubricApiPositionsPositionIdRubricPostMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: getPositionRubricApiPositionsPositionIdRubricGetQueryKey({
          path: { position_id: positionId },
        }),
      });
    },
  });
}
