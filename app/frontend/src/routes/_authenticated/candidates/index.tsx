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
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/shared/ui/pagination";
import { getStageVariant, STAGE_OPTIONS } from "@/shared/lib/stage-utils";

export const Route = createFileRoute("/_authenticated/candidates/")({
  component: CandidatesPage,
});

const candidateSchema = z.object({
  full_name: z.string().min(1, "Full name is required"),
  email: z.email("Please enter a valid email address"),
});

type CandidateFormData = z.infer<typeof candidateSchema>;

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
  const [page, setPage] = useState(1);
  const limit = 20;

  const { data: candidates, isLoading } = useCandidates({
    offset: (page - 1) * limit,
    limit,
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
    setPage(1);
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
        form.setError("root", {
          type: "manual",
          message: "Failed to create candidate. Please try again.",
        });
      }
    }
  };

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-semibold tracking-tight">Candidates</h1>
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
                {form.formState.errors.root && (
                  <p className="text-sm text-destructive">
                    {form.formState.errors.root.message}
                  </p>
                )}
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
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="pl-9"
          />
        </div>
        <Select
          value={stageFilter ?? "all"}
          onValueChange={(val) => {
            setStageFilter(val === "all" ? null : val);
            setPage(1);
          }}
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
          onValueChange={(val) => {
            setPositionFilter(val === "all" ? null : Number(val));
            setPage(1);
          }}
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
        <>
        <div className="border border-border rounded-lg overflow-hidden">
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
                  <TableCell className="font-mono tabular-nums">
                    {new Date(candidate.updated_at).toLocaleDateString()}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
        {candidates.total > limit && (
          <Pagination className="mt-4">
            <PaginationContent>
              <PaginationItem>
                <PaginationPrevious
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  aria-disabled={page === 1}
                  className={page === 1 ? "pointer-events-none opacity-50" : "cursor-pointer"}
                />
              </PaginationItem>
              {Array.from(
                { length: Math.ceil(candidates.total / limit) },
                (_, i) => i + 1,
              ).map((p) => (
                <PaginationItem key={p}>
                  <PaginationLink
                    isActive={p === page}
                    onClick={() => setPage(p)}
                    className="cursor-pointer"
                  >
                    {p}
                  </PaginationLink>
                </PaginationItem>
              ))}
              <PaginationItem>
                <PaginationNext
                  onClick={() =>
                    setPage((p) =>
                      Math.min(Math.ceil(candidates.total / limit), p + 1),
                    )
                  }
                  aria-disabled={page >= Math.ceil(candidates.total / limit)}
                  className={
                    page >= Math.ceil(candidates.total / limit)
                      ? "pointer-events-none opacity-50"
                      : "cursor-pointer"
                  }
                />
              </PaginationItem>
            </PaginationContent>
          </Pagination>
        )}
        </>
      ) : (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="relative inline-flex items-center justify-center mb-4">
            <Users className="size-12 text-muted-foreground/30" />
            <div className="absolute -bottom-1.5 -right-1.5 rounded-full bg-card p-1">
              <Plus className="size-4 text-primary" />
            </div>
          </div>
          {hasActiveFilters ? (
            <>
              <h3 className="text-base font-semibold tracking-tight mb-2">No matches found</h3>
              <p className="text-muted-foreground max-w-xs mb-4">
                Try adjusting your search or filters.
              </p>
              <Button variant="outline" onClick={clearFilters}>
                <X className="mr-2 h-4 w-4" />
                Clear filters
              </Button>
            </>
          ) : (
            <>
              <h3 className="text-base font-semibold tracking-tight mb-2">
                No candidates yet
              </h3>
              <p className="text-muted-foreground max-w-xs mb-4">
                Add your first candidate to get started.
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
