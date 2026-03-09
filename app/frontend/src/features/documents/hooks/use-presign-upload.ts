import { useMutation } from "@tanstack/react-query";
import { presignUploadApiDocumentsPresignPostMutation } from "@/shared/api/@tanstack/react-query.gen";

export function usePresignUpload() {
  return useMutation({
    ...presignUploadApiDocumentsPresignPostMutation(),
  });
}
