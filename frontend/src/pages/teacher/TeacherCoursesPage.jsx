import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { createCourse } from "../../api/courses.js";
import { COURSE_COLORS, courseBarClass } from "../../components/courseColors.js";
import { EmptyState, ErrorState, LoadingState } from "../../components/states.jsx";
import { Button, Card, FormError, PageHeader, TextField } from "../../components/ui.jsx";
import { useCourses } from "../../hooks/useCourses.js";
import { plural } from "../../lib/format.js";

function NewCourseForm() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [color, setColor] = useState(COURSE_COLORS[0]);
  const create = useMutation({
    mutationFn: () => createCourse({ title, color }),
    onSuccess: (course) => {
      queryClient.invalidateQueries({ queryKey: ["courses"] });
      navigate(`/courses/${course.id}`);
    },
  });

  return (
    <Card className="p-7">
      <form
        className="flex flex-wrap items-end gap-5"
        onSubmit={(event) => {
          event.preventDefault();
          create.mutate();
        }}
      >
        <TextField
          label="New course"
          className="min-w-64 flex-1"
          placeholder="Course title"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          maxLength={200}
        />
        <div>
          <span className="mb-2 block text-sm font-semibold text-accent-soft/90">Color</span>
          <div className="flex gap-2 py-2" role="radiogroup" aria-label="Course color">
            {COURSE_COLORS.map((name) => (
              <button
                key={name}
                type="button"
                role="radio"
                aria-checked={color === name}
                aria-label={name}
                onClick={() => setColor(name)}
                className={`h-8 w-8 rounded-full ${courseBarClass(name)} ${
                  color === name ? "ring-2 ring-white ring-offset-2 ring-offset-surface" : "opacity-60"
                }`}
              />
            ))}
          </div>
        </div>
        <Button type="submit" size="lg" disabled={!title.trim() || create.isPending}>
          <Plus className="h-4 w-4" aria-hidden="true" />
          Create course
        </Button>
      </form>
      <div className="mt-4">
        <FormError>{create.isError ? create.error.message : ""}</FormError>
      </div>
    </Card>
  );
}

/** Teacher view of "My courses". No mockup: cards in the style of the Learn screen. */
export default function TeacherCoursesPage() {
  const { data: courses, isPending, isError, error, refetch } = useCourses();

  return (
    <>
      <PageHeader title="My courses" subtitle="Your courses, their assignments and enrollment codes." />
      {isPending && <LoadingState />}
      {isError && <ErrorState error={error} onRetry={refetch} />}
      <div className="space-y-9">
        {courses?.length === 0 && (
          <Card>
            <EmptyState title="No courses yet">Create your first course below.</EmptyState>
          </Card>
        )}
        {courses?.length > 0 && (
          <div className="grid gap-9 md:grid-cols-2 lg:grid-cols-3">
            {courses.map((course) => (
              <Link key={course.id} to={`/courses/${course.id}`} className="group">
                <Card className="flex h-full overflow-hidden group-hover:border-accent-soft/60">
                  <span className={`w-2 shrink-0 ${courseBarClass(course.color)}`} aria-hidden="true" />
                  <div className="p-7">
                    <h2 className="text-xl font-semibold">{course.title}</h2>
                    <p className="mt-2 text-sm text-muted">{plural(course.assignment_count, "assignment")}</p>
                    <p className="mt-4 font-mono tracking-widest text-accent-soft">{course.join_code}</p>
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        )}
        {courses && <NewCourseForm />}
      </div>
    </>
  );
}
