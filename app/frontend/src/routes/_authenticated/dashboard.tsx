import { createFileRoute } from "@tanstack/react-router";
import {
  CandidatesPipeline,
  RecentActivity,
  PositionsOverview,
} from "@/widgets/dashboard";

export const Route = createFileRoute("/_authenticated/dashboard")({
  component: Dashboard,
});

function Dashboard() {
  return (
    <div className="p-8 space-y-8">
      <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 [&>*:first-child]:lg:col-span-2">
        <CandidatesPipeline />
        <RecentActivity />
        <PositionsOverview />
      </div>
    </div>
  );
}
