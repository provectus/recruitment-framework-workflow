import { useState } from "react";
import { CheckCircle2, XCircle } from "lucide-react";
import { Badge } from "@/shared/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/ui/table";
import { SectionLabel } from "./evaluation-primitives";

interface SkillMatch {
  skill: string;
  present: boolean;
  notes: string;
}

interface CvAnalysisResult {
  skills_match: SkillMatch[];
  experience_relevance: string;
  education: string;
  signals_and_red_flags: string;
  overall_fit: string;
}

function TruncatedText({ text, maxLen = 80 }: { text: string; maxLen?: number }) {
  const [expanded, setExpanded] = useState(false);
  if (text.length <= maxLen) return <span>{text}</span>;
  return (
    <span>
      {expanded ? text : text.slice(0, maxLen) + "…"}
      <button
        onClick={() => setExpanded(!expanded)}
        className="ml-1 text-xs text-primary hover:underline"
      >
        {expanded ? "Less" : "More"}
      </button>
    </span>
  );
}

export function CvAnalysisResult({ result }: { result: CvAnalysisResult }) {
  return (
    <div className="space-y-6">
      <div>
        <SectionLabel>Overall Fit</SectionLabel>
        <p className="text-sm leading-relaxed font-medium">{result.overall_fit ?? ""}</p>
      </div>

      <div>
        <SectionLabel>Skills Match</SectionLabel>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Skill</TableHead>
              <TableHead className="w-28">Status</TableHead>
              <TableHead>Notes</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {(result.skills_match ?? []).map((item, idx) => (
              <TableRow key={idx}>
                <TableCell className="py-2 font-medium">{item.skill}</TableCell>
                <TableCell className="py-2">
                  {item.present ? (
                    <Badge className="gap-1 text-xs px-1.5 py-0 bg-green-100 text-green-800 border-green-200 hover:bg-green-100">
                      <CheckCircle2 className="size-3" />
                      Present
                    </Badge>
                  ) : (
                    <Badge className="gap-1 text-xs px-1.5 py-0 bg-red-100 text-red-800 border-red-200 hover:bg-red-100">
                      <XCircle className="size-3" />
                      Absent
                    </Badge>
                  )}
                </TableCell>
                <TableCell className="py-2 text-muted-foreground whitespace-normal">
                  <TruncatedText text={item.notes} />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <div>
        <SectionLabel>Experience Relevance</SectionLabel>
        <p className="text-sm leading-relaxed">{result.experience_relevance ?? ""}</p>
      </div>

      <div>
        <SectionLabel>Education</SectionLabel>
        <p className="text-sm leading-relaxed">{result.education ?? ""}</p>
      </div>

      <div>
        <SectionLabel>Signals &amp; Red Flags</SectionLabel>
        <p className="text-sm leading-relaxed text-amber-800 dark:text-amber-400">
          {result.signals_and_red_flags ?? ""}
        </p>
      </div>
    </div>
  );
}
