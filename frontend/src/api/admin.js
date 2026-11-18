import { apiFetch } from "./client.js";

// The technical admin (decision D30): accounts and invite codes.

function query(params) {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== "" && value != null) search.set(key, value);
  }
  const text = search.toString();
  return text ? `?${text}` : "";
}

export const getAdminStats = () => apiFetch("/admin/stats");
export const listUsers = (params = {}) => apiFetch(`/admin/users${query(params)}`);
export const updateUser = (id, data) => apiFetch(`/admin/users/${id}`, { method: "PATCH", body: data });
export const resetPassword = (id) => apiFetch(`/admin/users/${id}/reset-password`, { method: "POST" });

export const listInviteCodes = () => apiFetch("/admin/invite-codes");
export const createInviteCode = (data) => apiFetch("/admin/invite-codes", { method: "POST", body: data });
export const revokeInviteCode = (id) => apiFetch(`/admin/invite-codes/${id}/revoke`, { method: "POST" });
