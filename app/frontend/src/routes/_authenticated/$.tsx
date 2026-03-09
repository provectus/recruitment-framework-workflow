import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { FileQuestion } from "lucide-react";
import { Button } from "@/shared/ui/button";

export const Route = createFileRoute("/_authenticated/$")({
  component: NotFoundPage,
});

function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] p-8 text-center">
      <FileQuestion className="h-16 w-16 text-muted-foreground/50 mb-6" />
      <h1 className="text-2xl font-semibold tracking-tight mb-2">
        Page not found
      </h1>
      <p className="text-muted-foreground max-w-md mb-6">
        The page you're looking for doesn't exist or has been moved.
      </p>
      <Button onClick={() => navigate({ to: "/dashboard" })}>
        Go to Dashboard
      </Button>
    </div>
  );
}
