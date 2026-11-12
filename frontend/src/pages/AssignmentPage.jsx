import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Eye, List, MessageSquare, Play, Target } from "lucide-react";
import { lazy, Suspense, useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import { Link, useParams } from "react-router-dom";

import { getAssignment, listTestCases } from "../api/assignments.js";
import { createSubmission, listSubmissions } from "../api/submissions.js";
import { ErrorState, LoadingState } from "../components/states.jsx";
import StatusBadge from "../components/StatusBadge.jsx";
import TestResultRow from "../components/TestResultRow.jsx";
import { Button, Card, CardHeader, Chip, FormError, IconBadge, PageHeader } from "../components/ui.jsx";
import VerdictSquares from "../components/VerdictSquares.jsx";
import { isFinal, useSubmission } from "../hooks/useSubmission.js";
import { capitalize, formatDay, formatSeconds, ordinal, timeAgo } from "../lib/format.js";

// Monaco is large: load it only when this page is opened.
const CodeEditor = lazy(() => import("../components/CodeEditor.jsx"));

const STARTER_CODE = "# Read the input with input() and print the answer with print()\n";

function draftKey(assignmentId) {
  return `autograder.draft.${assignmentId}`;
}

function scoreColor(score) {
  if (score === 100) return "text-pass";
  if (score === 0) return "text-fail";
  return "text-warn";
}

function ProblemCard({ assignment, examples }) {
  return (
    <Card>
      <CardHeader icon={MessageSquare} title="Problem" border={false} />
      <div className="space-y-5 px-7 pb-7">
        {/* react-markdown never renders raw HTML, so a description cannot inject scripts. */}
        <div className="space-y-3 leading-relaxed text-ink/90 [&_code]:rounded [&_code]:bg-raised [&_code]:px-1.5 [&_code]:font-mono [&_code]:text-sm [&_li]:ml-5 [&_li]:list-disc">
          <ReactMarkdown>{assignment.description || "No description yet."}</ReactMarkdown>
        </div>
        {examples.slice(0, 2).map((example) => (
          <div key={example.id} className="grid grid-cols-2 gap-3">
            <div className="rounded-lg border border-line bg-raised px-4 py-3">
              <div className="text-sm text-muted">Input</div>
              <pre className="mt-1 whitespace-pre-wrap font-mono">{example.input_data.trim() || "(empty)"}</pre>
            </div>
            <div className="rounded-lg border border-line bg-raised px-4 py-3">
              <div className="text-sm text-muted">Output</div>
              <pre className="mt-1 whitespace-pre-wrap font-mono">{example.expected_output.trim() || "(empty)"}</pre>
            </div>
          </div>
        ))}
        <div className="flex justify-between">
          <span className="text-muted">Libraries</span>
          <span>standard only</span>
        </div>
        {assignment.hidden_test_count > 0 && (
          <p className="flex gap-3 rounded-lg border border-accent/50 bg-accent-tint px-4 py-3 text-sm text-accent-soft">
            <Eye className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
            Some tests are hidden. You see whether they passed and which concept they check, not
            their data.
          </p>
        )}
      </div>
    </Card>
  );
}

function AttemptsCard({ attempts, activeId, onSelect }) {
  return (
    <Card>
      <CardHeader icon={List} title="Your attempts" />
      {attempts.length === 0 ? (
        <p className="px-7 py-6 text-sm text-muted">No attempts yet. Your results will appear here.</p>
      ) : (
        <ul>
          {attempts.map((attempt) => (
            <li key={attempt.id} className="border-b border-line last:border-b-0">
              <button
                type="button"
                onClick={() => onSelect(attempt.id)}
                aria-current={attempt.id === activeId ? "true" : undefined}
                className={`flex w-full items-center gap-4 px-7 py-4 text-left hover:bg-raised ${
                  attempt.id === activeId ? "bg-accent-tint/60" : ""
                }`}
              >
                <span className="flex-1">
                  <span className="block font-semibold">Attempt {attempt.attempt_number}</span>
                  <span className="block text-sm text-muted">{formatDay(attempt.created_at)}</span>
                </span>
                <VerdictSquares verdicts={attempt.verdicts} total={attempt.total_count} />
                <span className="w-12 text-right font-semibold">
                  {attempt.score != null ? `${attempt.score}%` : "–"}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

function ResultCard({ submission }) {
  const running = !isFinal(submission.status);
  const firstPending = submission.results.findIndex((result) => result.verdict == null);

  return (
    <Card aria-live="polite">
      <header className="flex flex-wrap items-center gap-4 px-7 py-6">
        <IconBadge icon={Target} />
        <div className="flex-1">
          <h2 className="text-lg font-semibold">Result of attempt {submission.attempt_number}</h2>
          <p className="text-sm text-muted">{timeAgo(submission.created_at)}</p>
        </div>
        {running && <StatusBadge status={submission.status} />}
        <VerdictSquares verdicts={submission.verdicts} total={submission.total_count} large />
        <div className="w-28 text-right">
          <div className={`text-4xl font-bold ${submission.score != null ? scoreColor(submission.score) : "text-muted"}`}>
            {submission.score != null ? `${submission.score}%` : "–"}
          </div>
          <div className="text-sm text-muted">
            {submission.passed_count} of {submission.total_count} passed
          </div>
        </div>
      </header>
      {submission.status === "error" && (
        <div className="px-7 pb-5">
          <FormError>{submission.error_message ?? "This submission could not be evaluated."}</FormError>
        </div>
      )}
      <ul>
        {submission.results.map((result, index) => (
          <TestResultRow
            key={result.test_case_id}
            result={result}
            running={submission.status === "running" && index === firstPending}
          />
        ))}
      </ul>
    </Card>
  );
}

export default function AssignmentPage() {
  const assignmentId = Number(useParams().assignmentId);
  const queryClient = useQueryClient();

  const assignmentQuery = useQuery({
    queryKey: ["assignment", assignmentId],
    queryFn: () => getAssignment(assignmentId),
  });
  const testsQuery = useQuery({
    queryKey: ["test-cases", assignmentId],
    queryFn: () => listTestCases(assignmentId),
  });
  const attemptsQuery = useQuery({
    queryKey: ["submissions", assignmentId],
    queryFn: () => listSubmissions(assignmentId),
  });

  // The draft lives only in this browser (localStorage); the server never sees it.
  const [code, setCode] = useState(() => localStorage.getItem(draftKey(assignmentId)) ?? STARTER_CODE);
  useEffect(() => {
    localStorage.setItem(draftKey(assignmentId), code);
  }, [assignmentId, code]);

  const attempts = attemptsQuery.data ?? [];
  const [selectedId, setSelectedId] = useState(null);
  const activeId = selectedId ?? attempts[0]?.id ?? null;
  const submissionQuery = useSubmission(activeId);
  const submission = submissionQuery.data;

  const submit = useMutation({
    mutationFn: () => createSubmission(assignmentId, code),
    onSuccess: (created) => {
      queryClient.setQueryData(["submission", created.id], created);
      setSelectedId(created.id);
      queryClient.invalidateQueries({ queryKey: ["submissions", assignmentId] });
      queryClient.invalidateQueries({ queryKey: ["assignment", assignmentId] });
    },
  });

  // When the watched submission finishes, refresh the attempts list (squares and score).
  const finishedId = submission && isFinal(submission.status) ? submission.id : null;
  useEffect(() => {
    if (finishedId != null) {
      queryClient.invalidateQueries({ queryKey: ["submissions", assignmentId] });
    }
  }, [finishedId, assignmentId, queryClient]);

  if (assignmentQuery.isPending) return <LoadingState />;
  if (assignmentQuery.isError) {
    return <ErrorState error={assignmentQuery.error} onRetry={assignmentQuery.refetch} />;
  }

  const assignment = assignmentQuery.data;
  const left = assignment.submissions_left ?? 0;
  const closed = assignment.status === "closed";
  const inProgress = submission != null && !isFinal(submission.status);
  const canSubmit = !closed && left > 0 && !inProgress && !submit.isPending && code.trim() !== "";

  let footer = `This will be your ${ordinal(attempts.length + 1)} attempt`;
  if (closed) footer = "The deadline has passed. You can no longer submit.";
  else if (left <= 0) footer = "You have used all your attempts.";
  else if (inProgress) footer = "Your code is being tested…";

  return (
    <>
      <PageHeader
        breadcrumb={
          <>
            <Link to="/courses" className="hover:text-ink">
              {assignment.course_title}
            </Link>{" "}
            / Assignments
          </>
        }
        title={assignment.title}
        right={
          <div className="flex flex-wrap gap-2">
            {assignment.due_at && (
              <Chip tone={closed ? "neutral" : "warn"}>
                {closed ? "Closed" : "Due"} {formatDay(assignment.due_at)}
              </Chip>
            )}
            <Chip tone="neutral">Python 3.12</Chip>
            <Chip tone="neutral">
              {formatSeconds(assignment.time_limit_ms)} per test, {assignment.memory_limit_mb} MB
            </Chip>
            <Chip>
              {left} of {assignment.max_submissions} attempts left
            </Chip>
          </div>
        }
      />
      <div className="grid gap-9 lg:grid-cols-[360px_1fr]">
        <div className="space-y-9">
          <ProblemCard assignment={assignment} examples={testsQuery.data ?? []} />
          <AttemptsCard attempts={attempts} activeId={activeId} onSelect={setSelectedId} />
        </div>
        <div className="min-w-0 space-y-9">
          <Card className="overflow-hidden">
            <header className="flex items-center justify-between border-b border-line px-6 py-4">
              <span className="font-mono text-sm">solution.py</span>
              <span className="text-sm text-muted">draft kept in this browser</span>
            </header>
            <Suspense fallback={<LoadingState label="Loading the editor…" />}>
              <CodeEditor value={code} onChange={setCode} />
            </Suspense>
            <footer className="flex flex-wrap items-center justify-between gap-4 border-t border-line px-6 py-4">
              <span className="text-sm text-muted">{capitalize(footer)}</span>
              <Button size="lg" disabled={!canSubmit} onClick={() => submit.mutate()}>
                <Play className="h-4 w-4 fill-current" aria-hidden="true" />
                {submit.isPending ? "Submitting…" : "Submit"}
              </Button>
            </footer>
            {submit.isError && (
              <div className="px-6 pb-4">
                <FormError>{submit.error.message}</FormError>
              </div>
            )}
          </Card>
          {submission && <ResultCard submission={submission} />}
          {activeId != null && submissionQuery.isError && (
            <ErrorState error={submissionQuery.error} onRetry={submissionQuery.refetch} />
          )}
        </div>
      </div>
    </>
  );
}
