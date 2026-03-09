import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  createPositionApiPositionsPostMutation,
  listPositionsApiPositionsGetQueryKey,
} from "@/shared/api/@tanstack/react-query.gen";

export function useCreatePosition() {
  const queryClient = useQueryClient();
  return useMutation({
    ...createPositionApiPositionsPostMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: listPositionsApiPositionsGetQueryKey(),
      });
    },
  });
}
