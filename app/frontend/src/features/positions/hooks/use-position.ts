import { useQuery } from "@tanstack/react-query";
import { getPositionApiPositionsPositionIdGetOptions } from "@/shared/api/@tanstack/react-query.gen";

export function usePosition(positionId: number) {
  return useQuery({
    ...getPositionApiPositionsPositionIdGetOptions({ path: { position_id: positionId } }),
  });
}
