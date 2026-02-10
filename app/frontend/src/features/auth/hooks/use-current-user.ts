import { useQuery } from "@tanstack/react-query";
import {
  getMeAuthMeGetOptions,
  getMeAuthMeGetQueryKey,
} from "@/shared/api/@tanstack/react-query.gen";

export { getMeAuthMeGetQueryKey as currentUserQueryKey };

export function useCurrentUser() {
  const { data, isLoading } = useQuery({
    ...getMeAuthMeGetOptions(),
    retry: false,
  });

  const user = data ?? null;

  return { user, isLoading, isAuthenticated: user !== null };
}
