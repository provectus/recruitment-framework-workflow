import { useQuery } from "@tanstack/react-query";
import { getDashboardStatsApiDashboardStatsGetOptions } from "@/shared/api/@tanstack/react-query.gen";

export function useDashboardStats() {
  return useQuery({
    ...getDashboardStatsApiDashboardStatsGetOptions(),
  });
}
