import { useState, useEffect } from "react";
import { Plus, FileText, FileUp, Loader2 } from "lucide-react";
import { useNavigate } from "@tanstack/react-router";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from "@/shared/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
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
import { Input } from "@/shared/ui/input";
import { Button } from "@/shared/ui/button";
import { Label } from "@/shared/ui/label";
import { useCandidates } from "@/features/candidates";
import { CvUploadDialog } from "@/widgets/documents/cv-upload-dialog";
import { TranscriptUploadDialog } from "@/widgets/documents/transcript-upload-dialog";
import type { CandidateListItem, PositionStageItem } from "@/shared/api";
import { cn } from "@/shared/lib/utils";

type UploadType = "cv" | "transcript";
type Step = "idle" | "select-candidate" | "select-position" | "upload" | "success";

interface SelectedCandidate {
  id: number;
  full_name: string;
  positions: PositionStageItem[];
}

interface GlobalUploadMenuProps {
  collapsed?: boolean;
  className?: string;
}

export function GlobalUploadMenu({ collapsed = false, className }: GlobalUploadMenuProps) {
  const navigate = useNavigate();
  const [uploadType, setUploadType] = useState<UploadType | null>(null);
  const [step, setStep] = useState<Step>("idle");
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [selectedCandidate, setSelectedCandidate] = useState<SelectedCandidate | null>(null);
  const [selectedPositionId, setSelectedPositionId] = useState<number | null>(null);
  const [showSearchResults, setShowSearchResults] = useState(false);

  const { data: searchResults, isLoading: isSearching } = useCandidates({
    search: debouncedSearch || null,
    limit: 10,
  });

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery);
    }, 300);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  const handleUploadTypeSelect = (type: UploadType) => {
    setUploadType(type);
    setStep("select-candidate");
  };

  const handleCandidateSelect = (candidate: CandidateListItem) => {
    setSelectedCandidate({
      id: candidate.id,
      full_name: candidate.full_name,
      positions: candidate.positions,
    });
    setSearchQuery(candidate.full_name);
    setShowSearchResults(false);

    if (candidate.positions.length === 0) {
      handleClose();
      return;
    } else if (candidate.positions.length === 1) {
      setSelectedPositionId(candidate.positions[0].position_id);
      setStep("upload");
    } else {
      setStep("select-position");
    }
  };

  const handlePositionSelect = (positionId: string) => {
    setSelectedPositionId(parseInt(positionId, 10));
    setStep("upload");
  };

  const handleUploadSuccess = () => {
    setStep("success");
  };

  const handleViewCandidate = () => {
    if (selectedCandidate) {
      navigate({
        to: "/candidates/$candidateId",
        params: { candidateId: selectedCandidate.id.toString() },
      });
      handleClose();
    }
  };

  const handleClose = () => {
    setUploadType(null);
    setStep("idle");
    setSearchQuery("");
    setDebouncedSearch("");
    setSelectedCandidate(null);
    setSelectedPositionId(null);
    setShowSearchResults(false);
  };

  const getCandidatePositionId = (): number | null => {
    if (!selectedCandidate || !selectedPositionId) return null;
    const position = selectedCandidate.positions.find(
      (p) => p.position_id === selectedPositionId
    );
    return position?.candidate_position_id || null;
  };

  const isDialogOpen = step !== "idle" && step !== "upload";
  const candidatePositionId = getCandidatePositionId();

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="default"
            className={cn(
              "w-full justify-center",
              collapsed ? "px-2" : "px-3",
              className
            )}
            title="Upload documents"
          >
            <Plus className={cn("h-5 w-5", !collapsed && "mr-2")} />
            {!collapsed && <span>Upload</span>}
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start">
          <DropdownMenuItem onClick={() => handleUploadTypeSelect("cv")}>
            <FileUp className="h-4 w-4" />
            Upload CV
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => handleUploadTypeSelect("transcript")}>
            <FileText className="h-4 w-4" />
            Upload Transcript
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <Dialog open={isDialogOpen} onOpenChange={(open) => !open && handleClose()}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {step === "select-candidate" && `Upload ${uploadType === "cv" ? "CV" : "Transcript"}`}
              {step === "select-position" && "Select Position"}
              {step === "success" && "Upload Complete"}
            </DialogTitle>
            <DialogDescription>
              {step === "select-candidate" && "Search and select a candidate"}
              {step === "select-position" && "Choose which position this upload is for"}
              {step === "success" && "Your file has been uploaded successfully"}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            {step === "select-candidate" && (
              <div className="space-y-2 relative">
                <Label htmlFor="candidate-search">Candidate</Label>
                <div className="relative">
                  <Input
                    id="candidate-search"
                    placeholder="Search by name or email..."
                    value={searchQuery}
                    onChange={(e) => {
                      setSearchQuery(e.target.value);
                      setShowSearchResults(true);
                      setSelectedCandidate(null);
                    }}
                    onFocus={() => setShowSearchResults(true)}
                  />
                  {isSearching && (
                    <div className="absolute right-3 top-1/2 -translate-y-1/2">
                      <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                    </div>
                  )}
                </div>

                {showSearchResults && searchQuery.length > 0 && (
                  <div className="absolute z-50 w-full mt-1 bg-popover border rounded-md shadow-md max-h-[300px] overflow-auto">
                    {isSearching ? (
                      <div className="p-4 text-center text-sm text-muted-foreground">
                        Searching...
                      </div>
                    ) : searchResults?.items && searchResults.items.length > 0 ? (
                      <div className="p-1">
                        {searchResults.items.map((candidate: CandidateListItem) => (
                          <button
                            key={candidate.id}
                            className="w-full text-left px-2 py-2 text-sm rounded-sm hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground outline-none"
                            onClick={() => handleCandidateSelect(candidate)}
                          >
                            <div className="font-medium">{candidate.full_name}</div>
                            <div className="text-xs text-muted-foreground">
                              {candidate.email}
                            </div>
                            {candidate.positions.length > 0 ? (
                              <div className="text-xs text-muted-foreground mt-1">
                                {candidate.positions.length} position{candidate.positions.length > 1 ? "s" : ""}
                              </div>
                            ) : (
                              <div className="text-xs text-destructive mt-1">
                                No positions — cannot upload
                              </div>
                            )}
                          </button>
                        ))}
                      </div>
                    ) : (
                      <div className="p-4 text-center text-sm text-muted-foreground">
                        No candidates found
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {step === "select-position" && selectedCandidate && (
              <div className="space-y-2">
                <Label htmlFor="position-select">Position</Label>
                <Select onValueChange={handlePositionSelect}>
                  <SelectTrigger id="position-select">
                    <SelectValue placeholder="Select a position" />
                  </SelectTrigger>
                  <SelectContent>
                    {selectedCandidate.positions.map((position) => (
                      <SelectItem key={position.position_id} value={position.position_id.toString()}>
                        {position.position_title}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            {step === "success" && (
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={handleClose}>
                  Close
                </Button>
                <Button onClick={handleViewCandidate}>View Candidate</Button>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {step === "upload" && candidatePositionId && uploadType === "cv" && (
        <CvUploadDialog
          candidatePositionId={candidatePositionId}
          open={true}
          onOpenChange={(open) => {
            if (!open) handleClose();
          }}
          onSuccess={handleUploadSuccess}
        />
      )}

      {step === "upload" && candidatePositionId && uploadType === "transcript" && (
        <TranscriptUploadDialog
          candidatePositionId={candidatePositionId}
          open={true}
          onOpenChange={(open) => {
            if (!open) handleClose();
          }}
          onSuccess={handleUploadSuccess}
        />
      )}
    </>
  );
}
