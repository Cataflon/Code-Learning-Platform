// The technical admin's list of every account (decision D30): search, filter, change the role,
// disable or enable an account, and give someone a temporary password.

import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Copy, KeyRound, Search, Users } from "lucide-react";
import { useDeferredValue, useState } from "react";

import * as adminApi from "../../api/admin.js";
import { useAuth } from "../../auth/AuthContext.jsx";
import Modal from "../../components/Modal.jsx";
import Pagination from "../../components/Pagination.jsx";
import { EmptyState, ErrorState, LoadingState } from "../../components/states.jsx";
import { Avatar, Button, Card, CardHeader, Chip, FormError, inputClass, PageHeader, Stat } from "../../components/ui.jsx";
import { formatDay } from "../../lib/format.js";

const PAGE_SIZE = 25;
const ROLE_TONE = { student: "info", teacher: "accent", admin: "pink" };

function StatsLine() {
  const stats = useQuery({ queryKey: ["admin-stats"], queryFn: adminApi.getAdminStats });
  if (!stats.data) return null;
  const s = stats.data;
  return (
    <div className="flex flex-wrap gap-10">
      <Stat value={s.students} label="students" />
      <Stat value={s.teachers} label="teachers" />
      <Stat value={s.courses} label="courses" />
      <Stat value={s.submissions} label="submissions" />
      <Stat value={s.disabled} label="disabled" tone={s.disabled ? "bad" : undefined} />
    </div>
  );
}

function PasswordDialog({ user, password, onClose }) {
  const [copied, setCopied] = useState(false);
  async function copy() {
    try {
      await navigator.clipboard.writeText(password);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  }
  return (
    <Modal
      title="Temporary password"
      subtitle={`For ${user.full_name} (${user.email}). It is shown only now: pass it on and ask them to change it from Profile.`}
      onClose={onClose}
      footer={<Button onClick={onClose}>Done</Button>}
    >
      <div className="flex flex-wrap items-center gap-3 px-6 py-6">
        <code className="io flex-1 px-4 py-3 font-mono text-lg tracking-wider text-ink">{password}</code>
        <Button variant="neutral" onClick={copy}>
          <Copy className="h-4 w-4" aria-hidden="true" />
          {copied ? "Copied" : "Copy"}
        </Button>
      </div>
    </Modal>
  );
}

function UserRow({ user, isMe, onChanged }) {
  const [password, setPassword] = useState(null);
  const update = useMutation({
    mutationFn: (data) => adminApi.updateUser(user.id, data),
    onSuccess: onChanged,
  });
  const reset = useMutation({
    mutationFn: () => adminApi.resetPassword(user.id),
    onSuccess: (data) => setPassword(data.temporary_password),
  });
  const error = update.error ?? reset.error;

  return (
    <tr className={user.is_active ? "" : "opacity-60"}>
      <td>
        <span className="flex items-center gap-3">
          <Avatar name={user.full_name} />
          <span className="min-w-0">
            <b className="block truncate">
              {user.full_name}
              {isMe && <span className="ml-2 text-sm font-normal text-ink-3">(you)</span>}
            </b>
            <span className="block truncate font-plain text-sm text-ink-3">{user.email}</span>
            <span className="block font-plain text-xs text-ink-3">joined {formatDay(user.created_at)}</span>
          </span>
        </span>
        {error && (
          <div className="mt-2">
            <FormError>{error.message}</FormError>
          </div>
        )}
      </td>
      <td>
        <select
          className={`${inputClass} w-32 py-1`}
          value={user.role}
          disabled={isMe || update.isPending}
          aria-label={`Role of ${user.full_name}`}
          onChange={(event) => {
            const role = event.target.value;
            if (window.confirm(`Make ${user.full_name} a ${role}?`)) update.mutate({ role });
          }}
        >
          <option value="student">student</option>
          <option value="teacher">teacher</option>
          <option value="admin">admin</option>
        </select>
      </td>
      <td>
        <Chip tone={user.is_active ? "ok" : "bad"}>{user.is_active ? "active" : "disabled"}</Chip>
      </td>
      <td className="font-plain text-sm text-ink-2">
        {user.role === "teacher" && `${user.courses_taught} taught`}
        {user.role === "student" && `${user.courses_enrolled} enrolled · ${user.submissions} submissions`}
        {user.role === "admin" && "–"}
        {user.invite_code && <span className="block font-mono text-xs text-ink-3">{user.invite_code}</span>}
      </td>
      <td>
        <span className="flex justify-end gap-1 whitespace-nowrap">
          <Button
            variant="neutral"
            size="sm"
            aria-label={`Reset password of ${user.full_name}`}
            title="Give a new temporary password"
            disabled={isMe || reset.isPending}
            onClick={() =>
              window.confirm(`Give ${user.full_name} a new temporary password? The current one stops working.`) &&
              reset.mutate()
            }
          >
            <KeyRound className="h-4 w-4" aria-hidden="true" />
            Reset
          </Button>
          <Button
            variant={user.is_active ? "danger" : "primary"}
            size="sm"
            disabled={isMe || update.isPending}
            onClick={() =>
              user.is_active
                ? window.confirm(`Disable ${user.full_name}? They will be signed out and cannot sign in.`) &&
                  update.mutate({ is_active: false })
                : update.mutate({ is_active: true })
            }
          >
            {user.is_active ? "Disable" : "Enable"}
          </Button>
        </span>
      </td>
      {password && <PasswordDialog user={user} password={password} onClose={() => setPassword(null)} />}
    </tr>
  );
}

/** Admin: every account on the platform. */
export default function AdminUsersPage() {
  const { user: me } = useAuth();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [role, setRole] = useState("");
  const [active, setActive] = useState("");
  const [page, setPage] = useState(1);
  const q = useDeferredValue(search.trim());
  const params = { q, role, active, limit: PAGE_SIZE, offset: (page - 1) * PAGE_SIZE };
  const users = useQuery({
    queryKey: ["admin-users", params],
    queryFn: () => adminApi.listUsers(params),
    placeholderData: keepPreviousData,
  });
  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ["admin-users"] });
    queryClient.invalidateQueries({ queryKey: ["admin-stats"] });
  };
  const filter = (setter) => (event) => {
    setter(event.target.value);
    setPage(1);
  };

  return (
    <>
      <PageHeader title="Users" subtitle="Every account on the platform. Course content stays with the teachers." right={<StatsLine />} />
      <Card className="overflow-hidden">
        <CardHeader icon={Users} title="Accounts" subtitle={users.data ? `${users.data.total} found` : undefined} />
        <div className="flex flex-wrap items-end gap-4 px-6 py-4">
          <label className="relative min-w-60 flex-1">
            <span className="sr-only">Search by name or email</span>
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-3" aria-hidden="true" />
            <input
              className={`${inputClass} pl-9`}
              placeholder="Search by name or email"
              value={search}
              onChange={filter(setSearch)}
            />
          </label>
          <select className={`${inputClass} w-40`} value={role} onChange={filter(setRole)} aria-label="Role">
            <option value="">All roles</option>
            <option value="student">Students</option>
            <option value="teacher">Teachers</option>
            <option value="admin">Admins</option>
          </select>
          <select className={`${inputClass} w-40`} value={active} onChange={filter(setActive)} aria-label="Status">
            <option value="">Any status</option>
            <option value="true">Active</option>
            <option value="false">Disabled</option>
          </select>
        </div>
        {users.isPending && <LoadingState />}
        {users.isError && <ErrorState error={users.error} onRetry={users.refetch} />}
        {users.data?.items.length === 0 && <EmptyState title="No account matches">Try another search.</EmptyState>}
        {users.data?.items.length > 0 && (
          <div className="overflow-x-auto">
            <table className="tbl min-w-[760px]">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Activity</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {users.data.items.map((user) => (
                  <UserRow key={user.id} user={user} isMe={user.id === me.id} onChanged={refresh} />
                ))}
              </tbody>
            </table>
          </div>
        )}
        {users.data && (
          <Pagination page={page} pageSize={PAGE_SIZE} total={users.data.total} onPageChange={setPage} />
        )}
      </Card>
    </>
  );
}
