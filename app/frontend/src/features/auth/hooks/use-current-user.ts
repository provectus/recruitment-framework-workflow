import { useQuery } from "@tanstack/react-query";
import {
  getMeApiAuthMeGetOptions,
  getMeApiAuthMeGetQueryKey,
} from "@/shared/api/@tanstack/react-query.gen";

export { getMeApiAuthMeGetQueryKey as currentUserQueryKey };

export function useCurrentUser() {
  const { data, isLoading } = useQuery({
    ...getMeApiAuthMeGetOptions(),
    retry: false,
    staleTime: Infinity,
    refetchOnWindowFocus: false,
    refetchOnMount: false,
    refetchOnReconnect: true,
  });

  const user = data ?? null;

  return { user, isLoading, isAuthenticated: user !== null };
}
