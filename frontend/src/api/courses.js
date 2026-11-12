import { apiFetch } from "./client.js";

export const listCourses = () => apiFetch("/courses");
export const getCourse = (id) => apiFetch(`/courses/${id}`);
export const createCourse = (data) => apiFetch("/courses", { method: "POST", body: data });
export const updateCourse = (id, data) => apiFetch(`/courses/${id}`, { method: "PATCH", body: data });
export const deleteCourse = (id) => apiFetch(`/courses/${id}`, { method: "DELETE" });
export const joinCourse = (joinCode) =>
  apiFetch("/courses/join", { method: "POST", body: { join_code: joinCode } });
export const leaveCourse = (id) => apiFetch(`/courses/${id}/enrollment`, { method: "DELETE" });
export const newJoinCode = (id) => apiFetch(`/courses/${id}/join-code`, { method: "POST" });

export const listConcepts = (courseId) => apiFetch(`/courses/${courseId}/concepts`);
export const createConcept = (courseId, name) =>
  apiFetch(`/courses/${courseId}/concepts`, { method: "POST", body: { name } });
