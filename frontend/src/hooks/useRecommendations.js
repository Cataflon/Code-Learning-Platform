import { useQuery } from "@tanstack/react-query";

import { getRecommendations } from "../api/materials.js";

/**
 * Materials to review after a finished submission with failed tests.
 * Asked only once the submission is done, and only when something failed.
 */
export function useRecommendations(submission) {
  const failed = submission != null && submission.status === "done" && submission.passed_count < submission.total_count;
  return useQuery({
    queryKey: ["recommendations", submission?.id],
    queryFn: () => getRecommendations(submission.id),
    enabled: failed,
    staleTime: 60_000,
  });
}
