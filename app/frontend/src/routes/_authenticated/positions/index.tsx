"use client";

import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { Plus, Loader2, Briefcase, X } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod/v4";
import { usePositions, useCreatePosition, useUsers } from "@/features/positions";
import { useTeams } from "@/features/settings";
import { Button } from "@/shared/ui/button";
import { Badge } from "@/shared/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/shared/ui/dialog";
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
import { Skeleton } from "@/shared/ui/skeleton";

export const Route = createFileRoute("/_authenticated/positions/")({
  component: PositionsPage,
});

const positionSchema = z.object({
  title: z.string().min(1, "Title is required"),
  requirements: z.string().optional(),
  team_id: z.number({ message: "Team is required" }),
  hiring_manager_id: z.number({ message: "Hiring manager is required" }),
});

type PositionFormData = z.infer<typeof positionSchema>;

function PositionsPage() {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [teamFilter, setTeamFilter] = useState<string>("");

  const { data: positions, isLoading } = usePositions({
    status: statusFilter || undefined,
    team_id: teamFilter ? Number(teamFilter) : undefined,
  });
  const { data: teams } = useTeams();
  const { data: users } = useUsers();
  const createPosition = useCreatePosition();

  const hasActiveFilters = statusFilter || teamFilter;

  const clearFilters = () => {
    setStatusFilter("");
    setTeamFilter("");
  };

  const form = useForm<PositionFormData>({
    resolver: zodResolver(positionSchema),
    defaultValues: {
      title: "",
      requirements: "",
    },
  });

  const onSubmit = async (data: PositionFormData) => {
    try {
      await createPosition.mutateAsync({
        body: data,
      });
      setDialogOpen(false);
      form.reset();
    } catch (error) {
      console.error("Failed to create position:", error);
    }
  };

  const getStatusVariant = (
    status: string
  ): "default" | "secondary" | "outline" | "destructive" => {
    switch (status.toLowerCase()) {
      case "open":
        return "default";
      case "on hold":
        return "secondary";
      case "closed":
        return "outline";
      default:
        return "default";
    }
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Positions</h1>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              New Position
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[525px]">
            <DialogHeader>
              <DialogTitle>Create Position</DialogTitle>
              <DialogDescription>
                Add a new position to start tracking candidates.
              </DialogDescription>
            </DialogHeader>
            <Form {...form}>
              <form
                onSubmit={form.handleSubmit(onSubmit)}
                className="grid gap-4"
              >
                <FormField
                  control={form.control}
                  name="title"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Title</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="Senior Frontend Engineer"
                          {...field}
                          disabled={createPosition.isPending}
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
                      <FormLabel>Requirements (optional)</FormLabel>
                      <FormControl>
                        <Textarea
                          placeholder="5+ years experience with React..."
                          rows={4}
                          {...field}
                          disabled={createPosition.isPending}
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
                        disabled={createPosition.isPending}
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
                        disabled={createPosition.isPending}
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
                <DialogFooter>
                  <Button
                    type="submit"
                    disabled={createPosition.isPending}
                  >
                    {createPosition.isPending && (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    )}
                    Create Position
                  </Button>
                </DialogFooter>
              </form>
            </Form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="flex items-center gap-3 mb-6">
        <Select
          value={statusFilter || "all"}
          onValueChange={(v) => setStatusFilter(v === "all" ? "" : v)}
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="All statuses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            <SelectItem value="open">Open</SelectItem>
            <SelectItem value="on_hold">On Hold</SelectItem>
            <SelectItem value="closed">Closed</SelectItem>
          </SelectContent>
        </Select>

        <Select
          value={teamFilter || "all"}
          onValueChange={(v) => setTeamFilter(v === "all" ? "" : v)}
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="All teams" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All teams</SelectItem>
            {teams?.map((team) => (
              <SelectItem key={team.id} value={String(team.id)}>
                {team.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {hasActiveFilters && (
          <Button
            variant="ghost"
            size="sm"
            onClick={clearFilters}
            className="h-10"
          >
            <X className="mr-2 h-4 w-4" />
            Clear filters
          </Button>
        )}
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      ) : positions && positions.items.length > 0 ? (
        <div className="border rounded-lg">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Title</TableHead>
                <TableHead>Team</TableHead>
                <TableHead>Hiring Manager</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Candidates</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {positions.items.map((position) => (
                <Link
                  key={position.id}
                  to="/positions/$positionId"
                  params={{ positionId: String(position.id) }}
                  className="contents"
                >
                  <TableRow className="cursor-pointer hover:bg-muted/50">
                    <TableCell className="font-medium">
                      {position.title}
                    </TableCell>
                    <TableCell>{position.team_name}</TableCell>
                    <TableCell>{position.hiring_manager_name}</TableCell>
                    <TableCell>
                      <Badge variant={getStatusVariant(position.status)}>
                        {position.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      {position.candidate_count}
                    </TableCell>
                  </TableRow>
                </Link>
              ))}
            </TableBody>
          </Table>
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <Briefcase className="h-12 w-12 text-muted-foreground mb-4" />
          {hasActiveFilters ? (
            <>
              <h3 className="text-lg font-semibold mb-2">No matches found</h3>
              <p className="text-muted-foreground mb-4">
                Try adjusting your filters.
              </p>
              <Button variant="outline" onClick={clearFilters}>
                <X className="mr-2 h-4 w-4" />
                Clear filters
              </Button>
            </>
          ) : (
            <>
              <h3 className="text-lg font-semibold mb-2">No positions yet</h3>
              <p className="text-muted-foreground mb-4">
                Create your first position to start tracking candidates.
              </p>
              <Button onClick={() => setDialogOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                New Position
              </Button>
            </>
          )}
        </div>
      )}
    </div>
  );
}
