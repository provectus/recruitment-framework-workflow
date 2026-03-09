import { useState } from "react";
import { useSaveRubricAsTemplate } from "@/features/rubrics";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/shared/ui/dialog";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";

interface SaveAsTemplateDialogProps {
  positionId: number;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function SaveAsTemplateDialog({
  positionId,
  open,
  onOpenChange,
}: SaveAsTemplateDialogProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [nameError, setNameError] = useState<string | null>(null);
  const saveAsTemplate = useSaveRubricAsTemplate();

  const handleClose = () => {
    setName("");
    setDescription("");
    setNameError(null);
    onOpenChange(false);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setNameError("Template name is required");
      return;
    }
    saveAsTemplate.mutate(
      {
        path: { position_id: positionId },
        body: {
          name: name.trim(),
          description: description.trim() || null,
        },
      },
      { onSuccess: handleClose },
    );
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Save as Template</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
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
              disabled={saveAsTemplate.isPending}
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
              disabled={saveAsTemplate.isPending}
            />
          </div>

          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              disabled={saveAsTemplate.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={saveAsTemplate.isPending}>
              {saveAsTemplate.isPending ? "Saving..." : "Save Template"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
