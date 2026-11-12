// Helpers for rendering components that need the router, TanStack Query and an auth state.

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";

import { AuthContext } from "../auth/AuthContext.jsx";

export const STUDENT = { id: 1, full_name: "Andrei Pop", email: "andrei@example.com", role: "student" };
export const TEACHER = { id: 2, full_name: "Dr. Maria Ionescu", email: "maria@example.com", role: "teacher" };

export function renderApp(ui, { route = "/", user = null, status = "ready", auth = {} } = {}) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  const authValue = {
    user,
    status,
    login: vi.fn(),
    logout: vi.fn(),
    setUser: vi.fn(),
    ...auth,
  };
  const result = render(
    <QueryClientProvider client={queryClient}>
      <AuthContext.Provider value={authValue}>
        <MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter>
      </AuthContext.Provider>
    </QueryClientProvider>,
  );
  return { ...result, authValue, queryClient };
}

/** A fake fetch Response carrying JSON. */
export function jsonResponse(body, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  };
}

/**
 * Replace global fetch with a router: keys are "METHOD /path" (path without /api/v1, query
 * string ignored), values are a body, a [status, body] pair or a function returning either.
 */
export function mockApi(routes) {
  const calls = [];
  const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (url, options = {}) => {
    const method = options.method ?? "GET";
    const path = String(url).replace("/api/v1", "").split("?")[0];
    calls.push({ method, path, url: String(url), body: options.body });
    const key = `${method} ${path}`;
    if (!(key in routes)) return jsonResponse({ detail: `No mock for ${key}`, code: "not_found" }, 404);
    let value = routes[key];
    if (typeof value === "function") value = value({ url: String(url), body: options.body });
    if (Array.isArray(value) && typeof value[0] === "number" && value.length === 2) {
      return jsonResponse(value[1], value[0]);
    }
    return jsonResponse(value);
  });
  return { calls, fetchMock };
}
