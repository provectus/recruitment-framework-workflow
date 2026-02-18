import { useState } from "react";
import { Loader2, MoreHorizontal } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import {
  getRubricTemplateApiRubricTemplatesTemplateIdGetOptions,
} from "@/shared/api/@tanstack/react-query.gen";
import type { RubricTemplateDetail } from "@/shared/api/types.gen";
import {
  useRubricTemplates,
  useDuplicateRubricTemplate,
  useArchiveRubricTemplate,
} from "@/features/rubrics";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
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
import { Button } from "@/shared/ui/button";
import { TemplateEditorDialog } from "./template-editor-dialog";

export function RubricTemplateTable() {
  const { data, isLoading } = useRubricTemplates();
  const templates = data?.items ?? [];

  const duplicateTemplate = useDuplicateRubricTemplate();
  const archiveTemplate = useArchiveRubricTemplate();
  const queryClient = useQueryClient();

  const [editTemplate, setEditTemplate] = useState<RubricTemplateDetail | null>(null);
  const [archiveTarget, setArchiveTarget] = useState<{
    id: number;
    name: string;
    position_count: number;
  } | null>(null);

  const handleEdit = async (id: number) => {
    const detail = await queryClient.fetchQuery(
      getRubricTemplateApiRubricTemplatesTemplateIdGetOptions({ path: { template_id: id } })
    );
    setEditTemplate(detail);
  };

  const handleDuplicate = (id: number) => {
    duplicateTemplate.mutate({ path: { template_id: id } });
  };

  const handleArchiveConfirm = () => {
    if (!archiveTarget) return;
    archiveTemplate.mutate(
      { path: { template_id: archiveTarget.id } },
      { onSuccess: () => setArchiveTarget(null) }
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (templates.length === 0) {
    return (
      <p className="text-muted-foreground text-sm">No rubric templates yet.</p>
    );
  }

  return (
    <>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Template Name</TableHead>
            <TableHead>Categories</TableHead>
            <TableHead>Created</TableHead>
            <TableHead className="w-[60px]">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {templates.map((template) => (
            <TableRow key={template.id}>
              <TableCell className="font-medium">{template.name}</TableCell>
              <TableCell>{template.category_count}</TableCell>
              <TableCell>
                {new Date(template.created_at).toLocaleDateString()}
              </TableCell>
              <TableCell>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon" className="h-8 w-8">
                      <MoreHorizontal className="h-4 w-4" />
                      <span className="sr-only">Open menu</span>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onSelect={() => handleEdit(template.id)}>
                      Edit
                    </DropdownMenuItem>
                    <DropdownMenuItem onSelect={() => handleDuplicate(template.id)}>
                      Duplicate
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onSelect={() =>
                        setArchiveTarget({
                          id: template.id,
                          name: template.name,
                          position_count: template.position_count,
                        })
                      }
                      className="text-destructive"
                    >
                      Archive
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <TemplateEditorDialog
        open={editTemplate !== null}
        onOpenChange={(open) => { if (!open) setEditTemplate(null); }}
        template={editTemplate ?? undefined}
      />

      <AlertDialog
        open={archiveTarget !== null}
        onOpenChange={(open) => { if (!open) setArchiveTarget(null); }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Archive {archiveTarget?.name}?</AlertDialogTitle>
            <AlertDialogDescription>
              {archiveTarget && archiveTarget.position_count > 0
                ? `${archiveTarget.position_count} position${archiveTarget.position_count === 1 ? "" : "s"} ${archiveTarget.position_count === 1 ? "was" : "were"} created from this template. Archiving will not affect existing position rubrics.`
                : "This template will no longer be available for new positions."}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleArchiveConfirm}
              disabled={archiveTemplate.isPending}
            >
              {archiveTemplate.isPending ? "Archiving..." : "Archive"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
