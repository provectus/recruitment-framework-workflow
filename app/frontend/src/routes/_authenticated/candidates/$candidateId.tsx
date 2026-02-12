"use client";

import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Loader2, Archive, Trash2 } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod/v4";
import { useCandidate, useUpdateCandidate, useAddToPosition, useRemoveFromPosition, useUpdateStage, useArchiveCandidate, STAGE_LABELS, getValidNextStages } from "@/features/candidates";
import { usePositions } from "@/features/positions";
import { Button } from "@/shared/ui/button";
import { Badge } from "@/shared/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/shared/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/ui/table";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/shared/ui/form";
import { Input } from "@/shared/ui/input";
import { Skeleton } from "@/shared/ui/skeleton";

export const Route = createFileRoute("/_authenticated/candidates/$candidateId")({
  component: CandidateDetailPage,
});

const candidateSchema = z.object({
  full_name: z.string().min(1, "Full name is required"),
  email: z.email("Please enter a valid email"),
});

type CandidateFormData = z.infer<typeof candidateSchema>;

function CandidateDetailPage() {
  const navigate = useNavigate();
  const { candidateId } = Route.useParams();
  const candidateIdNum = Number(candidateId);
  const { data: candidate, isLoading, error } = useCandidate(candidateIdNum);
  const { data: positionsData } = usePositions();
  const updateCandidate = useUpdateCandidate(candidateIdNum);
  const addToPosition = useAddToPosition(candidateIdNum);
  const removeFromPosition = useRemoveFromPosition(candidateIdNum);
  const updateStageMutation = useUpdateStage(candidateIdNum);
  const archiveCandidate = useArchiveCandidate(candidateIdNum);

  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [selectedPositionId, setSelectedPositionId] = useState<string>("");
  const [addError, setAddError] = useState<string>("");

  const [removeDialogOpen, setRemoveDialogOpen] = useState(false);
  const [positionToRemove, setPositionToRemove] = useState<{ id: number; title: string } | null>(null);

  const [archiveDialogOpen, setArchiveDialogOpen] = useState(false);
  const [updatingStage, setUpdatingStage] = useState<number | null>(null);

  const form = useForm<CandidateFormData>({
    resolver: zodResolver(candidateSchema),
    defaultValues: {
      full_name: "",
      email: "",
    },
  });

  useEffect(() => {
    if (candidate) {
      form.reset({
        full_name: candidate.full_name,
        email: candidate.email,
      });
    }
  }, [candidate, form]);

  const onSubmit = async (data: CandidateFormData) => {
    const changedFields: Partial<CandidateFormData> = {};
    if (data.full_name !== candidate?.full_name) {
      changedFields.full_name = data.full_name;
    }
    if (data.email !== candidate?.email) {
      changedFields.email = data.email;
    }

    if (Object.keys(changedFields).length === 0) return;

    try {
      const result = await updateCandidate.mutateAsync({
        path: { candidate_id: candidateIdNum },
        body: changedFields,
      });
      if (result) {
        form.reset({
          full_name: result.full_name,
          email: result.email,
        });
      }
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosError = err as { response?: { status?: number } };
        if (axiosError.response?.status === 409) {
          form.setError("email", {
            message: "A candidate with this email already exists.",
          });
        } else if (axiosError.response?.status === 404) {
          form.setError("root", {
            message: "Candidate not found",
          });
        } else {
          console.error("Failed to update candidate:", err);
        }
      } else {
        console.error("Failed to update candidate:", err);
      }
    }
  };

  const getStageVariant = (
    stage: string
  ): "default" | "secondary" | "outline" | "destructive" => {
    switch (stage.toLowerCase()) {
      case "new":
        return "default";
      case "screening":
        return "secondary";
      case "technical":
        return "outline";
      case "offer":
        return "default";
      case "hired":
        return "default";
      case "rejected":
        return "destructive";
      default:
        return "default";
    }
  };

  const handleAddToPosition = async () => {
    if (!selectedPositionId) return;

    setAddError("");
    try {
      await addToPosition.mutateAsync({
        path: { candidate_id: candidateIdNum },
        body: { position_id: Number(selectedPositionId) },
      });
      setAddDialogOpen(false);
      setSelectedPositionId("");
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosError = err as { response?: { status?: number } };
        if (axiosError.response?.status === 409) {
          setAddError("Candidate is already associated with this position.");
        } else {
          setAddError("Failed to add candidate to position.");
        }
      } else {
        setAddError("Failed to add candidate to position.");
      }
    }
  };

  const handleRemoveClick = (positionId: number, positionTitle: string) => {
    setPositionToRemove({ id: positionId, title: positionTitle });
    setRemoveDialogOpen(true);
  };

  const handleRemoveConfirm = async () => {
    if (!positionToRemove) return;

    try {
      await removeFromPosition.mutateAsync({
        path: { candidate_id: candidateIdNum, position_id: positionToRemove.id },
      });
      setRemoveDialogOpen(false);
      setPositionToRemove(null);
    } catch (err) {
      console.error("Failed to remove candidate from position:", err);
    }
  };


  const handleStageChange = async (positionId: number, newStage: string) => {
    setUpdatingStage(positionId);
    try {
      await updateStageMutation.mutateAsync({
        path: { candidate_id: candidateIdNum, position_id: positionId },
        body: { stage: newStage },
      });
    } catch (err) {
      console.error("Failed to update stage:", err);
    } finally {
      setUpdatingStage(null);
    }
  };

  const availablePositions = positionsData?.items?.filter(
    (pos) =>
      pos.status !== "closed" &&
      !candidate?.positions?.some((cp) => cp.position_id === pos.id)
  ) || [];

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <Skeleton className="h-8 w-64" />
          <div className="flex gap-2">
            <Skeleton className="h-10 w-24" />
            <Skeleton className="h-10 w-28" />
          </div>
        </div>
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-48" />
          </CardHeader>
          <CardContent className="space-y-4">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error || !candidate) {
    return (
      <div className="p-6">
        <Card>
          <CardContent className="pt-6">
            <p className="text-center text-muted-foreground">
              Candidate not found
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-semibold">{candidate.full_name}</h1>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={form.handleSubmit(onSubmit)}
            disabled={updateCandidate.isPending}
          >
            {updateCandidate.isPending && (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            )}
            Save
          </Button>
          <Button variant="outline" onClick={() => setArchiveDialogOpen(true)}>
            <Archive className="mr-2 h-4 w-4" />
            Archive
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Candidate Details</CardTitle>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form className="space-y-4">
              <FormField
                control={form.control}
                name="full_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Full Name</FormLabel>
                    <FormControl>
                      <Input {...field} disabled={updateCandidate.isPending} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Email</FormLabel>
                    <FormControl>
                      <Input {...field} disabled={updateCandidate.isPending} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              {form.formState.errors.root && (
                <p className="text-sm font-medium text-destructive">
                  {form.formState.errors.root.message}
                </p>
              )}
            </form>
          </Form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Positions</CardTitle>
            <Button
              variant="outline"
              onClick={() => setAddDialogOpen(true)}
              disabled={availablePositions.length === 0}
            >
              Add to Position
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {candidate.positions && candidate.positions.length > 0 ? (
            <div className="border rounded-lg">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Position</TableHead>
                    <TableHead>Stage</TableHead>
                    <TableHead className="w-20"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {candidate.positions.map((position) => {
                    const validNextStages = getValidNextStages(position.stage);
                    const isUpdating = updatingStage === position.position_id;
                    const isTerminal = validNextStages.length === 0;

                    return (
                      <TableRow key={position.position_id}>
                        <TableCell className="font-medium">
                          <Link
                            to="/positions/$positionId"
                            params={{ positionId: String(position.position_id) }}
                            className="hover:underline"
                          >
                            {position.position_title}
                          </Link>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            {isUpdating ? (
                              <div className="flex items-center gap-2">
                                <Loader2 className="h-4 w-4 animate-spin" />
                                <span className="text-sm text-muted-foreground">Updating...</span>
                              </div>
                            ) : isTerminal ? (
                              <Badge variant={getStageVariant(position.stage)}>
                                {STAGE_LABELS[position.stage]}
                              </Badge>
                            ) : (
                              <Select
                                value={position.stage}
                                onValueChange={(value) => handleStageChange(position.position_id, value)}
                                disabled={isUpdating}
                              >
                                <SelectTrigger className="w-[140px]">
                                  <SelectValue>
                                    <Badge variant={getStageVariant(position.stage)}>
                                      {STAGE_LABELS[position.stage]}
                                    </Badge>
                                  </SelectValue>
                                </SelectTrigger>
                                <SelectContent>
                                  {validNextStages.map((stage) => (
                                    <SelectItem
                                      key={stage}
                                      value={stage}
                                      className={stage === "rejected" ? "text-destructive" : ""}
                                    >
                                      {STAGE_LABELS[stage]}
                                    </SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleRemoveClick(position.position_id, position.position_title)}
                            disabled={removeFromPosition.isPending}
                          >
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-muted-foreground">
                No positions linked yet. Use 'Add to Position' to link this candidate.
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={addDialogOpen} onOpenChange={setAddDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add to Position</DialogTitle>
            <DialogDescription>
              Select a position to link {candidate.full_name} to.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <Select value={selectedPositionId} onValueChange={setSelectedPositionId}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select a position" />
              </SelectTrigger>
              <SelectContent>
                {availablePositions.map((position) => (
                  <SelectItem key={position.id} value={String(position.id)}>
                    {position.title}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {addError && (
              <p className="text-sm font-medium text-destructive">{addError}</p>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setAddDialogOpen(false);
              setSelectedPositionId("");
              setAddError("");
            }}>
              Cancel
            </Button>
            <Button
              onClick={handleAddToPosition}
              disabled={!selectedPositionId || addToPosition.isPending}
            >
              {addToPosition.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Add
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={removeDialogOpen} onOpenChange={setRemoveDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Remove from Position</DialogTitle>
            <DialogDescription>
              Remove {candidate.full_name} from {positionToRemove?.title}? This will delete their pipeline progress for this position.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setRemoveDialogOpen(false);
              setPositionToRemove(null);
            }}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleRemoveConfirm}
              disabled={removeFromPosition.isPending}
            >
              {removeFromPosition.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Remove
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={archiveDialogOpen} onOpenChange={setArchiveDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Archive Candidate</DialogTitle>
            <DialogDescription>
              Are you sure you want to archive {candidate.full_name}? They will be hidden from the candidates list.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setArchiveDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={async () => {
                try {
                  await archiveCandidate.mutateAsync({
                    path: { candidate_id: candidateIdNum },
                  });
                  setArchiveDialogOpen(false);
                  navigate({ to: "/candidates" });
                } catch (err) {
                  console.error("Failed to archive candidate:", err);
                }
              }}
              disabled={archiveCandidate.isPending}
            >
              {archiveCandidate.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Archive
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <div className="text-sm text-muted-foreground space-y-1">
        <p>Created: {new Date(candidate.created_at).toLocaleString()}</p>
        <p>Last updated: {new Date(candidate.updated_at).toLocaleString()}</p>
      </div>
    </div>
  );
}
