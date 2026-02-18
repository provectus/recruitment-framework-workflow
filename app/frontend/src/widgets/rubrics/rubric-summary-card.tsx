import { useState } from "react";
import { AxiosError } from "axios";
import { FileText, MoreHorizontal, Plus } from "lucide-react";
import {
  usePositionRubric,
  useUpdatePositionRubric,
  useDeletePositionRubric,
} from "@/features/rubrics";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/shared/ui/dropdown-menu";
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
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/shared/ui/dialog";
import { RubricEditor, type RubricStructure } from "./rubric-editor";
import { AssignRubricDialog } from "./assign-rubric-dialog";
import { VersionHistoryDialog } from "./version-history-dialog";
import { SaveAsTemplateDialog } from "./save-as-template-dialog";

interface RubricSummaryCardProps {
  positionId: number;
}

export function RubricSummaryCard({ positionId }: RubricSummaryCardProps) {
  const { data: rubric, isLoading, error } = usePositionRubric(positionId);
  const updateRubric = useUpdatePositionRubric(positionId);
  const deleteRubric = useDeletePositionRubric(positionId);

  const [assignOpen, setAssignOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [saveTemplateOpen, setSaveTemplateOpen] = useState(false);

  const is404 =
    error instanceof AxiosError && error.response?.status === 404;
  const hasRubric = rubric && !error;
  const noRubric = is404 || (!error && !rubric);
  const hasError = !!error && !is404;

  const handleEditSubmit = (structure: RubricStructure) => {
    updateRubric.mutate(
      {
        path: { position_id: positionId },
        body: { structure },
      },
      { onSuccess: () => setEditOpen(false) },
    );
  };

  const handleDelete = () => {
    deleteRubric.mutate(
      { path: { position_id: positionId } },
      { onSuccess: () => setDeleteOpen(false) },
    );
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Decision Rubric</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-sm">Loading...</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">Decision Rubric</CardTitle>
            {hasRubric && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground">
                  v{rubric.version_number}
                </span>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon" className="h-7 w-7">
                      <MoreHorizontal className="h-4 w-4" />
                      <span className="sr-only">Rubric actions</span>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => setEditOpen(true)}>
                      Edit
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => setHistoryOpen(true)}>
                      View History
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => setSaveTemplateOpen(true)}>
                      Save as Template
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                      className="text-destructive focus:text-destructive"
                      onClick={() => setDeleteOpen(true)}
                    >
                      Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {hasError ? (
            <p className="text-destructive text-sm">Failed to load rubric.</p>
          ) : noRubric ? (
            <div className="flex flex-col items-center gap-3 py-4">
              <FileText className="h-8 w-8 text-muted-foreground" />
              <p className="text-muted-foreground text-sm">No rubric assigned</p>
              <Button variant="outline" onClick={() => setAssignOpen(true)}>
                <Plus className="h-4 w-4 mr-1" />
                Add Rubric
              </Button>
            </div>
          ) : hasRubric ? (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Source</span>
                <span>{rubric.source_template_name ?? "Custom"}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Categories</span>
                <span>
                  {(rubric.structure as { categories?: unknown[] })?.categories
                    ?.length ?? 0}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Created by</span>
                <span>{rubric.created_by}</span>
              </div>
            </div>
          ) : null}
        </CardContent>
      </Card>

      <AssignRubricDialog
        positionId={positionId}
        open={assignOpen}
        onOpenChange={setAssignOpen}
      />

      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Rubric</DialogTitle>
          </DialogHeader>
          {rubric && (
            <RubricEditor
              defaultValue={rubric.structure as unknown as RubricStructure}
              onSubmit={handleEditSubmit}
              onCancel={() => setEditOpen(false)}
              isSubmitting={updateRubric.isPending}
            />
          )}
        </DialogContent>
      </Dialog>

      <AlertDialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Remove rubric?</AlertDialogTitle>
            <AlertDialogDescription>
              All versions will be deleted. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleteRubric.isPending}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={deleteRubric.isPending}
            >
              {deleteRubric.isPending ? "Deleting..." : "Delete"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {rubric && (
        <VersionHistoryDialog
          positionId={positionId}
          currentVersionNumber={rubric.version_number}
          open={historyOpen}
          onOpenChange={setHistoryOpen}
        />
      )}

      <SaveAsTemplateDialog
        positionId={positionId}
        open={saveTemplateOpen}
        onOpenChange={setSaveTemplateOpen}
      />
    </>
  );
}
