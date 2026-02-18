import { createFileRoute, Outlet, redirect } from "@tanstack/react-router";
import { Sidebar } from "@/widgets/sidebar";

export const Route = createFileRoute("/_authenticated")({
  beforeLoad: ({ context, location }) => {
    if (context.auth.isLoading) return;
    if (!context.auth.isAuthenticated) {
      throw redirect({
        to: "/login",
        search: { redirect: location.href, error: undefined },
      });
    }
  },
  component: AuthenticatedLayout,
});

function AuthenticatedLayout() {
  return (
    <div className="flex h-[calc(100vh-49px)]">
      <Sidebar />
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
