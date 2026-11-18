import { apiFetch } from "./client.js";

/** { ai_available } - whether the server has an Anthropic API key configured. */
export const getConfig = () => apiFetch("/config");

export const generateTests = (assignmentId, count) =>
  apiFetch(`/assignments/${assignmentId}/generate-tests`, { method: "POST", body: { count } });

export const getGenerationJob = (jobId) => apiFetch(`/generation-jobs/${jobId}`);

export const approveTest = (testCaseId) => apiFetch(`/test-cases/${testCaseId}/approve`, { method: "POST" });

export const approveAllTests = (assignmentId) =>
  apiFetch(`/assignments/${assignmentId}/tests/approve-all`, { method: "POST" });

export const reindexMaterial = (materialId) => apiFetch(`/materials/${materialId}/reindex`, { method: "POST" });
