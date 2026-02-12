import { createFileRoute } from "@tanstack/react-router";
import {
  CandidatesPipeline,
  RecentEvaluations,
  UpcomingInterviews,
} from "@/widgets/dashboard";

export const Route = createFileRoute("/_authenticated/dashboard")({
  component: Dashboard,
});

function Dashboard() {
  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-semibold">Dashboard</h1>
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <CandidatesPipeline />
        <RecentEvaluations />
        <UpcomingInterviews />
      </div>
    </div>
  );
}
