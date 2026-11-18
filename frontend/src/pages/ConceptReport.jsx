import { useQuery } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";

import { getMyConceptReport } from "../api/reports.js";
import { ConceptBars, LevelChip, percent } from "../components/ConceptLevel.jsx";
import { EmptyState, ErrorState, LoadingState } from "../components/states.jsx";
import { buttonClass, Card, CardHeader, PageHeader, ProgressBar } from "../components/ui.jsx";
import VerdictSquares from "../components/VerdictSquares.jsx";
import { useCourses } from "../hooks/useCourses.js";
import { plural } from "../lib/format.js";

const LEVEL_COLORS = { review: "var(--bad)", progress: "var(--warn)", mastered: "var(--ok)" };

/** "You failed the hidden test in Digit sum and one test in Input and output." */
export function describeFailures(concept) {
  const failed = concept.tests.filter((test) => test.verdict !== "passed");
  const byAssignment = new Map();
  for (const test of failed) {
    const list = byAssignment.get(test.assignment_title) ?? [];
    list.push(test);
    byAssignment.set(test.assignment_title, list);
  }
  const parts = [...byAssignment].map(([title, tests]) => {
    if (tests.length === 1) {
      const what = tests[0].is_hidden ? "the hidden test" : `“${tests[0].test_name}”`;
      return `${what} in ${title}`;
    }
    return `${plural(tests.length, "test")} in ${title}`;
  });
  if (parts.length === 0) return "No failed tests.";
  const last = parts.pop();
  return `You failed ${parts.length ? `${parts.join(", ")} and ${last}` : last}.`;
}

/** Assignments with failed tests for this concept, in order, without duplicates. */
function failedAssignments(concept) {
  const seen = new Map();
  for (const test of concept.tests) {
    if (test.verdict !== "passed" && !seen.has(test.assignment_id)) {
      seen.set(test.assignment_id, test.assignment_title);
    }
  }
  return [...seen].map(([id, title]) => ({ id, title }));
}

function ConceptTable({ report }) {
  const { review_below: low, mastered_from: high } = report.thresholds;
  return (
    <Card>
      <CardHeader
        title="Concepts"
        subtitle={`${report.tests_passed} of ${plural(report.tests_total, "test")} passed across ${plural(report.assignment_count, "assignment")}`}
        right={<VerdictSquares verdicts={report.verdicts} />}
      />
      <div className="overflow-x-auto">
      <table className="tbl">
        <thead>
          <tr>
            <th>Concept</th>
            <th className="hide-sm">Tests</th>
            <th>Pass rate</th>
            <th className="hide-sm text-right">Level</th>
          </tr>
        </thead>
        <tbody>
          {report.concepts.map((concept) => (
            <tr key={concept.concept_id}>
              <td>
                <b className="flex flex-wrap items-center gap-2">
                  {concept.concept}
                  <span className="show-sm">
                    <LevelChip level={concept.level} />
                  </span>
                </b>
                <span className="block text-sm text-ink-3">
                  {concept.passed} of {plural(concept.total, "test")},{" "}
                  {plural(concept.assignment_count, "assignment")}
                </span>
              </td>
              <td className="hide-sm">
                <VerdictSquares verdicts={concept.tests.map((test) => test.verdict)} />
              </td>
              <td className="min-w-32">
                <span className="flex items-center gap-3">
                  <ProgressBar
                    value={concept.pass_rate * 100}
                    color={LEVEL_COLORS[concept.level]}
                    label={`${concept.concept} pass rate`}
                    className="flex-1"
                  />
                  <span className="num term w-12 text-right text-xl text-ink">
                    {percent(concept.pass_rate)}
                  </span>
                </span>
              </td>
              <td className="hide-sm text-right">
                <LevelChip level={concept.level} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      </div>
      <p className="dash-top px-6 py-4 text-sm text-ink-3">
        Below {percent(low)} you should review, {percent(low)}–{percent(high)} is in progress,{" "}
        {percent(high)} and above is mastered.
      </p>
    </Card>
  );
}

function ReviewFirst({ concepts }) {
  const toReview = concepts.filter((concept) => concept.level === "review");
  return (
    <Card tint="bad">
      <CardHeader title="Review first" />
      {toReview.length === 0 ? (
        <p className="pad plain text-ink-2">Nothing below the review line. Keep going.</p>
      ) : (
        <ul className="sep">
          {toReview.map((concept) => {
            const assignments = failedAssignments(concept);
            return (
              <li key={concept.concept_id} className="pad grid gap-3">
                <b className="text-ink">{concept.concept}</b>
                <p className="plain text-ink-2">{describeFailures(concept)}</p>
                <div className="flex flex-wrap gap-2">
                  {assignments.map((assignment) => (
                    <Link
                      key={assignment.id}
                      to={`/assignments/${assignment.id}`}
                      className={buttonClass("neutral", "sm")}
                    >
                      Reopen {assignment.title}
                    </Link>
                  ))}
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </Card>
  );
}

function CoursePicker({ courses, value, onChange }) {
  return (
    <label className="block min-w-64">
      <span className="label">Course</span>
      <select className="field" value={value} onChange={(event) => onChange(event.target.value)}>
        {courses.map((course) => (
          <option key={course.id} value={course.id}>
            {course.title}
          </option>
        ))}
      </select>
    </label>
  );
}

/** The student's "where you go wrong" report (mockup 05, in the 8-bit style). */
export default function ConceptReport() {
  const [params, setParams] = useSearchParams();
  const courses = useCourses();
  const list = courses.data ?? [];
  const requested = Number(params.get("course"));
  const courseId = list.some((course) => course.id === requested) ? requested : list[0]?.id;

  const report = useQuery({
    queryKey: ["concept-report", courseId],
    queryFn: () => getMyConceptReport(courseId),
    enabled: courseId != null,
  });

  if (courses.isPending) return <LoadingState />;
  if (courses.isError) return <ErrorState error={courses.error} onRetry={courses.refetch} />;

  const header = (
    <PageHeader
      title="Where you go wrong"
      subtitle="Based on your latest submission for each assignment. Every test is linked to the concepts it checks."
      right={
        list.length > 0 && (
          <CoursePicker
            courses={list}
            value={courseId}
            onChange={(id) => setParams({ course: id }, { replace: true })}
          />
        )
      }
    />
  );

  if (list.length === 0) {
    return (
      <>
        {header}
        <Card>
          <EmptyState title="No courses yet">Join a course from your profile to see a report.</EmptyState>
        </Card>
      </>
    );
  }

  return (
    <>
      {header}
      {report.isPending && <LoadingState />}
      {report.isError && <ErrorState error={report.error} onRetry={report.refetch} />}
      {report.data && report.data.concepts.length === 0 && (
        <Card>
          <EmptyState title="Nothing to report yet">
            Submit an assignment in {report.data.course_title} and your concepts will appear here.
          </EmptyState>
        </Card>
      )}
      {report.data && report.data.concepts.length > 0 && (
        <div className="cols">
          <div className="stack">
            <ConceptTable report={report.data} />
            <Card>
              <CardHeader title="Pass rate by concept" />
              <div className="pad">
                <ConceptBars
                  items={report.data.concepts.map((c) => ({
                    name: c.concept,
                    rate: c.pass_rate,
                    level: c.level,
                  }))}
                />
              </div>
            </Card>
          </div>
          <ReviewFirst concepts={report.data.concepts} />
        </div>
      )}
    </>
  );
}
