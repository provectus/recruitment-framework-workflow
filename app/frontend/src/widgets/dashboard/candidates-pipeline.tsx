import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/shared/ui/card";

const PIPELINE_STAGES = [
  { name: "Screening", count: 12, color: "bg-blue-500" },
  { name: "Interview", count: 8, color: "bg-amber-500" },
  { name: "Technical", count: 5, color: "bg-violet-500" },
  { name: "Offer", count: 3, color: "bg-emerald-500" },
] as const;

export function CandidatesPipeline() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Candidates Pipeline</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {PIPELINE_STAGES.map((stage) => (
          <div key={stage.name} className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className={`h-2 w-2 rounded-full ${stage.color}`} />
              <span className="text-sm">{stage.name}</span>
            </div>
            <span className="text-sm font-medium">{stage.count}</span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
