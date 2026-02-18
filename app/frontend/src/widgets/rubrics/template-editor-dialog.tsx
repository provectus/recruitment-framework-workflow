import { useState } from "react";
import { useCreateRubricTemplate, useUpdateRubricTemplate } from "@/features/rubrics";
import { RubricEditor, type RubricStructure } from "./rubric-editor";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/shared/ui/dialog";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";

interface ExistingTemplate {
  id: number;
  name: string;
  description: string | null;
  structure: Record<string, unknown>;
}

interface TemplateEditorDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  template?: ExistingTemplate;
}

function TemplateEditorDialogContent({
  onOpenChange,
  template,
}: Omit<TemplateEditorDialogProps, "open">) {
  const createTemplate = useCreateRubricTemplate();
  const updateTemplate = useUpdateRubricTemplate();

  const [name, setName] = useState(template?.name ?? "");
  const [description, setDescription] = useState(template?.description ?? "");
  const [nameError, setNameError] = useState<string | null>(null);

  const isEditMode = template !== undefined;
  const isPending = isEditMode ? updateTemplate.isPending : createTemplate.isPending;

  const handleClose = () => {
    onOpenChange(false);
  };

  const handleSubmit = (structure: RubricStructure) => {
    if (!name.trim()) {
      setNameError("Template name is required");
      return;
    }

    if (isEditMode) {
      updateTemplate.mutate(
        {
          path: { template_id: template.id },
          body: {
            name: name.trim(),
            description: description.trim() || null,
            structure,
          },
        },
        { onSuccess: () => { handleClose(); } }
      );
    } else {
      createTemplate.mutate(
        {
          body: {
            name: name.trim(),
            description: description.trim() || null,
            structure,
          },
        },
        { onSuccess: () => { handleClose(); } }
      );
    }
  };

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="template-name">
          Template Name <span className="text-destructive">*</span>
        </Label>
        <Input
          id="template-name"
          placeholder="e.g. Senior Backend Engineer"
          value={name}
          onChange={(e) => {
            setName(e.target.value);
            if (nameError) setNameError(null);
          }}
          disabled={isPending}
        />
        {nameError && (
          <p className="text-destructive text-sm">{nameError}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="template-description">Description</Label>
        <Input
          id="template-description"
          placeholder="Optional description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          disabled={isPending}
        />
      </div>

      <div className="border-t pt-4">
        <RubricEditor
          defaultValue={template?.structure as RubricStructure | undefined}
          onSubmit={handleSubmit}
          onCancel={handleClose}
          isSubmitting={isPending}
        />
      </div>
    </div>
  );
}

export function TemplateEditorDialog({
  open,
  onOpenChange,
  template,
}: TemplateEditorDialogProps) {
  const isEditMode = template !== undefined;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {isEditMode ? "Edit Rubric Template" : "Create Rubric Template"}
          </DialogTitle>
        </DialogHeader>
        <TemplateEditorDialogContent
          key={template?.id ?? "create"}
          onOpenChange={onOpenChange}
          template={template}
        />
      </DialogContent>
    </Dialog>
  );
}
