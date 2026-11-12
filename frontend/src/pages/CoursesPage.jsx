import { MessageSquare } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";

import { courseBarClass } from "../components/courseColors.js";
import { EmptyState, ErrorState, LoadingState } from "../components/states.jsx";
import { Button, Card, CardHeader, Chip, FormError, inputClass, PageHeader } from "../components/ui.jsx";
import { useAssignments, useCourses, useJoinCourse } from "../hooks/useCourses.js";
import { formatDay, plural } from "../lib/format.js";

function CourseAssignments({ course }) {
  const { data, isPending, isError, error } = useAssignments(course.id);

  return (
    <Card className="overflow-hidden">
      <div className="flex">
        <span className={`w-1.5 shrink-0 ${courseBarClass(course.color)}`} aria-hidden="true" />
        <div className="min-w-0 flex-1">
          <CardHeader
            icon={MessageSquare}
            title={course.title}
            subtitle={`${course.teacher_name}, ${plural(course.assignment_count, "assignment")}`}
          />
          {isPending && <LoadingState />}
          {isError && <p className="px-7 py-5 text-sm text-fail">{error.message}</p>}
          {data?.length === 0 && (
            <p className="px-7 py-5 text-sm text-muted">No assignments published yet.</p>
          )}
          <ul>
            {data?.map((assignment) => (
              <li key={assignment.id} className="border-b border-line last:border-b-0">
                <Link
                  to={`/assignments/${assignment.id}`}
                  className="flex flex-wrap items-center gap-4 px-7 py-4 hover:bg-raised"
                >
                  <span className="flex-1 font-semibold">{assignment.title}</span>
                  <span className="text-sm text-muted">
                    {assignment.due_at ? `Due ${formatDay(assignment.due_at)}` : "No deadline"}
                  </span>
                  <Chip tone={assignment.status === "open" ? "info" : "neutral"}>
                    {assignment.status === "open" ? "Open" : "Closed"}
                  </Chip>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </Card>
  );
}

export function JoinCourseForm() {
  const [code, setCode] = useState("");
  const join = useJoinCourse();

  function handleSubmit(event) {
    event.preventDefault();
    join.mutate(code.trim(), { onSuccess: () => setCode("") });
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <label htmlFor="join-code" className="block text-sm font-semibold text-accent-soft/90">
        Join a course
      </label>
      <div className="flex gap-4">
        <input
          id="join-code"
          className={`${inputClass} font-mono`}
          placeholder="Code from your teacher, e.g. PP4K7MAB"
          value={code}
          onChange={(event) => setCode(event.target.value)}
        />
        <Button type="submit" size="lg" disabled={!code.trim() || join.isPending} className="shrink-0">
          Join course
        </Button>
      </div>
      <FormError>{join.isError ? join.error.message : ""}</FormError>
    </form>
  );
}

/** Student view of "Courses": every course with its published assignments. */
export default function CoursesPage() {
  const { data: courses, isPending, isError, error, refetch } = useCourses();

  return (
    <>
      <PageHeader title="Courses" subtitle="Your courses and their assignments." />
      {isPending && <LoadingState />}
      {isError && <ErrorState error={error} onRetry={refetch} />}
      <div className="space-y-9">
        {courses?.length === 0 && (
          <Card>
            <EmptyState title="You are not enrolled in any course yet">
              Enter the code you got from your teacher below.
            </EmptyState>
          </Card>
        )}
        {courses?.map((course) => (
          <CourseAssignments key={course.id} course={course} />
        ))}
        {courses && (
          <Card className="p-7">
            <JoinCourseForm />
          </Card>
        )}
      </div>
    </>
  );
}
