import { Badge } from "@/shared/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/shared/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/ui/table";
import { useDocuments } from "@/features/documents";
import { formatDateTime } from "@/shared/lib/format";

interface CvVersionHistoryProps {
  candidateId: number;
  candidatePositionId: number;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onVersionClick: (documentId: number) => void;
}

export function CvVersionHistory({
  candidateId,
  candidatePositionId,
  open,
  onOpenChange,
  onVersionClick,
}: CvVersionHistoryProps) {
  const { data: documents, isLoading } = useDocuments(candidateId, {
    candidate_position_id: candidatePositionId,
    type: "cv",
  });

  const versions = documents || [];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>CV Version History</DialogTitle>
        </DialogHeader>
        {isLoading ? (
          <div className="flex items-center justify-center py-8 text-sm text-muted-foreground">
            Loading versions...
          </div>
        ) : versions.length === 0 ? (
          <div className="flex items-center justify-center py-8 text-sm text-muted-foreground">
            No versions found.
          </div>
        ) : (
          <div className="border rounded-lg">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Filename</TableHead>
                  <TableHead>Upload Date</TableHead>
                  <TableHead>Uploader</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {versions.map((version, index) => (
                  <TableRow
                    key={version.id}
                    onClick={() => onVersionClick(version.id)}
                    className="cursor-pointer"
                  >
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        {version.file_name || "Untitled document"}
                        {index === 0 && (
                          <Badge variant="default" className="bg-green-600">
                            Current
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {formatDateTime(version.created_at)}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {version.uploaded_by_name || "Unknown"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
