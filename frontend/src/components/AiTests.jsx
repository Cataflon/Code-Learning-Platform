// AI test generation in the assignment editor (Step 9): the button, the job panel and the drafts.

import { useMutation, useQuery } from "@tanstack/react-query";
import { Check, Pencil, Sparkles, Trash2 } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";

import * as aiApi from "../api/ai.js";
import { deleteTestCase, updateTestCase } from "../api/assignments.js";
import { viewerLink } from "../api/materials.js";
import { FileBadge } from "./MaterialBits.jsx";
import { Button, Card, CardHeader, Chip, FormError } from "./ui.jsx";
import { plural } from "../lib/format.js";

export const POLL_MS = 2000;

const PHASES = {
  queued: "Waiting to start",
  writing: "Proposing test inputs",
  sandbox: "Running in sandbox",
  linking: "Linking materials",
};

export function useAiConfig() {
  return useQuery({ queryKey: ["config"], queryFn: aiApi.getConfig, staleTime: Infinity });
}

/** One generation job, polled every 2 seconds until it is done or failed. */
export function useGenerationJob(jobId, interval = POLL_MS) {
  return useQuery({
    queryKey: ["generation-job", jobId],
    queryFn: () => aiApi.getGenerationJob(jobId),
    enabled: jobId != null,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "done" || status === "error" || query.state.error ? false : interval;
    },
  });
}

/** "Generate tests with AI" and the panel that follows the job. */
export function AiGeneratePanel({ assignmentId, hasStatement, onFinished, interval = POLL_MS }) {
  const [count, setCount] = useState(8);
  const [solution, setSolution] = useState("");
  const [jobId, setJobId] = useState(null);
  const [finishedId, setFinishedId] = useState(null);
  const start = useMutation({
    mutationFn: () => aiApi.generateTests(assignmentId, count, solution),
    onSuccess: (created) => setJobId(created.job_id),
  });
  const job = useGenerationJob(jobId, interval);
  const status = job.data?.status;
  const running = jobId != null && status !== "done" && status !== "error";

  if ((status === "done" || status === "error") && finishedId !== jobId) {
    setFinishedId(jobId);
    onFinished?.();
  }

  return (
    <Card tint="pink">
      <div className="pad grid gap-3">
        <div className="flex flex-wrap items-center gap-3">
          <Sparkles className="h-5 w-5 text-pink" aria-hidden="true" />
          <h2 className="flex-1">Generate tests with AI</h2>
          <label className="flex items-center gap-2 text-sm text-ink-3">
            Tests
            <select
              className="field w-20 py-1"
              value={count}
              onChange={(event) => setCount(Number(event.target.value))}
              disabled={running}
              aria-label="Number of tests to generate"
            >
              {[4, 5, 6, 7, 8, 9, 10, 11, 12].map((n) => (
                <option key={n}>{n}</option>
              ))}
            </select>
          </label>
          <Button
            variant="primary"
            disabled={!hasStatement || running || start.isPending}
            onClick={() => start.mutate()}
          >
            {running ? "Generating…" : "Generate tests with AI"}
          </Button>
        </div>
        <p className="plain text-sm text-ink-3">
          Paste your reference solution and the model only proposes test inputs. Leave it empty and the
          model also writes the solution, plus a second one of its own to cross-check it: tests where the
          two disagree are flagged. Either way the expected outputs come from running a solution in the
          sandbox, never from the model. New tests arrive as drafts and count only after you approve them.
          {!hasStatement && " Save a task statement first."}
        </p>
        <label className="label">
          Your reference solution (optional)
          <textarea
            className="field mono mt-1 min-h-32"
            value={solution}
            onChange={(event) => setSolution(event.target.value)}
            disabled={running}
            spellCheck={false}
            placeholder={"n = abs(int(input()))\nprint(sum(int(d) for d in str(n)))"}
          />
        </label>
        <FormError>{start.isError ? start.error.message : ""}</FormError>
        {jobId != null && job.data && (
          <div role="status" aria-live="polite" className="grid gap-2">
            {running && (
              <>
                <p className="text-ink">
                  {job.data.phase === "writing" && job.data.reference_by === "ai"
                    ? "Writing the solution and the tests"
                    : (PHASES[job.data.phase] ?? "Working")}
                  …
                </p>
                <span className="bar">
                  <i className="animate-pulse" style={{ "--w": `${({ queued: 10, writing: 35, sandbox: 65, linking: 90 })[job.data.phase] ?? 50}%` }} />
                </span>
              </>
            )}
            {status === "done" && (
              <p className="text-ok">
                {plural(job.data.tests_kept ?? 0, "test")} ready for review
                {job.data.tests_proposed > job.data.tests_kept &&
                  ` (${job.data.tests_proposed - job.data.tests_kept} dropped: the solution failed on them)`}
                .
              </p>
            )}
            {status === "error" && <FormError>{job.data.error_message}</FormError>}
          </div>
        )}
      </div>
    </Card>
  );
}

function Block({ label, value }) {
  return (
    <div className="io">
      <div>
        <span>{label}</span>
        <pre className="max-h-32 overflow-auto">{value === "" ? "(empty)" : value}</pre>
      </div>
    </div>
  );
}

function DraftCard({ test, index, onChanged }) {
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState(() => ({
    name: test.name,
    input_data: test.input_data,
    expected_output: test.expected_output,
    is_hidden: test.is_hidden,
    weight: test.weight,
  }));
  const approve = useMutation({ mutationFn: () => aiApi.approveTest(test.id), onSuccess: onChanged });
  const remove = useMutation({ mutationFn: () => deleteTestCase(test.id), onSuccess: onChanged });
  const save = useMutation({
    mutationFn: () => updateTestCase(test.id, { ...form, weight: Number(form.weight) || 1 }),
    onSuccess: () => {
      setEditing(false);
      onChanged();
    },
  });
  const error = approve.error ?? remove.error ?? save.error;
  const set = (field) => (event) =>
    setForm((old) => ({ ...old, [field]: event.target.type === "checkbox" ? event.target.checked : event.target.value }));

  return (
    <li className="grid gap-3 px-6 py-5" aria-label={`Draft ${index + 1}: ${test.name}`}>
      <div className="flex flex-wrap items-center gap-2">
        <b className="text-ink">{test.name}</b>
        <Chip tone="pink">AI draft</Chip>
        {test.is_hidden && <Chip tone="neutral">hidden</Chip>}
        <Chip tone="neutral">weight {test.weight}</Chip>
        {test.ai_check_output != null && <Chip tone="bad">solutions disagree</Chip>}
        {test.concepts.length === 0 && <Chip tone="warn">no concept</Chip>}
        {test.concepts.map((concept) => (
          <Chip key={concept.id}>{concept.name}</Chip>
        ))}
      </div>
      {test.ai_rationale && <p className="plain text-sm text-ink-3">{test.ai_rationale}</p>}
      {editing ? (
        <form
          className="grid gap-3"
          onSubmit={(event) => {
            event.preventDefault();
            save.mutate();
          }}
        >
          <label className="label">
            Name
            <input className="field mt-1" value={form.name} onChange={set("name")} maxLength={120} />
          </label>
          <div className="grid gap-3 md:grid-cols-2">
            <label className="label">
              Input
              <textarea className="field mono mt-1 min-h-20" value={form.input_data} onChange={set("input_data")} />
            </label>
            <label className="label">
              Expected output
              <textarea className="field mono mt-1 min-h-20" value={form.expected_output} onChange={set("expected_output")} />
            </label>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={form.is_hidden} onChange={set("is_hidden")} /> Hidden
            </label>
            <label className="flex items-center gap-2 text-sm">
              Weight
              <input className="field w-20 py-1" type="number" min="1" max="100" value={form.weight} onChange={set("weight")} />
            </label>
            <span className="flex-1" />
            <Button variant="neutral" size="sm" onClick={() => setEditing(false)}>
              Cancel
            </Button>
            <Button type="submit" size="sm" disabled={!form.name.trim() || save.isPending}>
              Save
            </Button>
          </div>
        </form>
      ) : (
        <div className="grid gap-2 md:grid-cols-2">
          <Block label="Input" value={test.input_data} />
          <Block label="Expected output (from the sandbox)" value={test.expected_output} />
          {test.ai_check_output != null && (
            <div className="md:col-span-2">
              <Block label="The second AI solution printed instead: check which one is right" value={test.ai_check_output} />
            </div>
          )}
        </div>
      )}
      {test.materials?.length > 0 && (
        <p className="flex flex-wrap items-center gap-2 text-sm text-ink-3">
          Proposed material:
          {test.materials.map((link) => (
            <Link
              key={link.material_id}
              to={viewerLink(link.material_id, { page: link.first_page, pages: link.pages })}
              className="flex items-center gap-2 text-accent-strong hover:underline"
            >
              <FileBadge type={link.file_type} />
              {link.title}
              {link.pages && <span className="pages">pages {link.pages}</span>}
            </Link>
          ))}
        </p>
      )}
      <FormError>{error?.message}</FormError>
      {!editing && (
        <div className="flex flex-wrap gap-2">
          <Button size="sm" onClick={() => approve.mutate()} disabled={approve.isPending}>
            <Check className="h-4 w-4" aria-hidden="true" />
            Approve
          </Button>
          <Button variant="neutral" size="sm" onClick={() => setEditing(true)}>
            <Pencil className="h-4 w-4" aria-hidden="true" />
            Edit
          </Button>
          <Button
            variant="danger"
            size="sm"
            disabled={remove.isPending}
            onClick={() => window.confirm(`Delete the draft “${test.name}”?`) && remove.mutate()}
          >
            <Trash2 className="h-4 w-4" aria-hidden="true" />
            Delete
          </Button>
        </div>
      )}
    </li>
  );
}

function ReferenceSolution({ jobId }) {
  const job = useGenerationJob(jobId);
  if (!job.data?.reference_code) return null;
  const byAi = job.data.reference_by === "ai";
  return (
    <details className="dash-top px-6 py-4">
      <summary className="cursor-pointer text-sm text-accent-strong">
        {byAi ? "Solution written by the AI: check it before approving" : "Your reference solution"} ·{" "}
        {job.data.model} · {job.data.input_tokens + job.data.output_tokens} tokens
      </summary>
      <pre className="io mt-3 max-h-80 overflow-auto p-4 font-mono text-sm">{job.data.reference_code}</pre>
      {job.data.check_code && (
        <>
          <p className="mt-4 text-sm text-ink-3">Second AI solution, written separately to cross-check the first:</p>
          <pre className="io mt-2 max-h-80 overflow-auto p-4 font-mono text-sm">{job.data.check_code}</pre>
        </>
      )}
    </details>
  );
}

/** The AI drafts of an assignment: review them one by one or approve them all. */
export function DraftsPanel({ assignmentId, drafts, onChanged }) {
  const approveAll = useMutation({ mutationFn: () => aiApi.approveAllTests(assignmentId), onSuccess: onChanged });
  if (drafts.length === 0) return null;
  const jobIds = [...new Set(drafts.map((test) => test.generation_job_id).filter(Boolean))];

  return (
    <Card tint="pink">
      <CardHeader
        title="AI tests to review"
        subtitle={`${plural(drafts.length, "draft")} left. Drafts do not count and students do not see them.`}
        right={
          <Button size="sm" onClick={() => approveAll.mutate()} disabled={approveAll.isPending}>
            Approve all
          </Button>
        }
      />
      <FormError>{approveAll.isError ? approveAll.error.message : ""}</FormError>
      <ul className="sep">
        {drafts.map((test, index) => (
          <DraftCard key={test.id} test={test} index={index} onChanged={onChanged} />
        ))}
      </ul>
      {jobIds.map((id) => (
        <ReferenceSolution key={id} jobId={id} />
      ))}
    </Card>
  );
}
