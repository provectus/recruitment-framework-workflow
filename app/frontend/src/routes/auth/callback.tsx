import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";
import { currentUserQueryKey } from "@/features/auth";
import { useEffect } from "react";

export const Route = createFileRoute("/auth/callback")({
  validateSearch: (search: Record<string, unknown>) => ({
    redirect: (search.redirect as string) || "/",
  }),
  component: AuthCallback,
});

function AuthCallback() {
  const { redirect } = Route.useSearch();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  useEffect(() => {
    queryClient
      .refetchQueries({ queryKey: currentUserQueryKey() })
      .then(() => navigate({ to: redirect || "/" }));
  }, [queryClient, navigate, redirect]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <p className="text-muted-foreground">Signing in...</p>
    </div>
  );
}
