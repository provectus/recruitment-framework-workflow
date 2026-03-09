import { useMutation, useQueryClient } from "@tanstack/react-query";
import { logoutApiAuthLogoutPostMutation } from "@/shared/api/@tanstack/react-query.gen";
import { currentUserQueryKey } from "./use-current-user";

export function useLogout() {
  const queryClient = useQueryClient();

  return useMutation({
    ...logoutApiAuthLogoutPostMutation(),
    onSuccess: () => {
      queryClient.setQueryData(currentUserQueryKey(), null);
    },
  });
}
