import { apiFetch } from "./client.js";

export const createSubmission = (assignmentId, code) =>
  apiFetch(`/assignments/${assignmentId}/submissions`, { method: "POST", body: { code } });

export const listSubmissions = (assignmentId) => apiFetch(`/assignments/${assignmentId}/submissions`);

export const getSubmission = (id) => apiFetch(`/submissions/${id}`);
