// Small HTTP client: adds the token, parses JSON and turns error responses into ApiError.

const TOKEN_KEY = "autograder.token";
export const API_PREFIX = "/api/v1";

let onUnauthorized = () => {};

/** AuthContext registers its logout here, so a 401 anywhere signs the user out. */
export function setUnauthorizedHandler(handler) {
  onUnauthorized = handler;
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  constructor(status, detail, code) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

async function parseError(response) {
  try {
    const body = await response.json();
    return new ApiError(response.status, body.detail ?? "Request failed", body.code);
  } catch {
    return new ApiError(response.status, "Request failed", undefined);
  }
}

/**
 * apiFetch("/courses") or apiFetch("/courses", { method: "POST", body: {...} }).
 * `form` sends application/x-www-form-urlencoded, `formData` sends multipart (file uploads),
 * `raw: true` returns the Response itself (file downloads).
 */
export async function apiFetch(path, { method = "GET", body, form, formData, raw = false } = {}) {
  const headers = {};
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  let payload;
  if (form) {
    payload = new URLSearchParams(form);
  } else if (formData) {
    payload = formData;
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  const response = await fetch(`${API_PREFIX}${path}`, { method, headers, body: payload });

  if (!response.ok) {
    // A 401 on a request that carried a token means the token expired or was revoked.
    if (response.status === 401 && token) onUnauthorized();
    throw await parseError(response);
  }
  if (raw) return response;
  if (response.status === 204) return null;
  return response.json();
}
