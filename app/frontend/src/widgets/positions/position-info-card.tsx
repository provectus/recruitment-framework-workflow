import { useState } from "react";
import { Loader2, Pencil, X, Check } from "lucide-react";
import { useUpdatePosition, useUsers } from "@/features/positions";
import { useTeams } from "@/features/settings";
import { Card, CardContent, CardFooter } from "@/shared/ui/card";
import { Input } from "@/shared/ui/input";
import { Textarea } from "@/shared/ui/textarea";
import { Button } from "@/shared/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/ui/select";
import { formatDate } from "@/shared/lib/format";
import { formatStatus } from "@/shared/lib/stage-utils";

type EditableField =
  | "title"
  | "requirements"
  | "evaluation_instructions"
  | "team_id"
  | "hiring_manager_id"
  | "status";

const STATUS_OPTIONS = [
  { value: "open", label: "Open" },
  { value: "on_hold", label: "On Hold" },
  { value: "closed", label: "Closed" },
];

interface PositionInfoCardProps {
  positionId: number;
  title: string;
  requirements: string | null;
  evaluationInstructions: string | null;
  teamId: number;
  teamName: string;
  hiringManagerId: number;
  hiringManagerName: string;
  status: string;
  createdAt: string;
  updatedAt: string;
}

export function PositionInfoCard({
  positionId,
  title,
  requirements,
  evaluationInstructions,
  teamId,
  teamName,
  hiringManagerId,
  hiringManagerName,
  status,
  createdAt,
  updatedAt,
}: PositionInfoCardProps) {
  const [editingField, setEditingField] = useState<EditableField | null>(null);
  const [editValue, setEditValue] = useState("");
  const updatePosition = useUpdatePosition(positionId);
  const { data: teams } = useTeams();
  const { data: users } = useUsers();

  const startEditing = (field: EditableField) => {
    if (field === "title") setEditValue(title);
    else if (field === "requirements") setEditValue(requirements ?? "");
    else if (field === "evaluation_instructions") setEditValue(evaluationInstructions ?? "");
    setEditingField(field);
  };

  const cancelEditing = () => setEditingField(null);

  const saveTextField = async (field: "title" | "requirements" | "evaluation_instructions") => {
    const currentValue = field === "title" ? title : field === "requirements" ? (requirements ?? "") : (evaluationInstructions ?? "");
    if (editValue === currentValue) {
      setEditingField(null);
      return;
    }
    if (field === "title" && editValue.trim() === "") return;

    try {
      await updatePosition.mutateAsync({
        path: { position_id: positionId },
        body: { [field]: editValue },
      });
      setEditingField(null);
    } catch (error) {
      console.error("Failed to update position:", error);
    }
  };

  const saveSelectField = async (
    field: "team_id" | "hiring_manager_id" | "status",
    value: string,
  ) => {
    const payload =
      field === "status"
        ? { [field]: value }
        : { [field]: Number(value) };

    try {
      await updatePosition.mutateAsync({
        path: { position_id: positionId },
        body: payload,
      });
      setEditingField(null);
    } catch (error) {
      console.error("Failed to update position:", error);
    }
  };

  const fields: {
    name: EditableField;
    label: string;
    value: string;
    type: "text" | "textarea" | "select";
  }[] = [
    { name: "title", label: "Title", value: title, type: "text" },
    {
      name: "requirements",
      label: "Requirements",
      value: requirements ?? "",
      type: "textarea",
    },
    {
      name: "evaluation_instructions",
      label: "Evaluation Instructions",
      value: evaluationInstructions ?? "",
      type: "textarea",
    },
    { name: "team_id", label: "Team", value: teamName, type: "select" },
    {
      name: "hiring_manager_id",
      label: "Hiring Manager",
      value: hiringManagerName,
      type: "select",
    },
    {
      name: "status",
      label: "Status",
      value: formatStatus(status),
      type: "select",
    },
  ];

  return (
    <Card>
      <CardContent className="pt-6 pb-0">
        <div className="divide-y divide-border">
          {fields.map(({ name, label, value, type }) => (
            <div
              key={name}
              className="group flex items-start gap-4 py-3 first:pt-0"
            >
              <span className="w-36 shrink-0 pt-1 text-sm text-muted-foreground">
                {label}
              </span>

              {editingField === name ? (
                <EditField
                  fieldName={name}
                  fieldType={type}
                  editValue={editValue}
                  setEditValue={setEditValue}
                  isPending={updatePosition.isPending}
                  onSave={() =>
                    saveTextField(name as "title" | "requirements" | "evaluation_instructions")
                  }
                  onCancel={cancelEditing}
                  onSelectChange={(val) =>
                    saveSelectField(
                      name as "team_id" | "hiring_manager_id" | "status",
                      val,
                    )
                  }
                  teams={teams}
                  users={users}
                  currentTeamId={teamId}
                  currentManagerId={hiringManagerId}
                  currentStatus={status}
                />
              ) : (
                <div className="flex flex-1 items-center justify-between min-h-[28px]">
                  {value ? (
                    <span
                      className={`text-sm ${name === "requirements" ? "whitespace-pre-wrap" : ""}`}
                    >
                      {value}
                    </span>
                  ) : (
                    <span className="text-sm text-muted-foreground">
                      Not specified
                    </span>
                  )}
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
                    onClick={() => startEditing(name)}
                  >
                    <Pencil className="h-3.5 w-3.5 text-muted-foreground" />
                  </Button>
                </div>
              )}
            </div>
          ))}
        </div>
      </CardContent>
      <CardFooter className="text-xs text-muted-foreground/70 pt-4">
        Created {formatDate(createdAt)} &middot; Updated{" "}
        {formatDate(updatedAt)}
      </CardFooter>
    </Card>
  );
}

function EditField({
  fieldName,
  fieldType,
  editValue,
  setEditValue,
  isPending,
  onSave,
  onCancel,
  onSelectChange,
  teams,
  users,
  currentTeamId,
  currentManagerId,
  currentStatus,
}: {
  fieldName: EditableField;
  fieldType: "text" | "textarea" | "select";
  editValue: string;
  setEditValue: (v: string) => void;
  isPending: boolean;
  onSave: () => void;
  onCancel: () => void;
  onSelectChange: (value: string) => void;
  teams: Array<{ id: number; name: string }> | undefined;
  users: Array<{ id: number; full_name: string; email: string }> | undefined;
  currentTeamId: number;
  currentManagerId: number;
  currentStatus: string;
}) {
  if (fieldType === "select") {
    if (fieldName === "team_id") {
      return (
        <SelectEditor
          value={String(currentTeamId)}
          options={(teams ?? []).map((t) => ({
            value: String(t.id),
            label: t.name,
          }))}
          isPending={isPending}
          onChange={onSelectChange}
        />
      );
    }
    if (fieldName === "hiring_manager_id") {
      return (
        <SelectEditor
          value={String(currentManagerId)}
          options={(users ?? []).map((u) => ({
            value: String(u.id),
            label: u.full_name || u.email,
          }))}
          isPending={isPending}
          onChange={onSelectChange}
        />
      );
    }
    return (
      <SelectEditor
        value={currentStatus}
        options={STATUS_OPTIONS}
        isPending={isPending}
        onChange={onSelectChange}
      />
    );
  }

  if (fieldType === "textarea") {
    return (
      <div className="flex flex-1 items-start gap-2">
        <Textarea
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          autoFocus
          rows={3}
          className="min-h-[80px]"
          disabled={isPending}
          onKeyDown={(e) => {
            if (e.key === "Escape") onCancel();
          }}
        />
        {isPending ? (
          <Loader2 className="mt-2 h-4 w-4 animate-spin text-muted-foreground" />
        ) : (
          <div className="flex flex-col gap-1">
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={onSave}
            >
              <Check className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={onCancel}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="flex flex-1 items-center gap-2">
      <Input
        value={editValue}
        onChange={(e) => setEditValue(e.target.value)}
        autoFocus
        className="h-8"
        disabled={isPending}
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            e.preventDefault();
            onSave();
          }
          if (e.key === "Escape") onCancel();
        }}
      />
      {isPending ? (
        <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
      ) : (
        <>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={onSave}
          >
            <Check className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={onCancel}
          >
            <X className="h-4 w-4" />
          </Button>
        </>
      )}
    </div>
  );
}

function SelectEditor({
  value,
  options,
  isPending,
  onChange,
}: {
  value: string;
  options: Array<{ value: string; label: string }>;
  isPending: boolean;
  onChange: (value: string) => void;
}) {
  return (
    <div className="flex flex-1 items-center gap-2">
      <Select value={value} onValueChange={onChange} disabled={isPending}>
        <SelectTrigger className="h-8 w-[200px]">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {options.map((opt) => (
            <SelectItem key={opt.value} value={opt.value}>
              {opt.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {isPending && (
        <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
      )}
    </div>
  );
}
