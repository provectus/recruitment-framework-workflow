import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  archiveRubricTemplateApiRubricTemplatesTemplateIdArchivePostMutation,
  listRubricTemplatesApiRubricTemplatesGetQueryKey,
} from "@/shared/api/@tanstack/react-query.gen";

export function useArchiveRubricTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    ...archiveRubricTemplateApiRubricTemplatesTemplateIdArchivePostMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: listRubricTemplatesApiRubricTemplatesGetQueryKey(),
      });
    },
  });
}
