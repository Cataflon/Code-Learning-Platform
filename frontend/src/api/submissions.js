import { apiFetch } from "./client.js";

export const createSubmission = (assignmentId, code) =>
  apiFetch(`/assignments/${assignmentId}/submissions`, { method: "POST", body: { code } });

/**
 * A page of submissions: { items, total, page, page_size, counts }.
 * params: verdict (all|correct|partial|wrong|running), q, page, page_size.
 */
export function listSubmissions(assignmentId, params = {}) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") query.set(key, value);
  }
  const suffix = query.size ? `?${query}` : "";
  return apiFetch(`/assignments/${assignmentId}/submissions${suffix}`);
}

export const getSubmission = (id) => apiFetch(`/submissions/${id}`);
