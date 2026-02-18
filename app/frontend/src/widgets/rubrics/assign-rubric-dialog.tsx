import { useState } from "react";
import { useRubricTemplates, useCreatePositionRubric } from "@/features/rubrics";
import { RubricEditor, type RubricStructure } from "./rubric-editor";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/shared/ui/dialog";
import { Button } from "@/shared/ui/button";
import { Label } from "@/shared/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/ui/select";

interface AssignRubricDialogProps {
  positionId: number;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function AssignRubricDialog({
  positionId,
  open,
  onOpenChange,
}: AssignRubricDialogProps) {
  const { data: templatesData } = useRubricTemplates();
  const templates = templatesData?.items ?? [];
  const createRubric = useCreatePositionRubric(positionId);

  const [mode, setMode] = useState<"template" | "custom">("template");
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>("");

  const handleClose = () => {
    setMode("template");
    setSelectedTemplateId("");
    onOpenChange(false);
  };

  const handleTemplateAssign = () => {
    if (!selectedTemplateId) return;
    createRubric.mutate(
      {
        path: { position_id: positionId },
        body: {
          source: "template",
          template_id: Number(selectedTemplateId),
        },
      },
      { onSuccess: handleClose },
    );
  };

  const handleCustomSubmit = (structure: RubricStructure) => {
    createRubric.mutate(
      {
        path: { position_id: positionId },
        body: {
          source: "custom",
          structure,
        },
      },
      { onSuccess: handleClose },
    );
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Assign Rubric</DialogTitle>
          <DialogDescription>
            Choose a template or create a custom rubric for this position.
          </DialogDescription>
        </DialogHeader>

        <div className="flex gap-2 mb-4">
          <Button
            variant={mode === "template" ? "default" : "outline"}
            size="sm"
            onClick={() => setMode("template")}
          >
            Use Template
          </Button>
          <Button
            variant={mode === "custom" ? "default" : "outline"}
            size="sm"
            onClick={() => setMode("custom")}
          >
            Create Custom
          </Button>
        </div>

        {mode === "template" ? (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Select Template</Label>
              <Select
                value={selectedTemplateId}
                onValueChange={setSelectedTemplateId}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Choose a template..." />
                </SelectTrigger>
                <SelectContent>
                  {templates.map((t) => (
                    <SelectItem key={t.id} value={String(t.id)}>
                      {t.name} ({t.category_count} categories)
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button
                onClick={handleTemplateAssign}
                disabled={!selectedTemplateId || createRubric.isPending}
              >
                {createRubric.isPending ? "Assigning..." : "Assign Template"}
              </Button>
            </div>
          </div>
        ) : (
          <RubricEditor
            onSubmit={handleCustomSubmit}
            onCancel={handleClose}
            isSubmitting={createRubric.isPending}
          />
        )}
      </DialogContent>
    </Dialog>
  );
}
