import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, test, vi } from "vitest";

import { AppRoutes } from "../../App.jsx";
import { homePathFor } from "../../auth/AuthContext.jsx";
import { mockApi, renderApp } from "../../test/utils.jsx";
import AdminInvitesPage from "./AdminInvitesPage.jsx";
import AdminUsersPage from "./AdminUsersPage.jsx";

const ADMIN = { id: 9, full_name: "Ada Admin", email: "admin@example.com", role: "admin" };
const STATS = {
  students: 2,
  teachers: 1,
  admins: 1,
  disabled: 1,
  courses: 1,
  assignments: 3,
  submissions: 12,
  active_invite_codes: 1,
};

function user(id, overrides = {}) {
  return {
    id,
    email: `user${id}@example.com`,
    full_name: `User ${id}`,
    role: "student",
    is_active: true,
    created_at: "2026-11-01T10:00:00Z",
    courses_taught: 0,
    courses_enrolled: 1,
    submissions: 4,
    invite_code: null,
    ...overrides,
  };
}

afterEach(() => vi.restoreAllMocks());

test("admins land on the users page and see the admin menu", () => {
  expect(homePathFor(ADMIN)).toBe("/admin/users");
  mockApi({ "GET /admin/stats": STATS, "GET /admin/users": { items: [], total: 0 } });

  renderApp(<AppRoutes />, { route: "/courses", user: ADMIN });

  expect(screen.getAllByRole("link", { name: /Invite codes/ }).length).toBeGreaterThan(0);
  expect(screen.queryByRole("link", { name: /Dashboard/ })).toBeNull();
});

test("the users list filters, disables an account and shows a temporary password once", async () => {
  vi.spyOn(window, "confirm").mockReturnValue(true);
  const andrei = user(1, { full_name: "Andrei Pop" });
  const { calls } = mockApi({
    "GET /admin/stats": STATS,
    "GET /admin/users": ({ url }) =>
      url.includes("role=teacher")
        ? { items: [user(2, { role: "teacher", full_name: "Maria Ionescu", courses_taught: 2, invite_code: "TEACH-AAAA-BBBB" })], total: 1 }
        : { items: [andrei, user(9, { role: "admin", full_name: "Ada Admin" })], total: 2 },
    "PATCH /admin/users/1": { ...andrei, is_active: false },
    "POST /admin/users/1/reset-password": { temporary_password: "Kx7mPq2RtW9nZa" },
  });
  const u = userEvent.setup();
  renderApp(<AdminUsersPage />, { user: ADMIN });

  const row = (await screen.findByText("Andrei Pop")).closest("tr");
  expect(within(row).getByText("1 enrolled · 4 submissions")).toBeInTheDocument();
  const me = screen.getByText("Ada Admin").closest("tr");
  expect(within(me).getByRole("button", { name: "Disable" })).toBeDisabled(); // not on yourself
  expect(within(me).getByLabelText("Role of Ada Admin")).toBeDisabled();

  await u.click(within(row).getByRole("button", { name: "Disable" }));
  await waitFor(() => expect(calls.some((c) => c.method === "PATCH")).toBe(true));
  expect(JSON.parse(calls.find((c) => c.method === "PATCH").body)).toEqual({ is_active: false });

  await u.click(within(row).getByRole("button", { name: /Reset password/ }));
  expect(await screen.findByRole("dialog", { name: "Temporary password" })).toHaveTextContent("Kx7mPq2RtW9nZa");

  await u.click(screen.getByRole("button", { name: "Done" }));
  await u.selectOptions(screen.getByLabelText("Role"), "teacher");
  expect(await screen.findByText("Maria Ionescu")).toBeInTheDocument();
  expect(screen.getByText("TEACH-AAAA-BBBB")).toBeInTheDocument();
});

test("a new invite code is shown after it is generated, and an active one can be revoked", async () => {
  vi.spyOn(window, "confirm").mockReturnValue(true);
  const active = {
    id: 1,
    code: "TEACH-4KQ7-M2XD",
    note: "Prof. Popescu",
    max_uses: 1,
    uses: 0,
    expires_at: "2026-12-01T10:00:00Z",
    revoked_at: null,
    created_at: "2026-11-18T10:00:00Z",
    created_by_name: "Ada Admin",
    status: "active",
    used_by: [],
  };
  const used = { ...active, id: 2, code: "TEACH-ZZZZ-YYYY", uses: 1, status: "used", used_by: ["Maria Ionescu"] };
  const { calls } = mockApi({
    "GET /admin/invite-codes": [active, used],
    "POST /admin/invite-codes": [201, { ...active, id: 3, code: "TEACH-NEW1-CODE", note: "Prof. Ionescu" }],
    "POST /admin/invite-codes/1/revoke": { ...active, status: "revoked" },
  });
  const u = userEvent.setup();
  renderApp(<AdminInvitesPage />, { user: ADMIN });

  expect(await screen.findByText("TEACH-4KQ7-M2XD")).toBeInTheDocument();
  expect(screen.getByText("Maria Ionescu")).toBeInTheDocument();
  const usedRow = screen.getByText("TEACH-ZZZZ-YYYY").closest("tr");
  expect(within(usedRow).queryByRole("button", { name: "Revoke" })).toBeNull();

  await u.type(screen.getByLabelText("For (optional)"), "Prof. Ionescu");
  await u.selectOptions(screen.getByLabelText("Expires after"), "Never");
  await u.click(screen.getByRole("button", { name: "Generate code" }));

  expect(await screen.findByText("TEACH-NEW1-CODE")).toBeInTheDocument();
  const post = calls.find((c) => c.method === "POST" && c.path === "/admin/invite-codes");
  expect(JSON.parse(post.body)).toEqual({ note: "Prof. Ionescu", max_uses: 1, expires_in_days: null });

  const activeRow = screen.getByText("TEACH-4KQ7-M2XD").closest("tr");
  await u.click(within(activeRow).getByRole("button", { name: "Revoke" }));
  await waitFor(() => expect(calls.some((c) => c.path === "/admin/invite-codes/1/revoke")).toBe(true));
});
