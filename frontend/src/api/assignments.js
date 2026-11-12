import { apiFetch } from "./client.js";

export const listAssignments = (courseId) => apiFetch(`/courses/${courseId}/assignments`);
export const getAssignment = (id) => apiFetch(`/assignments/${id}`);
export const createAssignment = (courseId, data) =>
  apiFetch(`/courses/${courseId}/assignments`, { method: "POST", body: data });
export const updateAssignment = (id, data) =>
  apiFetch(`/assignments/${id}`, { method: "PATCH", body: data });
export const deleteAssignment = (id) => apiFetch(`/assignments/${id}`, { method: "DELETE" });

export const listTestCases = (assignmentId) => apiFetch(`/assignments/${assignmentId}/test-cases`);
export const createTestCase = (assignmentId, data) =>
  apiFetch(`/assignments/${assignmentId}/test-cases`, { method: "POST", body: data });
export const updateTestCase = (id, data) =>
  apiFetch(`/test-cases/${id}`, { method: "PATCH", body: data });
export const deleteTestCase = (id) => apiFetch(`/test-cases/${id}`, { method: "DELETE" });
