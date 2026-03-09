import { useMutation, useQueryClient } from "@tanstack/react-query";
import { devLoginApiAuthDevLoginPostMutation } from "@/shared/api/@tanstack/react-query.gen";
import { currentUserQueryKey } from "./use-current-user";

export function useDevLogin() {
  const queryClient = useQueryClient();

  return useMutation({
    ...devLoginApiAuthDevLoginPostMutation(),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: currentUserQueryKey() });
    },
  });
}
