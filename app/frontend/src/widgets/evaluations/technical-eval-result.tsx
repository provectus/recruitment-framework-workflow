import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { Progress } from "@/shared/ui/progress";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/ui/table";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/shared/ui/collapsible";
import { cn } from "@/shared/lib/utils";

interface CriterionScore {
  criterion_name: string;
  category_name: string;
  score: number;
  max_score: number;
  weight: number;
  evidence: string;
  reasoning: string;
}

interface TechnicalEvalResult {
  criteria_scores: CriterionScore[];
  weighted_total: number;
  strengths_summary: string[];
  improvement_areas: string[];
}

function scoreColorClass(score: number, maxScore: number): string {
  const ratio = score / maxScore;
  if (ratio <= 0.2) return "bg-red-500";
  if (ratio <= 0.4) return "bg-orange-500";
  if (ratio <= 0.6) return "bg-yellow-500";
  if (ratio <= 0.8) return "bg-lime-500";
  return "bg-green-500";
}

function ScoreIndicator({
  score,
  maxScore,
}: {
  score: number;
  maxScore: number;
}) {
  const dotColor = scoreColorClass(score, maxScore);
  return (
    <div className="flex items-center gap-2">
      <span
        className={cn("inline-block size-2.5 rounded-full shrink-0", dotColor)}
      />
      <span className="text-sm font-medium tabular-nums">
        {score}/{maxScore}
      </span>
    </div>
  );
}

function ExpandableCell({ content }: { content: string }) {
  const [open, setOpen] = useState(false);
  const isLong = content.length > 80;

  if (!isLong) {
    return (
      <span className="text-sm text-muted-foreground whitespace-normal">
        {content}
      </span>
    );
  }

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      {!open && (
        <div className="line-clamp-2 text-sm text-muted-foreground whitespace-normal">
          {content}
        </div>
      )}
      <CollapsibleContent>
        <div className="text-sm text-muted-foreground whitespace-normal">
          {content}
        </div>
      </CollapsibleContent>
      <CollapsibleTrigger className="mt-1 flex items-center gap-0.5 text-xs text-muted-foreground hover:text-foreground transition-colors">
        {open ? (
          <>
            <ChevronDown className="size-3" /> Less
          </>
        ) : (
          <>
            <ChevronRight className="size-3" /> More
          </>
        )}
      </CollapsibleTrigger>
    </Collapsible>
  );
}

function BulletList({
  items,
  className,
}: {
  items: string[];
  className?: string;
}) {
  return (
    <ul className={`space-y-1 ${className ?? ""}`}>
      {items.map((item, idx) => (
        <li key={idx} className="flex items-start gap-2 text-sm">
          <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-current opacity-50" />
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">
      {children}
    </p>
  );
}

export function TechnicalEvalResult({
  result,
}: {
  result: TechnicalEvalResult;
}) {
  const maxPossible = 5;
  const totalPercent = (result.weighted_total / maxPossible) * 100;

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-border bg-muted/30 px-5 py-4">
        <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
          Weighted Total Score
        </p>
        <div className="flex items-end gap-3 mb-2">
          <span className="text-3xl font-bold tabular-nums">
            {result.weighted_total.toFixed(1)}
          </span>
          <span className="text-lg text-muted-foreground mb-0.5">
            / {maxPossible.toFixed(1)}
          </span>
        </div>
        <Progress value={totalPercent} className="h-2" />
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="bg-green-50/50 rounded-lg p-3">
          <SectionLabel>Strengths</SectionLabel>
          <BulletList
            items={result.strengths_summary}
            className="text-green-800 dark:text-green-400"
          />
        </div>
        <div className="bg-amber-50/50 rounded-lg p-3">
          <SectionLabel>Improvement Areas</SectionLabel>
          <BulletList
            items={result.improvement_areas}
            className="text-amber-800 dark:text-amber-400"
          />
        </div>
      </div>

      <div>
        <SectionLabel>Criteria Scores</SectionLabel>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Category</TableHead>
              <TableHead>Criterion</TableHead>
              <TableHead className="w-24">Score</TableHead>
              <TableHead className="w-16">Weight</TableHead>
              <TableHead>Evidence</TableHead>
              <TableHead>Reasoning</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {result.criteria_scores.map((row, idx) => {
              const prevCategory =
                idx > 0
                  ? result.criteria_scores[idx - 1].category_name
                  : null;
              const isNewGroup =
                prevCategory !== null && row.category_name !== prevCategory;
              return (
                <TableRow
                  key={idx}
                  className={cn(isNewGroup && "border-t-2 border-border bg-muted/30")}
                >
                  <TableCell className="text-muted-foreground">
                    {row.category_name}
                  </TableCell>
                  <TableCell className="font-medium whitespace-normal">
                    {row.criterion_name}
                  </TableCell>
                  <TableCell>
                    <ScoreIndicator score={row.score} maxScore={row.max_score} />
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {row.weight}%
                  </TableCell>
                  <TableCell className="min-w-40 max-w-56">
                    <ExpandableCell content={row.evidence} />
                  </TableCell>
                  <TableCell className="min-w-40 max-w-56">
                    <ExpandableCell content={row.reasoning} />
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
