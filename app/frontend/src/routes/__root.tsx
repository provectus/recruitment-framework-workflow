import { createRootRouteWithContext, Outlet, type ErrorComponentProps } from "@tanstack/react-router";
import { TanStackRouterDevtools } from "@tanstack/react-router-devtools";
import { useAuth, type AuthState } from "@/features/auth";
import { UserMenu } from "@/widgets/user-menu";
import { Toaster } from "@/shared/ui/sonner";
import { ErrorBoundary, ErrorFallback } from "@/shared/ui/error-boundary";

interface RouterContext {
  auth: AuthState;
}

function RootLayout() {
  const { isAuthenticated } = useAuth();

  return (
    <ErrorBoundary>
      <div className="min-h-screen">
        <header className="sticky top-0 z-40 border-b border-border px-6 py-3 flex items-center justify-between bg-background">
          <span className="text-lg font-bold tracking-tight">Lauter</span>
          {isAuthenticated && <UserMenu />}
        </header>
        <main>
          <Outlet />
        </main>
      </div>
      <TanStackRouterDevtools />
      <Toaster />
    </ErrorBoundary>
  );
}

function RouteErrorComponent({ error, reset }: ErrorComponentProps) {
  return (
    <ErrorFallback
      error={error instanceof Error ? error : new Error(String(error))}
      onReset={reset}
    />
  );
}

export const Route = createRootRouteWithContext<RouterContext>()({
  component: RootLayout,
  errorComponent: RouteErrorComponent,
});
