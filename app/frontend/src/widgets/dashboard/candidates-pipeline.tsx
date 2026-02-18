import { useNavigate } from "@tanstack/react-router";
import { Users } from "lucide-react";
import { useDashboardStats } from "@/features/dashboard";
import { formatStage } from "@/shared/lib/stage-utils";
import { Button } from "@/shared/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/shared/ui/card";
import { Skeleton } from "@/shared/ui/skeleton";

const STAGE_COLORS: Record<string, string> = {
  new: "bg-slate-500",
  screening: "bg-blue-500",
  technical: "bg-violet-500",
  offer: "bg-amber-500",
  hired: "bg-emerald-500",
  rejected: "bg-red-500",
};

export function CandidatesPipeline() {
  const { data, isLoading } = useDashboardStats();
  const navigate = useNavigate();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Candidates Pipeline</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {isLoading ? (
          <>
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-5 w-full" />
            ))}
          </>
        ) : data && data.pipeline_counts.length > 0 ? (
          data.pipeline_counts.map((item) => (
            <div key={item.stage} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span
                  className={`h-2 w-2 rounded-full ${STAGE_COLORS[item.stage] ?? "bg-slate-400"}`}
                />
                <span className="text-sm">{formatStage(item.stage)}</span>
              </div>
              <span className="text-sm font-medium">{item.count}</span>
            </div>
          ))
        ) : (
          <div className="flex flex-col items-center gap-2 py-4">
            <Users className="h-8 w-8 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">No candidates yet</p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate({ to: "/candidates" })}
            >
              Add Candidates
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
