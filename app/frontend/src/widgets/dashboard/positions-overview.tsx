import { useNavigate } from "@tanstack/react-router";
import { Briefcase } from "lucide-react";
import { useDashboardStats } from "@/features/dashboard";
import { formatStatus, getStatusVariant } from "@/shared/lib/stage-utils";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/shared/ui/card";
import { Skeleton } from "@/shared/ui/skeleton";

export function PositionsOverview() {
  const { data, isLoading } = useDashboardStats();
  const navigate = useNavigate();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Open Positions</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading ? (
          <>
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </>
        ) : data && data.positions_summary.length > 0 ? (
          data.positions_summary.map((position) => (
            <div
              key={position.id}
              className="flex items-start justify-between gap-2"
            >
              <div className="min-w-0">
                <p className="text-sm font-medium truncate">
                  {position.title}
                </p>
                <p className="text-xs text-muted-foreground truncate">
                  {position.team_name}
                </p>
              </div>
              <div className="flex flex-col items-end gap-1 shrink-0">
                <Badge variant={getStatusVariant(position.status)}>
                  {formatStatus(position.status)}
                </Badge>
                <span className="text-xs text-muted-foreground">
                  {position.candidate_count} candidate{position.candidate_count !== 1 ? "s" : ""}
                </span>
              </div>
            </div>
          ))
        ) : (
          <div className="flex flex-col items-center gap-2 py-4">
            <Briefcase className="h-8 w-8 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">No positions yet</p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate({ to: "/positions" })}
            >
              Create Position
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
