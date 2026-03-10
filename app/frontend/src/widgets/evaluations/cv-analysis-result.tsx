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

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">
      {children}
    </p>
  );
}

export function CvAnalysisResult({ result }: { result: CvAnalysisResult }) {
  return (
    <div className="space-y-6">
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
            {result.skills_match.map((item, idx) => (
              <TableRow key={idx}>
                <TableCell className="font-medium">{item.skill}</TableCell>
                <TableCell>
                  {item.present ? (
                    <Badge className="gap-1 bg-green-100 text-green-800 border-green-200 hover:bg-green-100">
                      <CheckCircle2 className="size-3" />
                      Present
                    </Badge>
                  ) : (
                    <Badge className="gap-1 bg-red-100 text-red-800 border-red-200 hover:bg-red-100">
                      <XCircle className="size-3" />
                      Absent
                    </Badge>
                  )}
                </TableCell>
                <TableCell className="text-muted-foreground whitespace-normal">
                  {item.notes}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <div>
        <SectionLabel>Experience Relevance</SectionLabel>
        <p className="text-sm leading-relaxed">{result.experience_relevance}</p>
      </div>

      <div>
        <SectionLabel>Education</SectionLabel>
        <p className="text-sm leading-relaxed">{result.education}</p>
      </div>

      <div>
        <SectionLabel>Signals &amp; Red Flags</SectionLabel>
        <p className="text-sm leading-relaxed text-amber-800 dark:text-amber-400">
          {result.signals_and_red_flags}
        </p>
      </div>

      <div>
        <SectionLabel>Overall Fit</SectionLabel>
        <p className="text-sm leading-relaxed font-medium">{result.overall_fit}</p>
      </div>
    </div>
  );
}
