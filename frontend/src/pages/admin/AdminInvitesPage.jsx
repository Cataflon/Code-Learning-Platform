// Invite codes for teachers (decision D30): the admin makes one per future teacher (or one for
// a few), sends it, and sees who used it. Registering as a teacher needs a code.

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Copy, KeyRound, Plus } from "lucide-react";
import { useState } from "react";

import * as adminApi from "../../api/admin.js";
import { EmptyState, ErrorState, LoadingState } from "../../components/states.jsx";
import { Button, Card, CardHeader, Chip, FormError, inputClass, PageHeader, TextField } from "../../components/ui.jsx";
import { formatDay } from "../../lib/format.js";

const STATUS_TONE = { active: "ok", used: "neutral", expired: "warn", revoked: "bad" };
const EXPIRY = [
  { value: "7", label: "7 days" },
  { value: "14", label: "14 days" },
  { value: "30", label: "30 days" },
  { value: "90", label: "90 days" },
  { value: "", label: "Never" },
];

function CopyButton({ text, label = "Copy" }) {
  const [copied, setCopied] = useState(false);
  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  }
  return (
    <Button variant="neutral" size="sm" onClick={copy} aria-label={`${label} ${text}`}>
      <Copy className="h-4 w-4" aria-hidden="true" />
      {copied ? "Copied" : label}
    </Button>
  );
}

function NewCodeForm({ onCreated }) {
  const [note, setNote] = useState("");
  const [uses, setUses] = useState("1");
  const [expires, setExpires] = useState("14");
  const [created, setCreated] = useState(null);
  const create = useMutation({
    mutationFn: () =>
      adminApi.createInviteCode({
        note,
        max_uses: Number(uses) || 1,
        expires_in_days: expires ? Number(expires) : null,
      }),
    onSuccess: (code) => {
      setCreated(code);
      setNote("");
      onCreated();
    },
  });

  return (
    <Card tint="pink">
      <CardHeader icon={KeyRound} title="New invite code" subtitle="Send it to a future teacher; they enter it when they create their account." />
      <form
        className="flex flex-wrap items-end gap-4 px-6 py-5"
        onSubmit={(event) => {
          event.preventDefault();
          create.mutate();
        }}
      >
        <TextField
          label="For (optional)"
          className="min-w-56 flex-1"
          placeholder="e.g. Prof. Popescu, Algorithms"
          value={note}
          onChange={(event) => setNote(event.target.value)}
          maxLength={200}
        />
        <label className="label">
          Uses
          <input
            className={`${inputClass} mt-1 w-24`}
            type="number"
            min="1"
            max="100"
            value={uses}
            onChange={(event) => setUses(event.target.value)}
          />
        </label>
        <label className="label">
          Expires after
          <select className={`${inputClass} mt-1 w-36`} value={expires} onChange={(event) => setExpires(event.target.value)}>
            {EXPIRY.map((option) => (
              <option key={option.label} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <Button type="submit" disabled={create.isPending}>
          <Plus className="h-4 w-4" aria-hidden="true" />
          Generate code
        </Button>
      </form>
      <div className="px-6 pb-5">
        <FormError>{create.isError ? create.error.message : ""}</FormError>
        {created && (
          <div className="flex flex-wrap items-center gap-3" role="status">
            <span className="text-sm text-ink-3">New code{created.note ? ` for ${created.note}` : ""}:</span>
            <code className="io px-4 py-2 font-mono text-lg tracking-widest text-ink">{created.code}</code>
            <CopyButton text={created.code} />
          </div>
        )}
      </div>
    </Card>
  );
}

/** Admin: generate, list and revoke the invite codes for teachers. */
export default function AdminInvitesPage() {
  const queryClient = useQueryClient();
  const codes = useQuery({ queryKey: ["invite-codes"], queryFn: adminApi.listInviteCodes });
  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ["invite-codes"] });
    queryClient.invalidateQueries({ queryKey: ["admin-stats"] });
  };
  const revoke = useMutation({ mutationFn: adminApi.revokeInviteCode, onSuccess: refresh });

  return (
    <>
      <PageHeader title="Invite codes" subtitle="Only people with a code can create a teacher account. Students register freely." />
      <div className="stack">
        <NewCodeForm onCreated={refresh} />
        <Card className="overflow-hidden">
          <CardHeader icon={KeyRound} title="All codes" />
          <FormError>{revoke.isError ? revoke.error.message : ""}</FormError>
          {codes.isPending && <LoadingState />}
          {codes.isError && <ErrorState error={codes.error} onRetry={codes.refetch} />}
          {codes.data?.length === 0 && <EmptyState title="No codes yet">Generate the first one above.</EmptyState>}
          {codes.data?.length > 0 && (
            <div className="overflow-x-auto">
              <table className="tbl min-w-[860px]">
                <thead>
                  <tr>
                    <th>Code</th>
                    <th>For</th>
                    <th>Status</th>
                    <th>Used</th>
                    <th>Expires</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {codes.data.map((code) => (
                    <tr key={code.id}>
                      <td>
                        <b className="font-mono tracking-wider">{code.code}</b>
                        <span className="block font-plain text-xs text-ink-3">
                          {formatDay(code.created_at)}
                          {code.created_by_name && ` by ${code.created_by_name}`}
                        </span>
                      </td>
                      <td className="font-plain text-sm text-ink-2">{code.note || "–"}</td>
                      <td>
                        <Chip tone={STATUS_TONE[code.status]}>{code.status}</Chip>
                      </td>
                      <td className="font-plain text-sm text-ink-2">
                        {code.uses} of {code.max_uses}
                        {code.used_by.length > 0 && (
                          <span className="block text-xs text-ink-3">{code.used_by.join(", ")}</span>
                        )}
                      </td>
                      <td className="whitespace-nowrap font-plain text-sm text-ink-3">
                        {code.expires_at ? formatDay(code.expires_at) : "never"}
                      </td>
                      <td>
                        {code.status === "active" && (
                          <span className="flex justify-end gap-1">
                            <CopyButton text={code.code} />
                            <Button
                              variant="danger"
                              size="sm"
                              disabled={revoke.isPending}
                              onClick={() =>
                                window.confirm(`Revoke ${code.code}? Nobody can register with it after this.`) &&
                                revoke.mutate(code.id)
                              }
                            >
                              Revoke
                            </Button>
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </div>
    </>
  );
}
