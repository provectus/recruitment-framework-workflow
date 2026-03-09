import { useMutation, useQueryClient } from "@tanstack/react-query";
import { pasteTranscriptApiDocumentsPastePostMutation } from "@/shared/api/@tanstack/react-query.gen";

export function usePasteTranscript() {
  const queryClient = useQueryClient();
  return useMutation({
    ...pasteTranscriptApiDocumentsPastePostMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({
        predicate: (query) => {
          const key = query.queryKey[0];
          if (!key || typeof key !== "object" || !("_id" in key)) {
            return false;
          }
          return key._id === "listCandidateDocumentsApiCandidatesCandidateIdDocumentsGet";
        },
      });
    },
  });
}
