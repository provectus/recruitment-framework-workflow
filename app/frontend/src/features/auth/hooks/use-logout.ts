import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { logoutApiAuthLogoutPostMutation } from "@/shared/api/@tanstack/react-query.gen";
import { currentUserQueryKey } from "./use-current-user";

export function useLogout() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  return useMutation({
    ...logoutApiAuthLogoutPostMutation(),
    onSuccess: () => {
      queryClient.removeQueries({ queryKey: currentUserQueryKey() });
      navigate({ to: "/login", search: { redirect: undefined, error: undefined } });
    },
  });
}
