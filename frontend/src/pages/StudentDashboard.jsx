import { useQuery } from "@tanstack/react-query";
import { CalendarDays, Check, Code2, FlaskConical, List, Minus } from "lucide-react";
import { Link } from "react-router-dom";

import { getDashboard } from "../api/dashboard.js";
import { useAuth } from "../auth/AuthContext.jsx";
import { courseBarClass } from "../components/courseColors.js";
import { EmptyState, ErrorState, LoadingState } from "../components/states.jsx";
import { buttonClass, Card, CardHeader, Chip, IconBadge, PageHeader, Stat } from "../components/ui.jsx";
import VerdictSquares from "../components/VerdictSquares.jsx";
import { capitalize, dayDifference, formatDay, plural } from "../lib/format.js";

function passedOf(verdicts) {
  return verdicts.filter((verdict) => verdict === "passed").length;
}

/** The open, unsolved assignment with the closest deadline still ahead. */
export function nextDeadline(assignments, now = new Date()) {
  return (
    assignments
      .filter((a) => a.status === "open" && a.best_score !== 100 && a.due_at && new Date(a.due_at) > now)
      .sort((a, b) => new Date(a.due_at) - new Date(b.due_at))[0] ?? null
  );
}

function summaryLine(assignments, now = new Date()) {
  const pending = assignments.filter((a) => a.status === "open" && a.best_score !== 100 && a.due_at);
  const thisWeek = pending.filter((a) => {
    const days = dayDifference(new Date(a.due_at), now);
    return days >= 0 && days < 7;
  });
  if (thisWeek.length === 0) return "Nothing is due this week.";
  const closest = nextDeadline(assignments, now);
  const count = `${capitalize(plural(thisWeek.length, "assignment"))} ${thisWeek.length === 1 ? "is" : "are"} due this week.`;
  return closest ? `${count} The closest one is due ${formatDay(closest.due_at, now).split(",")[0]}.` : count;
}

function BestScore({ score }) {
  if (score == null) return <Chip tone="neutral">Not started</Chip>;
  if (score === 100) return <Chip tone="pass" icon={Check}>100%</Chip>;
  return <Chip tone={score === 0 ? "fail" : "warn"} icon={Minus}>{score}%</Chip>;
}

function NextDeadlineCard({ assignment }) {
  const hasAttempt = assignment.last_verdicts.length > 0;
  return (
    <Card className="flex flex-wrap items-center gap-6 bg-gradient-to-r from-[#1b1c3a] to-surface p-7">
      <IconBadge icon={CalendarDays} />
      <div className="min-w-0 flex-1">
        <p className="text-sm text-muted">Next deadline, {formatDay(assignment.due_at).replace(",", " at")}</p>
        <h2 className="mt-2 text-2xl font-semibold">{assignment.title}</h2>
        <p className="mt-3 flex flex-wrap items-center gap-3 text-sm text-muted">
          <VerdictSquares verdicts={assignment.last_verdicts} total={assignment.test_count} />
          {hasAttempt
            ? `${passedOf(assignment.last_verdicts)} of ${assignment.test_count} tests pass in your last attempt`
            : "You have not submitted anything yet"}
        </p>
      </div>
      <Link to={`/assignments/${assignment.id}`} className={buttonClass("primary", "lg")}>
        {hasAttempt ? "Continue" : "Start"}
      </Link>
    </Card>
  );
}

function AssignmentsTable({ assignments }) {
  return (
    <Card className="overflow-hidden">
      <CardHeader
        icon={Code2}
        title="Your assignments"
        right={<span className="text-sm text-muted">by deadline</span>}
      />
      {assignments.length === 0 ? (
        <EmptyState title="No assignments yet">
          Assignments appear here when your teachers publish them. Join a course from your profile.
        </EmptyState>
      ) : (
        <table className="w-full text-left">
          <thead className="bg-raised text-sm text-muted">
            <tr>
              <th className="px-7 py-3 font-semibold">Assignment</th>
              <th className="px-3 py-3 font-semibold">Due</th>
              <th className="px-3 py-3 font-semibold">Last attempt</th>
              <th className="px-7 py-3 text-right font-semibold">Best score</th>
            </tr>
          </thead>
          <tbody>
            {assignments.map((assignment) => {
              const urgent =
                assignment.status === "open" &&
                assignment.best_score !== 100 &&
                assignment.due_at &&
                dayDifference(new Date(assignment.due_at)) <= 1;
              let due = "No deadline";
              if (assignment.best_score === 100) due = "Submitted";
              else if (assignment.status === "closed") due = "Closed";
              else if (assignment.due_at) due = capitalize(formatDay(assignment.due_at));
              return (
                <tr key={assignment.id} className="border-t border-line hover:bg-raised/60">
                  <td className="px-7 py-4">
                    <Link to={`/assignments/${assignment.id}`} className="flex items-stretch gap-4">
                      <span
                        className={`w-1 shrink-0 rounded-full ${courseBarClass(assignment.course_color)}`}
                        aria-hidden="true"
                      />
                      <span>
                        <span className="block font-semibold">{assignment.title}</span>
                        <span className="block text-sm text-muted">{assignment.course_title}</span>
                      </span>
                    </Link>
                  </td>
                  <td className={`px-3 py-4 ${urgent ? "font-semibold text-fail" : "text-ink/90"}`}>{due}</td>
                  <td className="px-3 py-4">
                    <VerdictSquares verdicts={assignment.last_verdicts} total={assignment.test_count} />
                  </td>
                  <td className="px-7 py-4 text-right">
                    <BestScore score={assignment.best_score} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </Card>
  );
}

function ToReviewCard({ concepts }) {
  return (
    <Card>
      <CardHeader
        icon={FlaskConical}
        tone="fail"
        title="To review"
        border={false}
        right={
          <Link to="/report" className="text-sm font-semibold text-accent-soft hover:text-white">
            Report
          </Link>
        }
      />
      {concepts.length === 0 ? (
        <p className="px-7 pb-7 text-sm text-muted">Nothing to review right now.</p>
      ) : (
        <ul className="space-y-5 px-7 pb-7">
          {concepts.map((concept) => (
            <li key={concept.concept} className="flex items-center justify-between gap-4">
              <span>
                <span className="block font-semibold">{concept.concept}</span>
                <span className="block text-sm text-muted">
                  {concept.passed} of {plural(concept.total, "test")}
                </span>
              </span>
              <VerdictSquares verdicts={concept.verdicts} />
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

function RecentSubmissionsCard({ submissions }) {
  return (
    <Card className="overflow-hidden">
      <CardHeader icon={List} title="Recent submissions" />
      {submissions.length === 0 ? (
        <p className="px-7 py-6 text-sm text-muted">Your submissions will appear here.</p>
      ) : (
        <ul>
          {submissions.map((submission) => (
            <li key={submission.id} className="border-b border-line last:border-b-0">
              <Link
                to={`/assignments/${submission.assignment_id}`}
                className="flex items-center justify-between gap-4 px-7 py-4 hover:bg-raised/60"
              >
                <span>
                  <span className="block">{submission.assignment_title}</span>
                  <span className="block text-sm text-muted">{formatDay(submission.created_at)}</span>
                </span>
                <VerdictSquares verdicts={submission.verdicts} />
              </Link>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

export default function StudentDashboard() {
  const { user } = useAuth();
  const { data, isPending, isError, error, refetch } = useQuery({
    queryKey: ["dashboard"],
    queryFn: getDashboard,
  });

  if (isPending) return <LoadingState />;
  if (isError) return <ErrorState error={error} onRetry={refetch} />;

  const upcoming = nextDeadline(data.assignments);
  const { stats } = data;

  return (
    <>
      <PageHeader
        title={`Welcome back, ${user.full_name.split(" ")[0]}!`}
        subtitle={summaryLine(data.assignments)}
        right={
          <div className="flex gap-12">
            <Stat value={stats.to_submit} label="to submit" />
            <Stat
              value={stats.average_best_score != null ? `${stats.average_best_score}%` : "–"}
              label="average best score"
            />
            <Stat
              value={stats.concepts_to_review}
              label="concepts to review"
              tone={stats.concepts_to_review > 0 ? "fail" : undefined}
            />
          </div>
        }
      />
      <div className="grid gap-9 lg:grid-cols-[1fr_360px]">
        <div className="min-w-0 space-y-9">
          {upcoming && <NextDeadlineCard assignment={upcoming} />}
          <AssignmentsTable assignments={data.assignments} />
        </div>
        <div className="space-y-9">
          <ToReviewCard concepts={data.concepts_to_review} />
          <RecentSubmissionsCard submissions={data.recent_submissions} />
        </div>
      </div>
    </>
  );
}
