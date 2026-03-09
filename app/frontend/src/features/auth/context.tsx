import type { UserResponse } from "@/shared/api/types.gen";
import { useCurrentUser } from "./hooks/use-current-user";

export type User = UserResponse;

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export function useAuth(): AuthState {
  return useCurrentUser();
}
