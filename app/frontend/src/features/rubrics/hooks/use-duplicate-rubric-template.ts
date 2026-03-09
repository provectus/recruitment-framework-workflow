import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  duplicateRubricTemplateApiRubricTemplatesTemplateIdDuplicatePostMutation,
  listRubricTemplatesApiRubricTemplatesGetQueryKey,
} from "@/shared/api/@tanstack/react-query.gen";

export function useDuplicateRubricTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    ...duplicateRubricTemplateApiRubricTemplatesTemplateIdDuplicatePostMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: listRubricTemplatesApiRubricTemplatesGetQueryKey(),
      });
    },
  });
}
