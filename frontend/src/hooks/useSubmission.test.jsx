import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import * as submissionsApi from "../api/submissions.js";
import { useSubmission } from "./useSubmission.js";

function wrapper({ children }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

test("polls while the submission runs and stops at a final status", async () => {
  const responses = [
    { id: 5, status: "queued" },
    { id: 5, status: "running" },
    { id: 5, status: "done", score: 75 },
  ];
  const getSubmission = vi
    .spyOn(submissionsApi, "getSubmission")
    .mockImplementation(async () => responses.shift() ?? { id: 5, status: "done", score: 75 });

  const { result } = renderHook(() => useSubmission(5, { interval: 20 }), { wrapper });

  await waitFor(() => expect(result.current.data?.status).toBe("done"));
  expect(getSubmission).toHaveBeenCalledTimes(3);
  await sleep(120); // several intervals later: no more requests
  expect(getSubmission).toHaveBeenCalledTimes(3);
});

test("stops polling when the submission ends in error", async () => {
  const getSubmission = vi
    .spyOn(submissionsApi, "getSubmission")
    .mockResolvedValue({ id: 6, status: "error", error_message: "boom" });

  const { result } = renderHook(() => useSubmission(6, { interval: 20 }), { wrapper });

  await waitFor(() => expect(result.current.data?.status).toBe("error"));
  await sleep(100);
  expect(getSubmission).toHaveBeenCalledTimes(1);
});

test("does nothing without a submission id", async () => {
  const getSubmission = vi.spyOn(submissionsApi, "getSubmission");

  renderHook(() => useSubmission(null), { wrapper });
  await sleep(30);

  expect(getSubmission).not.toHaveBeenCalled();
});
