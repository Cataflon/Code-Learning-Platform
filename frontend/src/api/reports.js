import { apiFetch } from "./client.js";

/** The signed-in student's own concept report for one course. */
export const getMyConceptReport = (courseId) => apiFetch(`/courses/${courseId}/reports/concepts/me`);

/** The whole class, per concept (course teacher only). */
export const getClassConceptReport = (courseId) => apiFetch(`/courses/${courseId}/reports/concepts`);
