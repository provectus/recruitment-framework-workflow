import { useState } from "react";
import { Loader2, Pencil, X, Check } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod/v4";
import { useUpdateCandidate } from "@/features/candidates";
import { Card, CardContent, CardFooter } from "@/shared/ui/card";
import { Input } from "@/shared/ui/input";
import { Button } from "@/shared/ui/button";
import { formatDate } from "@/shared/lib/format";

const fieldSchema = z.object({
  full_name: z.string().min(1, "Full name is required"),
  email: z.email("Please enter a valid email"),
});

type FieldName = keyof z.infer<typeof fieldSchema>;

interface CandidateInfoCardProps {
  candidateId: number;
  fullName: string;
  email: string;
  createdAt: string;
  updatedAt: string;
}

export function CandidateInfoCard({
  candidateId,
  fullName,
  email,
  createdAt,
  updatedAt,
}: CandidateInfoCardProps) {
  const [editingField, setEditingField] = useState<FieldName | null>(null);
  const updateCandidate = useUpdateCandidate(candidateId);

  const form = useForm<z.infer<typeof fieldSchema>>({
    resolver: zodResolver(fieldSchema),
    defaultValues: { full_name: fullName, email },
  });

  const startEditing = (field: FieldName) => {
    form.reset({ full_name: fullName, email });
    setEditingField(field);
  };

  const cancelEditing = () => {
    form.clearErrors();
    setEditingField(null);
  };

  const saveField = async (field: FieldName) => {
    const valid = await form.trigger(field);
    if (!valid) return;

    const value = form.getValues(field);
    const currentValue = field === "full_name" ? fullName : email;
    if (value === currentValue) {
      setEditingField(null);
      return;
    }

    try {
      await updateCandidate.mutateAsync({
        path: { candidate_id: candidateId },
        body: { [field]: value },
      });
      setEditingField(null);
    } catch (err: unknown) {
      if (err && typeof err === "object" && "response" in err) {
        const axiosError = err as { response?: { status?: number } };
        if (axiosError.response?.status === 409) {
          form.setError("email", {
            message: "A candidate with this email already exists.",
          });
        }
      }
    }
  };

  const fields: { name: FieldName; label: string; value: string }[] = [
    { name: "full_name", label: "Full Name", value: fullName },
    { name: "email", label: "Email", value: email },
  ];

  return (
    <Card>
      <CardContent className="pt-6 pb-0">
        <div className="divide-y divide-border">
          {fields.map(({ name, label, value }) => (
            <div key={name} className="group flex items-center gap-4 py-3 first:pt-0">
              <span className="w-24 shrink-0 text-sm text-muted-foreground">
                {label}
              </span>

              {editingField === name ? (
                <div className="flex flex-1 items-center gap-2">
                  <Input
                    {...form.register(name)}
                    autoFocus
                    className="h-8"
                    disabled={updateCandidate.isPending}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        saveField(name);
                      }
                      if (e.key === "Escape") cancelEditing();
                    }}
                  />
                  {updateCandidate.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                  ) : (
                    <>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7"
                        onClick={() => saveField(name)}
                      >
                        <Check className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7"
                        onClick={cancelEditing}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </>
                  )}
                </div>
              ) : (
                <div className="flex flex-1 items-center justify-between">
                  {name === "email" ? (
                    <a
                      href={`mailto:${value}`}
                      className="text-sm hover:underline"
                    >
                      {value}
                    </a>
                  ) : (
                    <span className="text-sm">{value}</span>
                  )}
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity"
                    onClick={() => startEditing(name)}
                  >
                    <Pencil className="h-3.5 w-3.5 text-muted-foreground" />
                  </Button>
                </div>
              )}

              {editingField === name && form.formState.errors[name] && (
                <p className="text-sm text-destructive">
                  {form.formState.errors[name]?.message}
                </p>
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
