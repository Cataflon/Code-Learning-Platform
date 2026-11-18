import { apiFetch } from "./client.js";

export const getLearn = () => apiFetch("/me/learn");
export const listMaterials = (courseId) => apiFetch(`/courses/${courseId}/materials`);
export const getMaterial = (id) => apiFetch(`/materials/${id}`);

/** Multipart upload: file, title, category. A PPTX is converted before the answer comes. */
export function uploadMaterial(courseId, { file, title, category }) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("title", title);
  formData.append("category", category);
  return apiFetch(`/courses/${courseId}/materials`, { method: "POST", formData });
}

export const updateMaterial = (id, data) => apiFetch(`/materials/${id}`, { method: "PATCH", body: data });
export const deleteMaterial = (id) => apiFetch(`/materials/${id}`, { method: "DELETE" });

/** The PDF for the viewer, as a Blob (the request needs the token, so no plain URL). */
export async function fetchPreview(id) {
  const response = await apiFetch(`/materials/${id}/preview`, { raw: true });
  return response.blob();
}

/** Download the original file under its own name. */
export async function downloadOriginal(material) {
  const response = await apiFetch(`/materials/${material.id}/file`, { raw: true });
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = material.original_filename;
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export const getAssignmentMaterials = (assignmentId) => apiFetch(`/assignments/${assignmentId}/materials`);
export const setAssignmentMaterials = (assignmentId, items) =>
  apiFetch(`/assignments/${assignmentId}/materials`, { method: "PUT", body: items });
export const setTestCaseMaterials = (testCaseId, items) =>
  apiFetch(`/test-cases/${testCaseId}/materials`, { method: "PUT", body: items });

export const getRecommendations = (submissionId) => apiFetch(`/submissions/${submissionId}/recommendations`);

/** Where a material opens: the viewer, at a page, with the recommended pages highlighted. */
export function viewerLink(materialId, { page, pages, from } = {}) {
  const params = new URLSearchParams();
  if (page && page > 1) params.set("page", page);
  if (pages) params.set("rec", pages);
  if (from) params.set("from", from);
  const query = params.toString();
  return `/learn/materials/${materialId}${query ? `?${query}` : ""}`;
}
