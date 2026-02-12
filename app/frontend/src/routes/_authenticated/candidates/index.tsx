import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import {
  Plus,
  Loader2,
  Users,
  Search,
  X,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
} from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod/v4";
import { useCandidates, useCreateCandidate } from "@/features/candidates";
import { usePositions } from "@/features/positions";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/ui/select";
import { Input } from "@/shared/ui/input";
import { Skeleton } from "@/shared/ui/skeleton";
import { getStageVariant } from "@/shared/lib/stage-utils";

export const Route = createFileRoute("/_authenticated/candidates/")({
  component: CandidatesPage,
});

const candidateSchema = z.object({
  full_name: z.string().min(1, "Full name is required"),
  email: z.email("Please enter a valid email address"),
});

type CandidateFormData = z.infer<typeof candidateSchema>;

const STAGE_OPTIONS = [
  { value: "new", label: "New" },
  { value: "screening", label: "Screening" },
  { value: "technical", label: "Technical" },
  { value: "offer", label: "Offer" },
  { value: "hired", label: "Hired" },
  { value: "rejected", label: "Rejected" },
];

type SortColumn = "full_name" | "email" | "updated_at";
type SortOrder = "asc" | "desc";

function SortIcon({
  column,
  sortBy,
  sortOrder,
}: {
  column: SortColumn;
  sortBy: SortColumn;
  sortOrder: SortOrder;
}) {
  if (sortBy !== column) return <ArrowUpDown className="ml-1 h-3 w-3" />;
  return sortOrder === "asc" ? (
    <ArrowUp className="ml-1 h-3 w-3" />
  ) : (
    <ArrowDown className="ml-1 h-3 w-3" />
  );
}

function CandidatesPage() {
  const navigate = useNavigate();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [stageFilter, setStageFilter] = useState<string | null>(null);
  const [positionFilter, setPositionFilter] = useState<number | null>(null);
  const [sortBy, setSortBy] = useState<SortColumn>("updated_at");
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");

  const { data: candidates, isLoading } = useCandidates({
    search: search || null,
    stage: stageFilter,
    position_id: positionFilter,
    sort_by: sortBy,
    sort_order: sortOrder,
  });

  const { data: positions } = usePositions();
  const createCandidate = useCreateCandidate();

  const form = useForm<CandidateFormData>({
    resolver: zodResolver(candidateSchema),
    defaultValues: {
      full_name: "",
      email: "",
    },
  });

  const hasActiveFilters = search || stageFilter || positionFilter;

  const clearFilters = () => {
    setSearch("");
    setStageFilter(null);
    setPositionFilter(null);
    setSortBy("updated_at");
    setSortOrder("desc");
  };

  const toggleSort = (column: SortColumn) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortBy(column);
      setSortOrder("asc");
    }
  };

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

      <div className="flex flex-wrap items-center gap-3 mb-4">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search by name or email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select
          value={stageFilter ?? "all"}
          onValueChange={(val) =>
            setStageFilter(val === "all" ? null : val)
          }
        >
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="All Stages" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Stages</SelectItem>
            {STAGE_OPTIONS.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select
          value={positionFilter?.toString() ?? "all"}
          onValueChange={(val) =>
            setPositionFilter(val === "all" ? null : Number(val))
          }
        >
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="All Positions" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Positions</SelectItem>
            {positions?.items.map((pos) => (
              <SelectItem key={pos.id} value={pos.id.toString()}>
                {pos.title}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {hasActiveFilters && (
          <Button variant="ghost" size="sm" onClick={clearFilters}>
            <X className="mr-1 h-4 w-4" />
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
      ) : candidates && candidates.items.length > 0 ? (
        <div className="border rounded-lg">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>
                  <button
                    type="button"
                    className="flex items-center font-medium hover:text-foreground"
                    onClick={() => toggleSort("full_name")}
                  >
                    Name
                    <SortIcon column="full_name" sortBy={sortBy} sortOrder={sortOrder} />
                  </button>
                </TableHead>
                <TableHead>
                  <button
                    type="button"
                    className="flex items-center font-medium hover:text-foreground"
                    onClick={() => toggleSort("email")}
                  >
                    Email
                    <SortIcon column="email" sortBy={sortBy} sortOrder={sortOrder} />
                  </button>
                </TableHead>
                <TableHead>Positions</TableHead>
                <TableHead>
                  <button
                    type="button"
                    className="flex items-center font-medium hover:text-foreground"
                    onClick={() => toggleSort("updated_at")}
                  >
                    Last Updated
                    <SortIcon column="updated_at" sortBy={sortBy} sortOrder={sortOrder} />
                  </button>
                </TableHead>
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
          {hasActiveFilters ? (
            <>
              <h3 className="text-lg font-semibold mb-2">No matches found</h3>
              <p className="text-muted-foreground mb-4">
                Try adjusting your search or filters.
              </p>
              <Button variant="outline" onClick={clearFilters}>
                <X className="mr-2 h-4 w-4" />
                Clear filters
              </Button>
            </>
          ) : (
            <>
              <h3 className="text-lg font-semibold mb-2">
                No candidates yet
              </h3>
              <p className="text-muted-foreground mb-4">
                Add your first candidate to start tracking applications.
              </p>
              <Button onClick={() => setDialogOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                New Candidate
              </Button>
            </>
          )}
        </div>
      )}
    </div>
  );
}
