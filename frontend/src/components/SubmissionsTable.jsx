import { EmptyState } from "./states.jsx";
import { Avatar } from "./ui.jsx";
import VerdictSquares from "./VerdictSquares.jsx";
import { formatTime, timeAgo } from "../lib/format.js";

function isToday(value) {
  return new Date(value).toDateString() === new Date().toDateString();
}

/** The line under the student's name: what is happening or what went wrong. */
export function describeSubmission(submission) {
  if (submission.status === "queued") return { text: "waiting in the queue", tone: "text-info" };
  if (submission.status === "running") {
    const done = submission.verdicts.filter((verdict) => verdict != null).length;
    const current = Math.min(done + 1, submission.total_count);
    return { text: `running test ${current} of ${submission.total_count}`, tone: "text-info" };
  }
  if (submission.status === "error") return { text: "could not be evaluated", tone: "text-fail" };
  if (submission.error_excerpt) return { text: `runtime error: ${submission.error_excerpt}`, tone: "text-fail" };
  return { text: `attempt ${submission.attempt_number}`, tone: "text-muted" };
}

/** Squares for a row: tests still to run are shown in the "running" color. */
function rowVerdicts(submission) {
  if (submission.status !== "running" && submission.status !== "queued") return submission.verdicts;
  return submission.verdicts.map((verdict) => verdict ?? "running");
}

export default function SubmissionsTable({ submissions, onShowCode }) {
  if (submissions.length === 0) {
    return <EmptyState title="No submissions here">Nothing matches this filter yet.</EmptyState>;
  }
  return (
    <table className="w-full text-left">
      <thead className="bg-raised text-sm text-muted">
        <tr>
          <th className="px-7 py-3 font-semibold">Student</th>
          <th className="px-3 py-3 font-semibold">Submitted</th>
          <th className="px-3 py-3 font-semibold">Tests</th>
          <th className="px-3 py-3 text-right font-semibold">Score</th>
          <th className="px-7 py-3" />
        </tr>
      </thead>
      <tbody>
        {submissions.map((submission) => {
          const inProgress = submission.status === "queued" || submission.status === "running";
          const detail = describeSubmission(submission);
          return (
            <tr key={submission.id} className={`border-t border-line ${inProgress ? "bg-info-tint/60" : ""}`}>
              <td className="px-7 py-4">
                <span className="flex items-center gap-4">
                  <Avatar name={submission.student_name} size="sm" />
                  <span>
                    <span className="block">{submission.student_name}</span>
                    <span className={`block text-sm ${detail.tone}`}>{detail.text}</span>
                  </span>
                </span>
              </td>
              <td className="px-3 py-4 text-muted">
                {isToday(submission.created_at) && !inProgress
                  ? formatTime(new Date(submission.created_at))
                  : timeAgo(submission.created_at)}
              </td>
              <td className="px-3 py-4">
                <VerdictSquares verdicts={rowVerdicts(submission)} total={submission.total_count} />
              </td>
              <td className="px-3 py-4 text-right font-semibold">
                {submission.score != null ? `${submission.score}%` : "–"}
              </td>
              <td className="px-7 py-4 text-right">
                <button
                  type="button"
                  className="font-semibold text-accent-soft hover:text-white"
                  onClick={() => onShowCode(submission.id)}
                  aria-label={`Show the code of ${submission.student_name}, attempt ${submission.attempt_number}`}
                >
                  Code
                </button>
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
