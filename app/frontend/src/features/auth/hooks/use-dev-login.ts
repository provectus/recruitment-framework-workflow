import { useMutation, useQueryClient } from "@tanstack/react-query";
import { devLoginAuthDevLoginPostMutation } from "@/shared/api/@tanstack/react-query.gen";
import { currentUserQueryKey } from "./use-current-user";

export function useDevLogin() {
  const queryClient = useQueryClient();

  return useMutation({
    ...devLoginAuthDevLoginPostMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: currentUserQueryKey() });
    },
  });
}
