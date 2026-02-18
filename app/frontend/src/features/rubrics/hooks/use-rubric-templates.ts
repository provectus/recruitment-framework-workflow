import { useQuery } from "@tanstack/react-query";
import { listRubricTemplatesApiRubricTemplatesGetOptions } from "@/shared/api/@tanstack/react-query.gen";

export function useRubricTemplates() {
  return useQuery({
    ...listRubricTemplatesApiRubricTemplatesGetOptions(),
  });
}
