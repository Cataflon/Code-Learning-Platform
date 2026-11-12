import { useQuery } from "@tanstack/react-query";

import { getSubmission } from "../api/submissions.js";

export const POLL_INTERVAL_MS = 1000;

export function isFinal(status) {
  return status === "done" || status === "error";
}

/**
 * One submission, polled once a second while it is queued or running.
 * `refetchInterval` returns false at a final status, which stops the polling.
 */
export function useSubmission(submissionId, { interval = POLL_INTERVAL_MS } = {}) {
  return useQuery({
    queryKey: ["submission", submissionId],
    queryFn: () => getSubmission(submissionId),
    enabled: submissionId != null,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (query.state.error || isFinal(status)) return false;
      return interval;
    },
    // A finished submission never changes, so it never needs refetching.
    staleTime: (query) => (isFinal(query.state.data?.status) ? Infinity : 0),
  });
}
