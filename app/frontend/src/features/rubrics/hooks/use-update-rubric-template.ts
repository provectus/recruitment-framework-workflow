import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  updateRubricTemplateApiRubricTemplatesTemplateIdPatchMutation,
  listRubricTemplatesApiRubricTemplatesGetQueryKey,
} from "@/shared/api/@tanstack/react-query.gen";

export function useUpdateRubricTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    ...updateRubricTemplateApiRubricTemplatesTemplateIdPatchMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: listRubricTemplatesApiRubricTemplatesGetQueryKey(),
      });
    },
  });
}
