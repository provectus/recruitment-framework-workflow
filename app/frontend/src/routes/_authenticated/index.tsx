import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/_authenticated/")({
  component: Home,
});

function Home() {
  return (
    <div className="p-6">
      <h3 className="text-2xl font-semibold">Welcome to Tap</h3>
      <p className="text-muted-foreground mt-2">
        Recruitment workflow automation for Provectus
      </p>
    </div>
  );
}
