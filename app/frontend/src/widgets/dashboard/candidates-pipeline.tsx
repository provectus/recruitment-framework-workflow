import { useNavigate } from "@tanstack/react-router";
import { Users, TrendingUp } from "lucide-react";
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
  new: "bg-stone-400 dark:bg-stone-500",
  screening: "bg-amber-500 dark:bg-amber-400",
  technical: "bg-orange-500 dark:bg-orange-400",
  offer: "bg-yellow-500 dark:bg-yellow-400",
  hired: "bg-emerald-500 dark:bg-emerald-400",
  rejected: "bg-red-500 dark:bg-red-400",
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
                  className={`h-2 w-2 rounded-full ${STAGE_COLORS[item.stage] ?? "bg-stone-400"}`}
                />
                <span className="text-sm">{formatStage(item.stage)}</span>
              </div>
              <span className="text-sm font-medium font-mono tabular-nums">{item.count}</span>
            </div>
          ))
        ) : (
          <div className="flex flex-col items-center gap-2 py-4">
            <div className="relative inline-flex items-center justify-center">
              <Users className="size-10 text-muted-foreground/30" />
              <div className="absolute -bottom-1.5 -right-1.5 rounded-full bg-card p-1">
                <TrendingUp className="size-3.5 text-primary" />
              </div>
            </div>
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
