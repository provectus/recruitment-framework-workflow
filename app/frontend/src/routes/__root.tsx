import { createRootRouteWithContext, Outlet } from "@tanstack/react-router";
import { TanStackRouterDevtools } from "@tanstack/react-router-devtools";
import { useAuth, type AuthState } from "@/features/auth";
import { UserMenu } from "@/widgets/user-menu";

interface RouterContext {
  auth: AuthState;
}

function RootLayout() {
  const { isAuthenticated } = useAuth();

  return (
    <>
      <div className="min-h-screen">
        <header className="border-b p-4 flex items-center justify-between">
          <span className="text-lg font-semibold">Tap</span>
          {isAuthenticated && <UserMenu />}
        </header>
        <main>
          <Outlet />
        </main>
      </div>
      <TanStackRouterDevtools />
    </>
  );
}

export const Route = createRootRouteWithContext<RouterContext>()({ component: RootLayout });
