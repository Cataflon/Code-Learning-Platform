import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BookOpen, Eye, List, Play, Target } from "lucide-react";
import { lazy, Suspense, useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import { Link, useParams } from "react-router-dom";

import { getAssignment, listTestCases } from "../api/assignments.js";
import { createSubmission, listSubmissions } from "../api/submissions.js";
import Countdown from "../components/Countdown.jsx";
import { ErrorState, LoadingState } from "../components/states.jsx";
import { viewerLink } from "../api/materials.js";
import { FileBadge } from "../components/MaterialBits.jsx";
import RecommendationDialog, {
  alreadyShown,
  markShown,
} from "../components/RecommendationDialog.jsx";
import StatusBadge from "../components/StatusBadge.jsx";
import TestResultRow from "../components/TestResultRow.jsx";
import {
  Button,
  Card,
  CardHeader,
  Chip,
  FormError,
  IconBadge,
  PageHeader,
} from "../components/ui.jsx";
import VerdictSquares from "../components/VerdictSquares.jsx";
import { useAssignmentMaterials } from "../hooks/useMaterials.js";
import { useRecommendations } from "../hooks/useRecommendations.js";
import { isFinal, useSubmission } from "../hooks/useSubmission.js";
import {
  capitalize,
  formatDay,
  formatSeconds,
  ordinal,
  timeAgo,
} from "../lib/format.js";
import { describePages, unitOf } from "../lib/pages.js";

// Monaco is large: load it only when this page is opened.
const CodeEditor = lazy(() => import("../components/CodeEditor.jsx"));

const STARTER_CODE =
  "# Read the input with input() and print the answer with print()\n";

function draftKey(assignmentId) {
  return `autograder.draft.${assignmentId}`;
}

function scoreColor(score) {
  if (score === 100) return "text-ok";
  if (score === 0) return "text-bad";
  return "text-warn";
}

function TaskCard({ assignment, examples }) {
  return (
    <Card className="task">
      <div className="pad">
        <h2>Task</h2>
        {/* react-markdown never renders raw HTML, so a description cannot inject scripts. */}
        <div className="task-text">
          <ReactMarkdown>
            {assignment.description || "No description yet."}
          </ReactMarkdown>
        </div>
        {examples.slice(0, 2).map((example) => (
          <div key={example.id} className="io">
            <div>
              <span>Input</span>
              <pre>{example.input_data.trim() || "(empty)"}</pre>
            </div>
            <div>
              <span>Expected output</span>
              <pre>{example.expected_output.trim() || "(empty)"}</pre>
            </div>
          </div>
        ))}
        <p className="task-text text-ink-3">
          Limits: {formatSeconds(assignment.time_limit_ms)} and{" "}
          {assignment.memory_limit_mb} MB per test. Python 3.12 with the
          standard library only. You have {assignment.max_submissions} attempts;
          the best score counts.
        </p>
        {assignment.hidden_test_count > 0 && (
          <p className="flex gap-3 border border-accent/50 bg-accent/20 px-4 py-3 font-plain text-sm text-accent-strong">
            <Eye className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
            Some tests are hidden. You see whether they passed and which concept
            they check, not their data.
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
        <p className="px-7 py-6 text-sm text-ink-3">
          No attempts yet. Your results will appear here.
        </p>
      ) : (
        <ul>
          {attempts.map((attempt) => (
            <li
              key={attempt.id}
              className="border-b border-edge last:border-b-0"
            >
              <button
                type="button"
                onClick={() => onSelect(attempt.id)}
                aria-current={attempt.id === activeId ? "true" : undefined}
                className={`flex w-full items-center gap-4 px-7 py-4 text-left hover:bg-black/35 ${
                  attempt.id === activeId ? "bg-accent/15" : ""
                }`}
              >
                <span className="flex-1">
                  <span className="block font-semibold">
                    Attempt {attempt.attempt_number}
                  </span>
                  <span className="block text-sm text-ink-3">
                    {formatDay(attempt.created_at)}
                  </span>
                </span>
                <VerdictSquares
                  verdicts={attempt.verdicts}
                  total={attempt.total_count}
                />
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

/** "Study materials": where to learn for this assignment, with the pages indicated. */
function StudyMaterialsCard({ assignmentId, assignmentTitle }) {
  const { data } = useAssignmentMaterials(assignmentId);
  if (!data || data.length === 0) return null;
  return (
    <Card tint="warn">
      <CardHeader
        title="Study materials"
        right={<Link to="/learn">All materials</Link>}
      />
      {data.map((link) => (
        <Link
          key={link.material_id}
          to={viewerLink(link.material_id, {
            page: link.first_page,
            pages: link.pages,
            from: assignmentTitle,
          })}
          className="mat"
        >
          <FileBadge type={link.file_type} />
          <span className="min-w-0">
            <b>{link.title}</b>
            <small>
              {link.pages ? (
                <span className="pages">
                  {describePages(link.pages, unitOf(link))}
                </span>
              ) : (
                describePages("", unitOf(link))
              )}
            </small>
          </span>
          <span className="go">Open</span>
        </Link>
      ))}
    </Card>
  );
}

/** The page to read for each failed test, from the recommendations of the submission. */
function materialsByTest(recommendations) {
  const byTest = {};
  for (const material of recommendations?.materials ?? []) {
    const unit = unitOf(material);
    const label = `Read ${material.title}${material.pages ? `, ${describePages(material.pages, unit).toLowerCase()}` : ""}`;
    const to = viewerLink(material.material_id, {
      page: material.first_page,
      pages: material.pages,
    });
    for (const name of material.tests) byTest[name] ??= { to, label };
  }
  return byTest;
}

function ResultCard({ submission, recommendations, onShowMaterials }) {
  const running = !isFinal(submission.status);
  const firstPending = submission.results.findIndex(
    (result) => result.verdict == null,
  );
  const materials = materialsByTest(recommendations);

  return (
    <Card aria-live="polite">
      <header className="flex flex-wrap items-center gap-4 px-7 py-6">
        <IconBadge icon={Target} />
        <div className="flex-1">
          <h2 className="text-lg font-semibold">
            Result of attempt {submission.attempt_number}
          </h2>
          <p className="text-sm text-ink-3">{timeAgo(submission.created_at)}</p>
        </div>
        {running && <StatusBadge status={submission.status} />}
        <VerdictSquares
          verdicts={submission.verdicts}
          total={submission.total_count}
          large
        />
        <div className="w-28 text-right">
          <div
            className={`text-4xl font-bold ${submission.score != null ? scoreColor(submission.score) : "text-ink-3"}`}
          >
            {submission.score != null ? `${submission.score}%` : "–"}
          </div>
          <div className="text-sm text-ink-3">
            {submission.passed_count} of {submission.total_count} passed
          </div>
        </div>
      </header>
      {onShowMaterials && (
        <div className="px-7 pb-5">
          <Button variant="amber" size="sm" onClick={onShowMaterials}>
            <BookOpen className="h-4 w-4" aria-hidden="true" />
            Recommended pages
          </Button>
        </div>
      )}
      {submission.status === "error" && (
        <div className="px-7 pb-5">
          <FormError>
            {submission.error_message ??
              "This submission could not be evaluated."}
          </FormError>
        </div>
      )}
      <ul>
        {submission.results.map((result, index) => (
          <TestResultRow
            key={result.test_case_id}
            result={result}
            running={submission.status === "running" && index === firstPending}
            material={materials[result.name] ?? null}
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
    // A student has at most max_submissions attempts, so one page holds them all.
    queryFn: () => listSubmissions(assignmentId, { page_size: 100 }),
  });

  // The draft lives only in this browser (localStorage); the server never sees it.
  const [code, setCode] = useState(
    () => localStorage.getItem(draftKey(assignmentId)) ?? STARTER_CODE,
  );
  useEffect(() => {
    localStorage.setItem(draftKey(assignmentId), code);
  }, [assignmentId, code]);

  const attempts = attemptsQuery.data?.items ?? [];
  const [selectedId, setSelectedId] = useState(null);
  const activeId = selectedId ?? attempts[0]?.id ?? null;
  const submissionQuery = useSubmission(activeId);
  const submission = submissionQuery.data;

  // On a phone the page shows one section at a time (Task / Code / Tests), as in the prototype.
  const [pane, setPane] = useState("code");

  const submit = useMutation({
    mutationFn: () => createSubmission(assignmentId, code),
    onSuccess: (created) => {
      setPane("tests");
      queryClient.setQueryData(["submission", created.id], created);
      setSelectedId(created.id);
      queryClient.invalidateQueries({
        queryKey: ["submissions", assignmentId],
      });
      queryClient.invalidateQueries({ queryKey: ["assignment", assignmentId] });
    },
  });

  // After a finished submission with failed tests, the recommendations popup opens once.
  const recommendations = useRecommendations(submission);
  const hasRecommendations = (recommendations.data?.materials.length ?? 0) > 0;
  const [dialogFor, setDialogFor] = useState(null);
  useEffect(() => {
    if (hasRecommendations && submission && !alreadyShown(submission.id)) {
      markShown(submission.id);
      setDialogFor(submission.id);
    }
  }, [hasRecommendations, submission]);

  // When the watched submission finishes, refresh the attempts list (squares and score).
  const finishedId =
    submission && isFinal(submission.status) ? submission.id : null;
  useEffect(() => {
    if (finishedId != null) {
      queryClient.invalidateQueries({
        queryKey: ["submissions", assignmentId],
      });
    }
  }, [finishedId, assignmentId, queryClient]);

  if (assignmentQuery.isPending) return <LoadingState />;
  if (assignmentQuery.isError) {
    return (
      <ErrorState
        error={assignmentQuery.error}
        onRetry={assignmentQuery.refetch}
      />
    );
  }

  const assignment = assignmentQuery.data;
  const left = assignment.submissions_left ?? 0;
  const closed = assignment.status === "closed";
  const inProgress = submission != null && !isFinal(submission.status);
  const canSubmit =
    !closed &&
    left > 0 &&
    !inProgress &&
    !submit.isPending &&
    code.trim() !== "";
  const scores = attempts
    .map((attempt) => attempt.score)
    .filter((score) => score != null);
  const best = scores.length ? Math.max(...scores) : null;

  const last = attempts[0];
  let footer = `This will be your ${ordinal(attempts.length + 1)} attempt`;
  if (last && last.score != null) {
    footer = `Last run ${formatDay(last.created_at)}. ${last.passed_count} of ${last.total_count} tests pass. ${footer}.`;
  }
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
          <div className="meta-line">
            {assignment.due_at && (
              <Chip tone={closed ? "neutral" : "warn"}>
                {closed ? "closed" : "due"}{" "}
                {formatDay(assignment.due_at).replace(", ", " at ")}
              </Chip>
            )}
            {!closed && assignment.due_at && (
              <Countdown due={assignment.due_at} />
            )}
            {best != null && (
              <Chip tone={best === 100 ? "ok" : "warn"}>
                Best score {best}%
              </Chip>
            )}
            <Chip tone="neutral">
              {left} of {assignment.max_submissions} attempts left
            </Chip>
          </div>
        }
      />
      <div className="seg" role="tablist" aria-label="Assignment sections">
        {["task", "code", "tests"].map((name) => (
          <button
            key={name}
            type="button"
            role="tab"
            aria-selected={pane === name}
            onClick={() => setPane(name)}
          >
            {capitalize(name)}
          </button>
        ))}
      </div>
      <div className="work" data-pane={pane}>
        <div className="stack pane-task">
          <TaskCard assignment={assignment} examples={testsQuery.data ?? []} />
          <StudyMaterialsCard
            assignmentId={assignmentId}
            assignmentTitle={assignment.title}
          />
          <AttemptsCard
            attempts={attempts}
            activeId={activeId}
            onSelect={setSelectedId}
          />
        </div>
        <div className="stack">
          <Card className="pane-code overflow-hidden">
            <header className="ed-bar">
              <b>
                <i
                  className="dot"
                  style={{ background: "var(--ok)" }}
                  aria-hidden="true"
                />
                main.py
              </b>
              <span className="text-ink-3">
                Python 3.12 · draft kept in this browser
              </span>
            </header>
            <Suspense fallback={<LoadingState label="Loading the editor…" />}>
              <CodeEditor value={code} onChange={setCode} />
            </Suspense>
            <footer className="ed-foot">
              <p className="text-ink-2">{capitalize(footer)}</p>
              <Button
                size="lg"
                disabled={!canSubmit}
                onClick={() => submit.mutate()}
              >
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
          {!submission && (
            <p className="pane-tests show-sm card px-6 py-5 font-plain text-sm text-ink-3">
              No attempts yet. Submit your code to see how it does on every test.
            </p>
          )}
          {submission && (
            <div className="pane-tests">
              <ResultCard
                submission={submission}
                recommendations={recommendations.data}
                onShowMaterials={
                  hasRecommendations ? () => setDialogFor(submission.id) : null
                }
              />
            </div>
          )}
          {activeId != null && submissionQuery.isError && (
            <ErrorState
              error={submissionQuery.error}
              onRetry={submissionQuery.refetch}
            />
          )}
        </div>
      </div>
      {dialogFor != null &&
        dialogFor === submission?.id &&
        hasRecommendations && (
          <RecommendationDialog
            recommendations={recommendations.data}
            attemptNumber={submission.attempt_number}
            assignmentTitle={assignment.title}
            onClose={() => setDialogFor(null)}
          />
        )}
    </>
  );
}
