import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  saveRubricAsTemplateApiPositionsPositionIdRubricSaveAsTemplatePostMutation,
  listRubricTemplatesApiRubricTemplatesGetQueryKey,
} from "@/shared/api/@tanstack/react-query.gen";

export function useSaveRubricAsTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    ...saveRubricAsTemplateApiPositionsPositionIdRubricSaveAsTemplatePostMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: listRubricTemplatesApiRubricTemplatesGetQueryKey(),
      });
    },
  });
}
