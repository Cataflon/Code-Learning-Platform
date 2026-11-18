import { apiFetch } from "./client.js";

/** { ai_available } - whether the server has a key for its AI provider (NVIDIA or Anthropic). */
export const getConfig = () => apiFetch("/config");

/** The teacher's reference solution produces the expected outputs; the model only proposes inputs. */
export const generateTests = (assignmentId, count, referenceSolution) =>
  apiFetch(`/assignments/${assignmentId}/generate-tests`, {
    method: "POST",
    body: { count, reference_solution: referenceSolution },
  });

export const getGenerationJob = (jobId) => apiFetch(`/generation-jobs/${jobId}`);

export const approveTest = (testCaseId) => apiFetch(`/test-cases/${testCaseId}/approve`, { method: "POST" });

export const approveAllTests = (assignmentId) =>
  apiFetch(`/assignments/${assignmentId}/tests/approve-all`, { method: "POST" });

export const reindexMaterial = (materialId) => apiFetch(`/materials/${materialId}/reindex`, { method: "POST" });
