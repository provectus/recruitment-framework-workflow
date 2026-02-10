import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useAuth } from "@/lib/auth-context";
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
  const { refetch } = useAuth();

  useEffect(() => {
    refetch().then(() => {
      navigate({ to: redirect || "/" });
    });
  }, [refetch, navigate, redirect]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <p className="text-muted-foreground">Signing in...</p>
    </div>
  );
}
