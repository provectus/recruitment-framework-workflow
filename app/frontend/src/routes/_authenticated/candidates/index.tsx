"use client";

import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { Plus, Loader2, Users } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod/v4";
import { useCandidates, useCreateCandidate } from "@/features/candidates";
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
import { Skeleton } from "@/shared/ui/skeleton";

export const Route = createFileRoute("/_authenticated/candidates/")({
  component: CandidatesPage,
});

const candidateSchema = z.object({
  full_name: z.string().min(1, "Full name is required"),
  email: z.email("Please enter a valid email address"),
});

type CandidateFormData = z.infer<typeof candidateSchema>;

function CandidatesPage() {
  const navigate = useNavigate();
  const [dialogOpen, setDialogOpen] = useState(false);

  const { data: candidates, isLoading } = useCandidates();
  const createCandidate = useCreateCandidate();

  const form = useForm<CandidateFormData>({
    resolver: zodResolver(candidateSchema),
    defaultValues: {
      full_name: "",
      email: "",
    },
  });

  const onSubmit = async (data: CandidateFormData) => {
    try {
      const result = await createCandidate.mutateAsync({
        body: data,
      });
      setDialogOpen(false);
      form.reset();
      navigate({
        to: "/candidates/$candidateId",
        params: { candidateId: String(result.id) },
      });
    } catch (error: unknown) {
      const status =
        error && typeof error === "object" && "status" in error
          ? (error as { status: number }).status
          : undefined;
      if (status === 409) {
        form.setError("email", {
          type: "manual",
          message: "A candidate with this email already exists.",
        });
      } else {
        console.error("Failed to create candidate:", error);
      }
    }
  };

  const getStageVariant = (
    stage: string
  ): "default" | "secondary" | "outline" | "destructive" => {
    switch (stage.toLowerCase()) {
      case "new":
        return "secondary";
      case "screening":
        return "default";
      case "interview":
        return "default";
      case "offer":
        return "default";
      case "hired":
        return "default";
      case "rejected":
        return "outline";
      default:
        return "secondary";
    }
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Candidates</h1>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              New Candidate
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle>Create Candidate</DialogTitle>
              <DialogDescription>
                Add a new candidate to track their application.
              </DialogDescription>
            </DialogHeader>
            <Form {...form}>
              <form
                onSubmit={form.handleSubmit(onSubmit)}
                className="grid gap-4"
              >
                <FormField
                  control={form.control}
                  name="full_name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Full Name</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="John Doe"
                          {...field}
                          disabled={createCandidate.isPending}
                        />
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
                        <Input
                          type="email"
                          placeholder="john.doe@example.com"
                          {...field}
                          disabled={createCandidate.isPending}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <DialogFooter>
                  <Button type="submit" disabled={createCandidate.isPending}>
                    {createCandidate.isPending && (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    )}
                    Create Candidate
                  </Button>
                </DialogFooter>
              </form>
            </Form>
          </DialogContent>
        </Dialog>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      ) : candidates && candidates.items.length > 0 ? (
        <div className="border rounded-lg">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Positions</TableHead>
                <TableHead>Last Updated</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {candidates.items.map((candidate) => (
                <TableRow
                  key={candidate.id}
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() => {
                    navigate({
                      to: "/candidates/$candidateId",
                      params: { candidateId: String(candidate.id) },
                    });
                  }}
                >
                  <TableCell className="font-medium">
                    {candidate.full_name}
                  </TableCell>
                  <TableCell>{candidate.email}</TableCell>
                  <TableCell>
                    {candidate.positions.length > 0 ? (
                      <div className="flex flex-wrap gap-2">
                        {candidate.positions.map((pos, idx) => (
                          <div
                            key={idx}
                            className="flex items-center gap-2 text-sm"
                          >
                            <span className="text-muted-foreground">
                              {pos.position_title}:
                            </span>
                            <Badge variant={getStageVariant(pos.stage)}>
                              {pos.stage}
                            </Badge>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </TableCell>
                  <TableCell>
                    {new Date(candidate.updated_at).toLocaleDateString()}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <Users className="h-12 w-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">No candidates yet</h3>
          <p className="text-muted-foreground mb-4">
            Add your first candidate to start tracking applications.
          </p>
          <Button onClick={() => setDialogOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            New Candidate
          </Button>
        </div>
      )}
    </div>
  );
}
