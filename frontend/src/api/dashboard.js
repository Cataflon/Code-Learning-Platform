import { apiFetch } from "./client.js";

export const getDashboard = () => apiFetch("/me/dashboard");
export const getActivity = (weeks = 14) => apiFetch(`/users/me/activity?weeks=${weeks}`);
export const getAssignmentStats = (assignmentId) => apiFetch(`/assignments/${assignmentId}/stats`);
export const getCourseStats = (courseId) => apiFetch(`/courses/${courseId}/stats`);
