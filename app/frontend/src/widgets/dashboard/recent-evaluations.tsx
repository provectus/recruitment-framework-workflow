import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/shared/ui/card";
import { Badge } from "@/shared/ui/badge";

const STATUS_VARIANT = {
  Completed: "default",
  "In Progress": "secondary",
  Pending: "outline",
} as const;

const EVALUATIONS = [
  { candidate: "Alex Rivera", position: "Senior Backend Engineer", status: "Completed", date: "Feb 8, 2026" },
  { candidate: "Priya Sharma", position: "ML Engineer", status: "In Progress", date: "Feb 7, 2026" },
  { candidate: "Jordan Lee", position: "DevOps Engineer", status: "Pending", date: "Feb 6, 2026" },
  { candidate: "Maria Santos", position: "Frontend Engineer", status: "Completed", date: "Feb 5, 2026" },
] as const;

export function RecentEvaluations() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Evaluations</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {EVALUATIONS.map((evaluation) => (
          <div key={evaluation.candidate} className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <p className="text-sm font-medium truncate">{evaluation.candidate}</p>
              <p className="text-xs text-muted-foreground truncate">{evaluation.position}</p>
            </div>
            <div className="flex flex-col items-end gap-1 shrink-0">
              <Badge variant={STATUS_VARIANT[evaluation.status]}>
                {evaluation.status}
              </Badge>
              <span className="text-xs text-muted-foreground">{evaluation.date}</span>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
