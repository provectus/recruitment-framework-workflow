import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  createRubricTemplateApiRubricTemplatesPostMutation,
  listRubricTemplatesApiRubricTemplatesGetQueryKey,
} from "@/shared/api/@tanstack/react-query.gen";

export function useCreateRubricTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    ...createRubricTemplateApiRubricTemplatesPostMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: listRubricTemplatesApiRubricTemplatesGetQueryKey(),
      });
    },
  });
}
