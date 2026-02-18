import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ChevronLeft } from "lucide-react";
import {
  useRubricVersions,
  useRevertRubricVersion,
} from "@/features/rubrics";
import {
  getRubricVersionApiPositionsPositionIdRubricVersionsVersionNumberGetOptions,
} from "@/shared/api/@tanstack/react-query.gen";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/shared/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/shared/ui/alert-dialog";
import { Button } from "@/shared/ui/button";
import { Badge } from "@/shared/ui/badge";

interface VersionHistoryDialogProps {
  positionId: number;
  currentVersionNumber: number;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface VersionDetailViewProps {
  positionId: number;
  versionNumber: number;
  currentVersionNumber: number;
  onBack: () => void;
  onRevertSuccess: () => void;
}

function VersionDetailView({
  positionId,
  versionNumber,
  currentVersionNumber,
  onBack,
  onRevertSuccess,
}: VersionDetailViewProps) {
  const [confirmOpen, setConfirmOpen] = useState(false);
  const revert = useRevertRubricVersion(positionId);

  const { data: version, isLoading } = useQuery(
    getRubricVersionApiPositionsPositionIdRubricVersionsVersionNumberGetOptions({
      path: { position_id: positionId, version_number: versionNumber },
    }),
  );

  const isCurrent = versionNumber === currentVersionNumber;

  const handleRevert = () => {
    revert.mutate(
      { path: { position_id: positionId, version_number: versionNumber } },
      {
        onSuccess: () => {
          setConfirmOpen(false);
          onRevertSuccess();
        },
      },
    );
  };

  const structure = version?.structure as { categories?: Array<{ name: string; criteria?: unknown[] }> } | undefined;

  return (
    <>
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={onBack}>
            <ChevronLeft className="h-4 w-4" />
            Back to list
          </Button>
        </div>

        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium">Version {versionNumber}</p>
            {version && (
              <p className="text-sm text-muted-foreground">
                by {version.created_by} &middot; {new Date(version.created_at).toLocaleString()}
              </p>
            )}
          </div>
          {isCurrent && <Badge variant="secondary">Current</Badge>}
        </div>

        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading...</p>
        ) : structure?.categories ? (
          <div className="space-y-3 border rounded-md p-4 bg-muted/30">
            {structure.categories.map((category, idx) => (
              <div key={idx} className="space-y-1">
                <p className="text-sm font-medium">{category.name}</p>
                {Array.isArray(category.criteria) && (
                  <ul className="pl-4 space-y-0.5">
                    {(category.criteria as Array<{ name: string }>).map((criterion, cIdx) => (
                      <li key={cIdx} className="text-sm text-muted-foreground">
                        {criterion.name}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>
        ) : null}

        {!isCurrent && (
          <div className="flex justify-end">
            <Button
              variant="outline"
              onClick={() => setConfirmOpen(true)}
              disabled={revert.isPending}
            >
              Revert to this version
            </Button>
          </div>
        )}
      </div>

      <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Revert to version {versionNumber}?</AlertDialogTitle>
            <AlertDialogDescription>
              The current rubric will be replaced with this version. A new version entry will be created.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={revert.isPending}>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleRevert} disabled={revert.isPending}>
              {revert.isPending ? "Reverting..." : "Revert"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}

export function VersionHistoryDialog({
  positionId,
  currentVersionNumber,
  open,
  onOpenChange,
}: VersionHistoryDialogProps) {
  const [selectedVersion, setSelectedVersion] = useState<number | null>(null);
  const { data: versionsData, isLoading } = useRubricVersions(positionId);

  const versions = versionsData?.items ?? [];

  const handleClose = () => {
    setSelectedVersion(null);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Version History</DialogTitle>
        </DialogHeader>

        {selectedVersion !== null ? (
          <VersionDetailView
            positionId={positionId}
            versionNumber={selectedVersion}
            currentVersionNumber={currentVersionNumber}
            onBack={() => setSelectedVersion(null)}
            onRevertSuccess={handleClose}
          />
        ) : isLoading ? (
          <p className="text-sm text-muted-foreground">Loading versions...</p>
        ) : versions.length === 0 ? (
          <p className="text-sm text-muted-foreground">No versions found.</p>
        ) : (
          <ul className="space-y-2">
            {versions.map((v) => (
              <li key={v.version_number}>
                <button
                  className="w-full text-left rounded-md border px-4 py-3 hover:bg-muted/50 transition-colors"
                  onClick={() => setSelectedVersion(v.version_number)}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="font-medium text-sm">Version {v.version_number}</span>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        by {v.created_by} &middot; {new Date(v.created_at).toLocaleString()}
                      </p>
                    </div>
                    {v.version_number === currentVersionNumber && (
                      <Badge variant="secondary" className="ml-2">Current</Badge>
                    )}
                  </div>
                </button>
              </li>
            ))}
          </ul>
        )}
      </DialogContent>
    </Dialog>
  );
}
