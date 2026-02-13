import { useQuery } from "@tanstack/react-query";
import { getDocumentApiDocumentsDocumentIdGetOptions } from "@/shared/api/@tanstack/react-query.gen";

export function useDocument(documentId: number, options?: { enabled?: boolean }) {
  const queryOptions = getDocumentApiDocumentsDocumentIdGetOptions({
    path: { document_id: documentId },
  });

  return useQuery({
    ...queryOptions,
    enabled: options?.enabled ?? true,
  });
}
