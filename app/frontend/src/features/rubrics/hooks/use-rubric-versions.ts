import { useQuery } from "@tanstack/react-query";
import {
  listRubricVersionsApiPositionsPositionIdRubricVersionsGetOptions,
} from "@/shared/api/@tanstack/react-query.gen";

export function useRubricVersions(positionId: number) {
  return useQuery(
    listRubricVersionsApiPositionsPositionIdRubricVersionsGetOptions({
      path: { position_id: positionId },
    }),
  );
}
