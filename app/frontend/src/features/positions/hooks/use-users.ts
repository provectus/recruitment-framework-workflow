import { useQuery } from "@tanstack/react-query";
import { listUsersApiUsersGetOptions } from "@/shared/api/@tanstack/react-query.gen";

export function useUsers() {
  return useQuery({
    ...listUsersApiUsersGetOptions(),
  });
}
