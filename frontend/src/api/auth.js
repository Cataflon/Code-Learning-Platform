import { apiFetch } from "./client.js";

/** The backend uses the standard OAuth2 form: the email travels in the `username` field. */
export function login(email, password) {
  return apiFetch("/auth/login", { method: "POST", form: { username: email, password } });
}

export function register(data) {
  return apiFetch("/auth/register", { method: "POST", body: data });
}

export function getMe() {
  return apiFetch("/users/me");
}

export function updateMe(fullName) {
  return apiFetch("/users/me", { method: "PATCH", body: { full_name: fullName } });
}

export function changePassword(currentPassword, newPassword) {
  return apiFetch("/users/me/password", {
    method: "POST",
    body: { current_password: currentPassword, new_password: newPassword },
  });
}
