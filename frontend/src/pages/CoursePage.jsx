import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Clock, Copy, FlaskConical, List, Plus, Ticket } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { createAssignment, updateAssignment } from "../api/assignments.js";
import { createConcept, listConcepts, newJoinCode } from "../api/courses.js";
import { getCourseStats } from "../api/dashboard.js";
import { EmptyState, ErrorState, LoadingState } from "../components/states.jsx";
import {
  Button,
  buttonClass,
  Card,
  CardHeader,
  Chip,
  FormError,
  inputClass,
  PageHeader,
  Stat,
} from "../components/ui.jsx";
import { useAssignments, useCourse } from "../hooks/useCourses.js";
import { formatDay, plural } from "../lib/format.js";

const STATUS_CHIP = {
  open: { tone: "info", icon: Clock, label: "Open" },
  draft: { tone: "neutral", icon: undefined, label: "Draft" },
  closed: { tone: "pass", icon: Check, label: "Closed" },
};

function describe(assignment) {
  const parts = [];
  if (assignment.due_at) {
    const when = formatDay(assignment.due_at).split(",")[0];
    parts.push(assignment.status === "closed" ? `closed ${when}` : `due ${when}`);
  } else {
    parts.push("no deadline");
  }
  parts.push(plural(assignment.test_count, "test"));
  if (assignment.hidden_test_count > 0) parts.push(`${assignment.hidden_test_count} hidden`);
  return parts.join(", ");
}

/** Stacked bar: students who passed all tests, some tests, no test. */
export function ResultBar({ buckets, submitted, enrolled }) {
  const total = Math.max(1, submitted);
  const width = (count) => `${(count / total) * 100}%`;
  return (
    <div>
      <div
        className="flex h-2.5 w-full overflow-hidden rounded-full bg-idle"
        role="img"
        aria-label={`${buckets.full} passed all tests, ${buckets.partial} passed some, ${buckets.none} passed none`}
      >
        <span className="bg-pass" style={{ width: width(buckets.full) }} />
        <span className="bg-warn" style={{ width: width(buckets.partial) }} />
        <span className="bg-fail" style={{ width: width(buckets.none) }} />
      </div>
      <p className="mt-2 text-sm text-muted">
        {submitted} of {enrolled} submitted
      </p>
    </div>
  );
}

function AssignmentsCard({ courseId }) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: assignments, isPending, isError, error } = useAssignments(courseId);
  const refresh = () => queryClient.invalidateQueries({ queryKey: ["assignments", courseId] });

  const create = useMutation({
    mutationFn: () => createAssignment(courseId, { title: "Untitled assignment" }),
    onSuccess: (assignment) => {
      refresh();
      navigate(`/teacher/assignments/${assignment.id}/edit`);
    },
  });
  const publish = useMutation({
    mutationFn: (assignmentId) => updateAssignment(assignmentId, { is_published: true }),
    onSuccess: refresh,
  });

  return (
    <Card className="overflow-hidden">
      <CardHeader
        icon={List}
        title="Assignments"
        right={
          <Button onClick={() => create.mutate()} disabled={create.isPending}>
            <Plus className="h-4 w-4" aria-hidden="true" />
            New assignment
          </Button>
        }
      />
      {isPending && <LoadingState />}
      {isError && <p className="px-7 py-5 text-sm text-fail">{error.message}</p>}
      {(create.isError || publish.isError) && (
        <div className="px-7 pt-4">
          <FormError>{(create.error ?? publish.error).message}</FormError>
        </div>
      )}
      {assignments?.length === 0 && (
        <EmptyState title="No assignments yet">Create the first one with “New assignment”.</EmptyState>
      )}
      {assignments?.length > 0 && (
        <>
          <table className="w-full text-left">
            <thead className="bg-raised text-sm text-muted">
              <tr>
                <th className="px-7 py-3 font-semibold">Assignment</th>
                <th className="px-3 py-3 font-semibold">Status</th>
                <th className="px-3 py-3 font-semibold">Student results</th>
                <th className="px-7 py-3" />
              </tr>
            </thead>
            <tbody>
              {assignments.map((assignment) => {
                const chip = STATUS_CHIP[assignment.status];
                const isDraft = assignment.status === "draft";
                return (
                  <tr key={assignment.id} className="border-t border-line">
                    <td className="px-7 py-5">
                      <span className="block font-semibold">{assignment.title}</span>
                      <span className="block text-sm text-muted">{describe(assignment)}</span>
                    </td>
                    <td className="px-3 py-5">
                      <Chip tone={chip.tone} icon={chip.icon}>
                        {chip.label}
                      </Chip>
                    </td>
                    <td className="w-64 px-3 py-5">
                      {isDraft ? (
                        <span className="text-sm text-muted">Students can't see it yet.</span>
                      ) : (
                        <ResultBar
                          buckets={assignment.result_buckets ?? { full: 0, partial: 0, none: 0 }}
                          submitted={assignment.submitted_count ?? 0}
                          enrolled={assignment.enrolled_count ?? 0}
                        />
                      )}
                    </td>
                    <td className="px-7 py-5">
                      <span className="flex justify-end gap-3">
                        <Link to={`/teacher/assignments/${assignment.id}/edit`} className={buttonClass("neutral")}>
                          Edit
                        </Link>
                        {isDraft ? (
                          <Button onClick={() => publish.mutate(assignment.id)} disabled={publish.isPending}>
                            Publish
                          </Button>
                        ) : (
                          <Link
                            to={`/teacher/assignments/${assignment.id}/submissions`}
                            className={buttonClass("outline")}
                          >
                            Results
                          </Link>
                        )}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          <p className="flex flex-wrap gap-6 border-t border-line px-7 py-4 text-sm text-muted">
            <span className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-sm bg-pass" /> passed all tests
            </span>
            <span className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-sm bg-warn" /> passed some
            </span>
            <span className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-sm bg-fail" /> passed none
            </span>
          </p>
        </>
      )}
    </Card>
  );
}

function EnrollmentCodeCard({ course }) {
  const queryClient = useQueryClient();
  const [copied, setCopied] = useState(false);
  const regenerate = useMutation({
    mutationFn: () => newJoinCode(course.id),
    onSuccess: (updated) => {
      queryClient.setQueryData(["course", course.id], updated);
      queryClient.invalidateQueries({ queryKey: ["courses"] });
    },
  });

  async function copy() {
    try {
      await navigator.clipboard.writeText(course.join_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  }

  function handleNewCode() {
    if (window.confirm("Generate a new code? The current code will stop working.")) regenerate.mutate();
  }

  return (
    <Card>
      <CardHeader icon={Ticket} title="Enrollment code" border={false} />
      <div className="space-y-5 px-7 pb-7">
        <p
          className="rounded-lg border border-dashed border-accent/60 bg-raised py-6 text-center font-mono text-3xl tracking-[0.3em]"
          aria-label="Enrollment code"
        >
          {course.join_code}
        </p>
        <p className="text-sm text-muted">Students enter this code on their profile to join the course.</p>
        <div className="grid grid-cols-2 gap-3">
          <Button variant="outline" onClick={copy}>
            <Copy className="h-4 w-4" aria-hidden="true" />
            {copied ? "Copied" : "Copy code"}
          </Button>
          <Button variant="neutral" onClick={handleNewCode} disabled={regenerate.isPending}>
            New code
          </Button>
        </div>
        <FormError>{regenerate.isError ? regenerate.error.message : ""}</FormError>
      </div>
    </Card>
  );
}

function ConceptsCard({ courseId }) {
  const queryClient = useQueryClient();
  const [adding, setAdding] = useState(false);
  const [name, setName] = useState("");
  const { data: concepts } = useQuery({
    queryKey: ["concepts", courseId],
    queryFn: () => listConcepts(courseId),
  });
  const add = useMutation({
    mutationFn: () => createConcept(courseId, name.trim()),
    onSuccess: () => {
      setName("");
      setAdding(false);
      queryClient.invalidateQueries({ queryKey: ["concepts", courseId] });
    },
  });

  return (
    <Card>
      <CardHeader icon={FlaskConical} title="Concepts in this course" border={false} />
      <div className="space-y-4 px-7 pb-7">
        <div className="flex flex-wrap items-center gap-2">
          {concepts?.map((concept) => (
            <Chip key={concept.id}>{concept.name}</Chip>
          ))}
          {concepts?.length === 0 && <span className="text-sm text-muted">No concepts yet.</span>}
          {!adding && (
            <button type="button" className="px-2 text-sm text-muted hover:text-ink" onClick={() => setAdding(true)}>
              Add concept
            </button>
          )}
        </div>
        {adding && (
          <form
            className="flex gap-2"
            onSubmit={(event) => {
              event.preventDefault();
              if (name.trim()) add.mutate();
            }}
          >
            <input
              className={`${inputClass} py-2`}
              aria-label="Concept name"
              placeholder="e.g. Recursion"
              value={name}
              maxLength={80}
              autoFocus
              onChange={(event) => setName(event.target.value)}
            />
            <Button type="submit" disabled={!name.trim() || add.isPending}>
              Add
            </Button>
          </form>
        )}
        <FormError>{add.isError ? add.error.message : ""}</FormError>
      </div>
    </Card>
  );
}

/** Teacher view of one course (mockup 10). Tabs: Assignments now, Materials from Step 8. */
export default function CoursePage() {
  const courseId = Number(useParams().courseId);
  const { data: course, isPending, isError, error, refetch } = useCourse(courseId);
  const stats = useQuery({ queryKey: ["course-stats", courseId], queryFn: () => getCourseStats(courseId) });

  if (isPending) return <LoadingState />;
  if (isError) return <ErrorState error={error} onRetry={refetch} />;

  return (
    <>
      <PageHeader
        breadcrumb={
          <Link to="/courses" className="hover:text-ink">
            My courses
          </Link>
        }
        title={course.title}
        right={
          stats.data && (
            <div className="flex gap-12">
              <Stat value={stats.data.students} label="students" />
              <Stat value={stats.data.submissions_today} label="submissions today" />
              <Stat
                value={stats.data.average_score != null ? `${stats.data.average_score}%` : "–"}
                label="average score"
              />
            </div>
          )
        }
      />
      <div className="mb-9 flex gap-2 border-b border-line" role="tablist" aria-label="Course sections">
        <span
          role="tab"
          aria-selected="true"
          className="-mb-px border-b-2 border-accent-soft px-6 py-3 font-semibold text-accent-soft"
        >
          Assignments
        </span>
      </div>
      <div className="grid gap-9 lg:grid-cols-[1fr_360px]">
        <div className="min-w-0">
          <AssignmentsCard courseId={courseId} />
        </div>
        <div className="space-y-9">
          <EnrollmentCodeCard course={course} />
          <ConceptsCard courseId={courseId} />
        </div>
      </div>
    </>
  );
}
