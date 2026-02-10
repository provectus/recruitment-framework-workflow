import { useMutation, useQueryClient } from "@tanstack/react-query";
import { logoutAuthLogoutPostMutation } from "@/shared/api/@tanstack/react-query.gen";
import { currentUserQueryKey } from "./use-current-user";

export function useLogout() {
  const queryClient = useQueryClient();

  return useMutation({
    ...logoutAuthLogoutPostMutation(),
    onSuccess: () => {
      queryClient.removeQueries({ queryKey: currentUserQueryKey() });
      window.location.href = "/login";
    },
  });
}
