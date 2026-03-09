import { useNavigate } from "@tanstack/react-router";
import type { CandidateStageItem } from "@/shared/api";
import { Badge } from "@/shared/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/ui/table";
import { getStageVariant, formatStage } from "@/shared/lib/stage-utils";

interface PositionCandidatesTableProps {
  candidates: Array<CandidateStageItem>;
}

export function PositionCandidatesTable({
  candidates,
}: PositionCandidatesTableProps) {
  const navigate = useNavigate();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Candidates</CardTitle>
      </CardHeader>
      <CardContent>
        {candidates.length > 0 ? (
          <div className="border border-border rounded-lg overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Stage</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {candidates.map((candidate) => (
                  <TableRow
                    key={candidate.candidate_id}
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() =>
                      navigate({
                        to: "/candidates/$candidateId",
                        params: {
                          candidateId: String(candidate.candidate_id),
                        },
                      })
                    }
                  >
                    <TableCell className="font-medium">
                      {candidate.candidate_name}
                    </TableCell>
                    <TableCell>{candidate.candidate_email}</TableCell>
                    <TableCell>
                      <Badge variant={getStageVariant(candidate.stage)}>
                        {formatStage(candidate.stage)}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        ) : (
          <p className="text-muted-foreground text-center py-8">
            No candidates linked to this position yet.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
