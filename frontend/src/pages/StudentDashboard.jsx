// Student dashboard, as in the 8-bit prototype (docs/design-8bit/screenshots/dashboard-*.png):
// the next deadline in a big card with stars, three statistic cards beside it, then the
// assignments, the concepts to review and the recent submissions.

import { useQuery } from "@tanstack/react-query";
import { ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";

import { getDashboard } from "../api/dashboard.js";
import { viewerLink } from "../api/materials.js";
import { useAuth } from "../auth/AuthContext.jsx";
import Countdown from "../components/Countdown.jsx";
import { courseColorVar } from "../components/courseColors.js";
import { EmptyState, ErrorState, LoadingState } from "../components/states.jsx";
import { buttonClass, Card, Chip, StatCard } from "../components/ui.jsx";
import VerdictSquares from "../components/VerdictSquares.jsx";
import { useRecommendations } from "../hooks/useRecommendations.js";
import { capitalize, dayDifference, formatDay, plural } from "../lib/format.js";
import { describePages, unitOf } from "../lib/pages.js";

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

/** Without a deadline ahead, the first open assignment that is not solved yet. */
function nextToSolve(assignments) {
  return assignments.find((a) => a.status === "open" && a.best_score !== 100) ?? null;
}

function greeting(now = new Date()) {
  const hour = now.getHours();
  if (hour < 5 || hour >= 18) return "Good evening";
  if (hour < 12) return "Good morning";
  return "Good afternoon";
}

function dueText(due) {
  const [day, time] = formatDay(due).split(", ");
  return `due ${day} at ${time}`;
}

/** What the recommendations of the last attempt say: the failed tests and the materials. */
function useLastAttemptHelp(assignment) {
  const submission =
    assignment?.last_submission_id != null
      ? {
          id: assignment.last_submission_id,
          status: assignment.last_submission_status,
          passed_count: passedOf(assignment.last_verdicts),
          total_count: assignment.test_count,
        }
      : null;
  return useRecommendations(submission).data;
}

/** "Hidden test #1 fails on negative numbers." */
function failureLine(help) {
  const failed = help?.failed_tests[0];
  if (!failed) return "Keep going: every attempt shows what to fix.";
  const concept = failed.concepts[0];
  const more = help.failed_tests.length > 1 ? ` (and ${plural(help.failed_tests.length - 1, "more test")})` : "";
  return `“${failed.name}” fails${concept ? ` on ${concept.toLowerCase()}` : ""}${more}.`;
}

/** "Read Lecture 4, pages 12-15": the first material recommended after the last attempt. */
function RecommendedButton({ help }) {
  const first = help?.materials[0];
  if (!first) return null;
  const pages = first.pages ? `, ${describePages(first.pages, unitOf(first)).toLowerCase()}` : "";
  return (
    <Link to={viewerLink(first.material_id, { page: first.first_page, pages: first.pages })} className={buttonClass("amber")}>
      Read {first.title}
      {pages}
    </Link>
  );
}

function HeroCard({ name, assignment }) {
  const help = useLastAttemptHelp(assignment);
  const sparks = (
    <>
      <i className="spark" style={{ right: "9%", top: "22%", "--c": "#ffbe4f" }} aria-hidden="true" />
      <i className="spark s" style={{ right: "20%", top: "12%", animationDelay: "-.8s" }} aria-hidden="true" />
      <i className="spark s" style={{ right: "5%", top: "52%", "--c": "#ff92d4", animationDelay: "-1.6s" }} aria-hidden="true" />
      <i className="spark" style={{ right: "16%", top: "66%", "--c": "#5cc6ff", animationDelay: "-1.1s" }} aria-hidden="true" />
    </>
  );

  if (!assignment) {
    return (
      <Card className="hero">
        <div className="pad">
          {sparks}
          <p className="muted">{greeting()}, {name}.</p>
          <h1>All caught up</h1>
          <p className="plain text-ink-2">Nothing is waiting for you right now. Read ahead in Learn or check where you go wrong.</p>
          <div className="actions">
            <Link to="/learn" className={buttonClass("primary")}>
              Open Learn
            </Link>
            <Link to="/report" className={buttonClass("outline")}>
              Concept report
            </Link>
          </div>
        </div>
      </Card>
    );
  }

  const tried = assignment.last_verdicts.length > 0;
  const passed = passedOf(assignment.last_verdicts);
  const solved = tried && passed === assignment.test_count;
  return (
    <Card className="hero">
      <div className="pad">
        {sparks}
        <p className="muted">
          {greeting()}, {name}. {assignment.due_at ? "Your next deadline:" : "Up next:"}
        </p>
        <h1>
          <Link to={`/assignments/${assignment.id}`}>{assignment.title}</Link>
        </h1>
        <div className="meta-line">
          <Chip>
            <i className="dot" style={{ background: courseColorVar(assignment.course_color) }} />
            {assignment.course_title}
          </Chip>
          {assignment.due_at && <Chip tone="warn">{dueText(assignment.due_at)}</Chip>}
          {assignment.due_at && <Countdown due={assignment.due_at} />}
        </div>
        <div className="hero-status">
          <VerdictSquares verdicts={assignment.last_verdicts} total={assignment.test_count} large />
          <p className="plain">
            {tried ? (
              <>
                <b>
                  {passed} of {assignment.test_count} tests pass.
                </b>{" "}
                {solved ? "Well done." : failureLine(help)}
              </>
            ) : (
              <>
                <b>Not started yet.</b> {plural(assignment.test_count, "test")} and{" "}
                {plural(assignment.max_submissions, "attempt")}.
              </>
            )}
          </p>
        </div>
        <div className="actions">
          <Link to={`/assignments/${assignment.id}`} className={buttonClass("primary")}>
            {tried ? "Continue solving" : "Start solving"}
            <ArrowRight className="go" aria-hidden="true" />
          </Link>
          {tried && !solved && <RecommendedButton help={help} />}
        </div>
      </div>
    </Card>
  );
}

function scoreChip(assignment) {
  const score = assignment.best_score;
  if (score == null) return { tone: "idle", text: "New" };
  if (score === 100) return { tone: "ok", text: "100%" };
  return { tone: score === 0 ? "bad" : "warn", text: `${score}%` };
}

function AssignmentsCard({ assignments }) {
  return (
    <Card>
      <header className="card-head">
        <h2>Assignments</h2>
        <span>sorted by deadline</span>
      </header>
      {assignments.length === 0 ? (
        <EmptyState title="No assignments yet">
          Assignments appear here when your teachers publish them. Join a course from Courses.
        </EmptyState>
      ) : (
        <div role="table" aria-label="Your assignments">
          <div className="row head" role="row">
            <span role="columnheader">Assignment</span>
            <span role="columnheader">Due</span>
            <span role="columnheader">Last attempt</span>
            <span role="columnheader" style={{ justifySelf: "end" }}>
              Best
            </span>
          </div>
          {assignments.map((assignment) => {
            const color = courseColorVar(assignment.course_color);
            const open = assignment.status === "open" && assignment.best_score !== 100;
            const soon = open && assignment.due_at && dayDifference(new Date(assignment.due_at)) <= 1;
            let due = "No deadline";
            if (assignment.best_score === 100) due = "Submitted";
            else if (assignment.status === "closed") due = "Closed";
            else if (assignment.due_at) due = capitalize(formatDay(assignment.due_at));
            const chip = scoreChip(assignment);
            return (
              <Link key={assignment.id} to={`/assignments/${assignment.id}`} className="row" role="row" style={{ "--c": color }}>
                <span className="name" role="cell">
                  <b>{assignment.title}</b>
                  <span>
                    <i className="dot" style={{ background: color }} />
                    {assignment.course_title}
                  </span>
                </span>
                <span className={`due ${soon ? "soon" : ""}`} role="cell">
                  {due}
                </span>
                <span role="cell">
                  <VerdictSquares verdicts={assignment.last_verdicts} total={assignment.test_count} />
                </span>
                <span className={`score chip num ${chip.tone}`} role="cell">
                  {chip.text}
                </span>
              </Link>
            );
          })}
        </div>
      )}
    </Card>
  );
}

function ToReviewCard({ concepts }) {
  return (
    <Card tint="bad">
      <header className="card-head">
        <h2>To review</h2>
        <Link to="/report">Open report</Link>
      </header>
      {concepts.length === 0 ? (
        <p className="plain px-6 py-5 text-sm text-ink-3">Nothing to review right now.</p>
      ) : (
        <ul className="mini">
          {concepts.map((concept) => (
            <li key={concept.concept}>
              <Link to="/report">
                <span>
                  <b>{concept.concept}</b>
                  <small>
                    {concept.passed} of {plural(concept.total, "test")} pass
                  </small>
                </span>
                <VerdictSquares verdicts={concept.verdicts} />
              </Link>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

function RecentSubmissionsCard({ submissions }) {
  return (
    <Card tint="blue">
      <header className="card-head">
        <h2>Recent submissions</h2>
      </header>
      {submissions.length === 0 ? (
        <p className="plain px-6 py-5 text-sm text-ink-3">Your submissions will appear here.</p>
      ) : (
        <ul className="mini">
          {submissions.map((submission) => (
            <li key={submission.id}>
              <Link to={`/assignments/${submission.assignment_id}`}>
                <span>
                  <b>{submission.assignment_title}</b>
                  <small>{formatDay(submission.created_at)}</small>
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

  const upcoming = nextDeadline(data.assignments) ?? nextToSolve(data.assignments);
  const { stats } = data;
  const name = user.full_name.split(" ")[0];

  return (
    <div className="view">
      <h1 className="sr-only">Dashboard</h1>
      <div className="grid-hero">
        <HeroCard name={name} assignment={upcoming} />
        <div className="stats">
          <StatCard label="Assignments to submit" value={stats.to_submit} />
          <StatCard
            label="Average best score"
            tint="ok"
            value={stats.average_best_score != null ? `${stats.average_best_score}%` : "–"}
          />
          <StatCard as={Link} to="/report" label="Concepts to review" tint="bad" value={stats.concepts_to_review} />
        </div>
      </div>
      <div className="cols">
        <AssignmentsCard assignments={data.assignments} />
        <div className="stack">
          <ToReviewCard concepts={data.concepts_to_review} />
          <RecentSubmissionsCard submissions={data.recent_submissions} />
        </div>
      </div>
    </div>
  );
}
