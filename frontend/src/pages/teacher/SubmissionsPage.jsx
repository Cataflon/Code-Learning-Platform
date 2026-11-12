import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { BarChart3, FlaskConical, List, Search } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Bar, BarChart, Cell, LabelList, ResponsiveContainer, XAxis } from "recharts";

import { getAssignment } from "../../api/assignments.js";
import { getAssignmentStats } from "../../api/dashboard.js";
import { getSubmission, listSubmissions } from "../../api/submissions.js";
import Modal from "../../components/Modal.jsx";
import Pagination from "../../components/Pagination.jsx";
import { ErrorState, LoadingState } from "../../components/states.jsx";
import SubmissionsTable from "../../components/SubmissionsTable.jsx";
import TestResultRow from "../../components/TestResultRow.jsx";
import { Button, Card, CardHeader, Chip, inputClass, PageHeader, Stat } from "../../components/ui.jsx";

const PAGE_SIZE = 6;
const FILTERS = [
  { key: "all", label: "All" },
  { key: "correct", label: "Correct" },
  { key: "partial", label: "Partial" },
  { key: "wrong", label: "Wrong" },
  { key: "running", label: "Running" },
];
// One color per score band, from worst to best, as in the mockup.
const BAND_COLORS = ["#f87171", "#fb923c", "#fbbf24", "#a3e635", "#4ade80"];

function rateColor(rate) {
  if (rate == null) return { text: "text-muted", bar: "bg-idle" };
  if (rate < 0.5) return { text: "text-fail", bar: "bg-fail" };
  if (rate < 0.8) return { text: "text-warn", bar: "bg-warn" };
  return { text: "text-pass", bar: "bg-pass" };
}

function PassRateCard({ tests }) {
  const ran = tests.filter((test) => test.pass_rate != null);
  const weakest = ran.length ? ran.reduce((low, test) => (test.pass_rate < low.pass_rate ? test : low)) : null;

  return (
    <Card>
      <CardHeader icon={FlaskConical} title="Pass rate per test" border={false} />
      <div className="space-y-5 px-7 pb-7">
        {tests.length === 0 && <p className="text-sm text-muted">This assignment has no tests.</p>}
        {tests.map((test) => {
          const color = rateColor(test.pass_rate);
          const percent = test.pass_rate == null ? null : Math.round(test.pass_rate * 100);
          return (
            <div key={test.test_case_id}>
              <div className="flex items-center gap-3">
                <span className="min-w-0 truncate">{test.name}</span>
                {test.is_hidden && <Chip tone="neutral">hidden</Chip>}
                <span className={`ml-auto font-semibold ${color.text}`}>{percent == null ? "–" : `${percent}%`}</span>
              </div>
              <div className="mt-2 h-2 overflow-hidden rounded-full bg-idle">
                <div className={`h-full ${color.bar}`} style={{ width: `${percent ?? 0}%` }} />
              </div>
            </div>
          );
        })}
        {weakest && weakest.pass_rate < 0.5 && (
          <p className="rounded-lg border border-fail-line bg-fail-tint px-4 py-3 text-sm text-fail">
            Only {Math.round(weakest.pass_rate * 100)}% pass “{weakest.name}”
            {weakest.concepts.length > 0 && <>, which checks the concept “{weakest.concepts.join(", ")}”</>}.
          </p>
        )}
      </div>
    </Card>
  );
}

function ScoreDistributionCard({ distribution }) {
  const total = distribution.reduce((sum, bucket) => sum + bucket.count, 0);
  return (
    <Card>
      <CardHeader icon={BarChart3} title="Score distribution" border={false} />
      <div className="px-5 pb-6">
        {total === 0 ? (
          <p className="px-2 text-sm text-muted">No finished submissions yet.</p>
        ) : (
          <>
            <div className="h-56" aria-hidden="true">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={distribution} margin={{ top: 24, right: 4, left: 4, bottom: 0 }}>
                  <XAxis dataKey="label" tickLine={false} axisLine={false} tick={{ fill: "#9a9cb5", fontSize: 12 }} />
                  <Bar dataKey="count" radius={[6, 6, 0, 0]} isAnimationActive={false}>
                    <LabelList dataKey="count" position="top" fill="#ffffff" fontSize={13} fontWeight={600} />
                    {distribution.map((bucket, index) => (
                      <Cell key={bucket.label} fill={BAND_COLORS[index]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            {/* The same numbers as text, for screen readers and for tests. */}
            <ul className="sr-only">
              {distribution.map((bucket) => (
                <li key={bucket.label}>
                  {bucket.label}: {bucket.count} students
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    </Card>
  );
}

function CodeDialog({ submissionId, onClose }) {
  const { data, isPending, isError, error } = useQuery({
    queryKey: ["submission", submissionId],
    queryFn: () => getSubmission(submissionId),
  });

  return (
    <Modal
      wide
      title={data ? `${data.student_name}, attempt ${data.attempt_number}` : "Submission"}
      subtitle={data ? `${data.passed_count} of ${data.total_count} tests passed` : undefined}
      onClose={onClose}
      footer={
        <Button variant="neutral" onClick={onClose}>
          Close
        </Button>
      }
    >
      {isPending && <LoadingState />}
      {isError && <p className="px-7 pb-6 text-fail">{error.message}</p>}
      {data && (
        <>
          <pre className="mx-7 mb-6 max-h-80 overflow-auto rounded-lg border border-line bg-raised p-4 font-mono text-sm">
            {data.code}
          </pre>
          {data.error_message && <p className="px-7 pb-4 text-sm text-fail">{data.error_message}</p>}
          <ul>
            {data.results.map((result) => (
              <TestResultRow key={result.test_case_id} result={result} />
            ))}
          </ul>
        </>
      )}
    </Modal>
  );
}

/** Teacher view of one assignment: statistics and every submission (mockup 14). */
export default function SubmissionsPage() {
  const assignmentId = Number(useParams().assignmentId);
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [codeId, setCodeId] = useState(null);

  // Wait for a pause in typing before asking the server.
  useEffect(() => {
    const timer = setTimeout(() => {
      setQuery(search.trim());
      setPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [search]);

  const assignment = useQuery({
    queryKey: ["assignment", assignmentId],
    queryFn: () => getAssignment(assignmentId),
  });
  const stats = useQuery({
    queryKey: ["assignment-stats", assignmentId],
    queryFn: () => getAssignmentStats(assignmentId),
    // While something is running, keep the numbers fresh.
    refetchInterval: (q) => (q.state.data?.running_count > 0 ? 3000 : false),
  });
  const list = useQuery({
    queryKey: ["submissions", assignmentId, { filter, query, page }],
    queryFn: () => listSubmissions(assignmentId, { verdict: filter, q: query, page, page_size: PAGE_SIZE }),
    placeholderData: keepPreviousData,
    refetchInterval: (q) => (q.state.data?.counts.running > 0 ? 3000 : false),
  });

  if (assignment.isPending || stats.isPending) return <LoadingState />;
  if (assignment.isError) return <ErrorState error={assignment.error} onRetry={assignment.refetch} />;
  if (stats.isError) return <ErrorState error={stats.error} onRetry={stats.refetch} />;

  const counts = list.data?.counts;

  return (
    <>
      <PageHeader
        breadcrumb={
          <>
            <Link to={`/courses/${assignment.data.course_id}`} className="hover:text-ink">
              {assignment.data.course_title}
            </Link>{" "}
            / {assignment.data.title}
          </>
        }
        title="Submissions and statistics"
        right={
          <div className="flex gap-12">
            <Stat value={stats.data.submission_count} label="submissions" />
            <Stat value={`${stats.data.submitted_count} of ${stats.data.enrolled_count}`} label="students submitted" />
            <Stat
              value={stats.data.average_score != null ? `${stats.data.average_score}%` : "–"}
              label="average score"
            />
            <Stat value={stats.data.running_count} label="running now" />
          </div>
        }
      />
      <div className="grid gap-9 lg:grid-cols-[360px_1fr]">
        <div className="space-y-9">
          <PassRateCard tests={stats.data.tests} />
          <ScoreDistributionCard distribution={stats.data.score_distribution} />
        </div>
        <Card className="min-w-0 self-start overflow-hidden">
          <CardHeader
            icon={List}
            title="All submissions"
            border={false}
            right={
              <label className="relative block w-64">
                <Search className="absolute left-4 top-3.5 h-4 w-4 text-muted" aria-hidden="true" />
                <input
                  className={`${inputClass} pl-11`}
                  placeholder="Search for a student"
                  aria-label="Search for a student"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                />
              </label>
            }
          />
          <div className="flex flex-wrap gap-3 px-7 pb-6" role="tablist" aria-label="Filter submissions">
            {FILTERS.map(({ key, label }) => (
              <button
                key={key}
                type="button"
                role="tab"
                aria-selected={filter === key}
                onClick={() => {
                  setFilter(key);
                  setPage(1);
                }}
                className={`rounded-lg border px-4 py-2 text-sm font-semibold ${
                  filter === key ? "border-accent bg-accent text-white" : "border-line text-ink hover:bg-raised"
                }`}
              >
                {label} {counts ? counts[key] : ""}
              </button>
            ))}
          </div>
          {list.isPending && <LoadingState />}
          {list.isError && <p className="px-7 pb-6 text-fail">{list.error.message}</p>}
          {list.data && (
            <>
              <SubmissionsTable submissions={list.data.items} onShowCode={setCodeId} />
              <div className="border-t border-line">
                <Pagination page={page} pageSize={PAGE_SIZE} total={list.data.total} onPageChange={setPage} />
              </div>
            </>
          )}
        </Card>
      </div>
      {codeId != null && <CodeDialog submissionId={codeId} onClose={() => setCodeId(null)} />}
    </>
  );
}
