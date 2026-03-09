import { useMutation, useQueryClient } from "@tanstack/react-query";
import { archivePositionApiPositionsPositionIdArchivePostMutation } from "@/shared/api/@tanstack/react-query.gen";

export function useArchivePosition(positionId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    ...archivePositionApiPositionsPositionIdArchivePostMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["listPositionsApiPositionsGet"] });
      queryClient.invalidateQueries({
        queryKey: ["getPositionApiPositionsPositionIdGet", { path: { position_id: positionId } }],
      });
    },
  });
}
