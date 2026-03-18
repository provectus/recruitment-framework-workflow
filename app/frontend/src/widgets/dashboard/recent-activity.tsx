import { useNavigate } from "@tanstack/react-router";
import { Clock, UserPlus } from "lucide-react";
import { useDashboardStats } from "@/features/dashboard";
import { formatStage, getStageVariant } from "@/shared/lib/stage-utils";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/shared/ui/card";
import { Skeleton } from "@/shared/ui/skeleton";

export function RecentActivity() {
  const { data, isLoading } = useDashboardStats();
  const navigate = useNavigate();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading ? (
          <>
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </>
        ) : data?.recent_candidates?.length ? (
          data.recent_candidates.map((candidate, index) => (
            <div
              key={`${candidate.id}-${index}`}
              className="flex items-start justify-between gap-2"
            >
              <div className="min-w-0">
                <p className="text-sm font-medium truncate">
                  {candidate.full_name}
                </p>
                <p className="text-xs text-muted-foreground truncate">
                  {candidate.position_title ?? "No position"}
                </p>
              </div>
              <div className="flex flex-col items-end gap-1 shrink-0">
                {candidate.stage && (
                  <Badge variant={getStageVariant(candidate.stage)}>
                    {formatStage(candidate.stage)}
                  </Badge>
                )}
                <span className="text-xs text-muted-foreground font-mono tabular-nums">
                  {new Date(candidate.updated_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          ))
        ) : (
          <div className="flex flex-col items-center gap-2 py-4">
            <div className="relative inline-flex items-center justify-center">
              <Clock className="size-10 text-muted-foreground/30" />
              <div className="absolute -bottom-1.5 -right-1.5 rounded-full bg-card p-1">
                <UserPlus className="size-3.5 text-primary" />
              </div>
            </div>
            <p className="text-sm text-muted-foreground">No recent activity</p>
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
