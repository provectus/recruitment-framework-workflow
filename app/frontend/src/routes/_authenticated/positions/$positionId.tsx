"use client";

import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Loader2, Archive } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod/v4";
import {
  usePosition,
  useUpdatePosition,
  useUsers,
  useArchivePosition,
} from "@/features/positions";
import { useTeams } from "@/features/settings";
import { Button } from "@/shared/ui/button";
import { Badge } from "@/shared/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
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
import { Textarea } from "@/shared/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/shared/ui/dialog";
import { Skeleton } from "@/shared/ui/skeleton";

export const Route = createFileRoute("/_authenticated/positions/$positionId")({
  component: PositionDetailPage,
});

const positionSchema = z.object({
  title: z.string().min(1, "Title is required").optional(),
  requirements: z.string().optional().nullable(),
  team_id: z.number().optional(),
  hiring_manager_id: z.number().optional(),
  status: z.enum(["open", "on_hold", "closed"]).optional(),
});

type PositionFormData = z.infer<typeof positionSchema>;

function PositionDetailPage() {
  const navigate = useNavigate();
  const { positionId } = Route.useParams();
  const positionIdNum = Number(positionId);
  const { data: position, isLoading, error } = usePosition(positionIdNum);
  const { data: teams } = useTeams();
  const { data: users } = useUsers();
  const updatePosition = useUpdatePosition(positionIdNum);
  const archivePosition = useArchivePosition(positionIdNum);
  const [archiveDialogOpen, setArchiveDialogOpen] = useState(false);

  const form = useForm<PositionFormData>({
    resolver: zodResolver(positionSchema),
    defaultValues: {
      title: "",
      requirements: "",
    },
  });

  useEffect(() => {
    if (position) {
      form.reset({
        title: position.title,
        requirements: position.requirements || "",
        team_id: position.team_id,
        hiring_manager_id: position.hiring_manager_id,
        status: position.status as "open" | "on_hold" | "closed",
      });
    }
  }, [position, form]);

  const onSubmit = async (data: PositionFormData) => {
    const changedFields: Partial<PositionFormData> = {};
    if (data.title !== position?.title) changedFields.title = data.title;
    if (data.requirements !== position?.requirements)
      changedFields.requirements = data.requirements;
    if (data.team_id !== position?.team_id) changedFields.team_id = data.team_id;
    if (data.hiring_manager_id !== position?.hiring_manager_id)
      changedFields.hiring_manager_id = data.hiring_manager_id;
    if (data.status !== position?.status) changedFields.status = data.status;

    if (Object.keys(changedFields).length === 0) return;

    try {
      const result = await updatePosition.mutateAsync({
        path: { position_id: positionIdNum },
        body: changedFields,
      });
      if (result) {
        form.reset({
          title: result.title,
          requirements: result.requirements || "",
          team_id: result.team_id,
          hiring_manager_id: result.hiring_manager_id,
          status: result.status as "open" | "on_hold" | "closed",
        });
      }
    } catch (err) {
      console.error("Failed to update position:", err);
    }
  };

  const getStatusVariant = (
    status: string
  ): "default" | "secondary" | "outline" | "destructive" => {
    switch (status.toLowerCase()) {
      case "open":
        return "default";
      case "on_hold":
        return "secondary";
      case "closed":
        return "outline";
      default:
        return "default";
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

  const formatStatus = (status: string): string => {
    switch (status.toLowerCase()) {
      case "open":
        return "Open";
      case "on_hold":
        return "On Hold";
      case "closed":
        return "Closed";
      default:
        return status;
    }
  };

  const formatStage = (stage: string): string => {
    return stage.charAt(0).toUpperCase() + stage.slice(1).toLowerCase();
  };

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
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error || !position) {
    return (
      <div className="p-6">
        <Card>
          <CardContent className="pt-6">
            <p className="text-center text-muted-foreground">
              Position not found
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
          <h1 className="text-2xl font-semibold">{position.title}</h1>
          <Badge variant={getStatusVariant(position.status)}>
            {formatStatus(position.status)}
          </Badge>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={form.handleSubmit(onSubmit)}
            disabled={updatePosition.isPending}
          >
            {updatePosition.isPending && (
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
          <CardTitle>Position Details</CardTitle>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form className="space-y-4">
              <FormField
                control={form.control}
                name="title"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Title</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        disabled={updatePosition.isPending}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="requirements"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Requirements</FormLabel>
                    <FormControl>
                      <Textarea
                        {...field}
                        value={field.value || ""}
                        rows={4}
                        disabled={updatePosition.isPending}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="team_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Team</FormLabel>
                    <Select
                      value={field.value ? String(field.value) : ""}
                      onValueChange={(value) =>
                        field.onChange(Number(value))
                      }
                      disabled={updatePosition.isPending}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select a team" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {teams?.map((team) => (
                          <SelectItem key={team.id} value={String(team.id)}>
                            {team.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="hiring_manager_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Hiring Manager</FormLabel>
                    <Select
                      value={field.value ? String(field.value) : ""}
                      onValueChange={(value) =>
                        field.onChange(Number(value))
                      }
                      disabled={updatePosition.isPending}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select a hiring manager" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {users?.map((user) => (
                          <SelectItem key={user.id} value={String(user.id)}>
                            {user.full_name || user.email}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="status"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Status</FormLabel>
                    <Select
                      value={field.value || ""}
                      onValueChange={(value) => field.onChange(value)}
                      disabled={updatePosition.isPending}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select status" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="open">Open</SelectItem>
                        <SelectItem value="on_hold">On Hold</SelectItem>
                        <SelectItem value="closed">Closed</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </form>
          </Form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Candidates</CardTitle>
        </CardHeader>
        <CardContent>
          {position.candidates && position.candidates.length > 0 ? (
            <div className="border rounded-lg">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Stage</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {position.candidates.map((candidate) => (
                    <Link
                      key={candidate.candidate_id}
                      to="/candidates/$candidateId"
                      params={{ candidateId: String(candidate.candidate_id) }}
                      className="contents"
                    >
                      <TableRow className="cursor-pointer hover:bg-muted/50">
                        <TableCell className="font-medium">
                          {candidate.candidate_name}
                        </TableCell>
                        <TableCell>{candidate.candidate_email}</TableCell>
                        <TableCell>
                          <Badge variant={getStageVariant(candidate.stage)}>
                            {formatStage(candidate.stage)}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    </Link>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <p className="text-muted-foreground text-center py-8">
              No candidates linked to this position yet.
            </p>
          )}
        </CardContent>
      </Card>

      <Dialog open={archiveDialogOpen} onOpenChange={setArchiveDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Archive Position</DialogTitle>
            <DialogDescription>
              Are you sure you want to archive "{position.title}"? It will be hidden from the positions list and dropdown menus.
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
                  await archivePosition.mutateAsync({
                    path: { position_id: positionIdNum },
                  });
                  setArchiveDialogOpen(false);
                  navigate({ to: "/positions" });
                } catch (err) {
                  console.error("Failed to archive position:", err);
                }
              }}
              disabled={archivePosition.isPending}
            >
              {archivePosition.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Archive
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <div className="text-sm text-muted-foreground space-y-1">
        <p>Created: {new Date(position.created_at).toLocaleString()}</p>
        <p>Last updated: {new Date(position.updated_at).toLocaleString()}</p>
      </div>
    </div>
  );
}
