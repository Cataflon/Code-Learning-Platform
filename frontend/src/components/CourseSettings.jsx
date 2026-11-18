// What a teacher can change about a course: its details, its students, or the course itself.

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Pencil, Settings, Trash2, UserMinus, Users } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { deleteCourse, listStudents, removeStudent, updateCourse } from "../api/courses.js";
import { COURSE_COLORS, courseBarClass } from "./courseColors.js";
import Modal from "./Modal.jsx";
import { EmptyState, LoadingState } from "./states.jsx";
import { Avatar, Button, Card, CardHeader, FormError, inputClass, TextField } from "./ui.jsx";
import { formatDay } from "../lib/format.js";

function EditCourseDialog({ course, onClose }) {
  const queryClient = useQueryClient();
  const [title, setTitle] = useState(course.title);
  const [description, setDescription] = useState(course.description ?? "");
  const [color, setColor] = useState(course.color);
  const save = useMutation({
    mutationFn: () => updateCourse(course.id, { title: title.trim(), description, color }),
    onSuccess: (updated) => {
      queryClient.setQueryData(["course", course.id], updated);
      queryClient.invalidateQueries({ queryKey: ["courses"] });
      onClose();
    },
  });

  return (
    <Modal
      title="Edit course"
      onClose={onClose}
      footer={
        <>
          <Button variant="neutral" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" form="edit-course" disabled={!title.trim() || save.isPending}>
            Save
          </Button>
        </>
      }
    >
      <form
        id="edit-course"
        className="grid gap-5 px-6 py-6"
        onSubmit={(event) => {
          event.preventDefault();
          save.mutate();
        }}
      >
        <TextField label="Title" value={title} onChange={(event) => setTitle(event.target.value)} maxLength={200} />
        <label className="label">
          Description
          <textarea
            className={`${inputClass} mt-1 min-h-28`}
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            maxLength={5000}
          />
        </label>
        <div>
          <span className="label">Color</span>
          <div className="flex gap-2 py-2" role="radiogroup" aria-label="Course color">
            {COURSE_COLORS.map((name) => (
              <button
                key={name}
                type="button"
                role="radio"
                aria-checked={color === name}
                aria-label={name}
                onClick={() => setColor(name)}
                className={`h-8 w-8 ${courseBarClass(name)} ${
                  color === name ? "ring-2 ring-white ring-offset-2 ring-offset-black" : "opacity-60"
                }`}
              />
            ))}
          </div>
        </div>
        <FormError>{save.isError ? save.error.message : ""}</FormError>
      </form>
    </Modal>
  );
}

function DeleteCourseDialog({ course, onClose }) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [typed, setTyped] = useState("");
  const remove = useMutation({
    mutationFn: () => deleteCourse(course.id),
    onSuccess: () => {
      queryClient.removeQueries({ queryKey: ["course", course.id] });
      queryClient.invalidateQueries({ queryKey: ["courses"] });
      navigate("/courses", { replace: true });
    },
  });
  const matches = typed.trim() === course.title.trim();

  return (
    <Modal
      title="Delete this course?"
      subtitle="Its assignments, tests, submissions, materials and enrollments are deleted for good. This cannot be undone."
      onClose={onClose}
      footer={
        <>
          <Button variant="neutral" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="danger" disabled={!matches || remove.isPending} onClick={() => remove.mutate()}>
            <Trash2 className="h-4 w-4" aria-hidden="true" />
            Delete course
          </Button>
        </>
      }
    >
      <div className="grid gap-3 px-6 py-6">
        <TextField
          label={`Type the course title to confirm: ${course.title}`}
          value={typed}
          onChange={(event) => setTyped(event.target.value)}
          autoComplete="off"
        />
        <FormError>{remove.isError ? remove.error.message : ""}</FormError>
      </div>
    </Modal>
  );
}

/** Edit the details of the course, or delete it. */
export function CourseSettingsCard({ course }) {
  const [dialog, setDialog] = useState(null);
  return (
    <Card>
      <CardHeader icon={Settings} title="Course" border={false} />
      <div className="grid gap-3 px-7 pb-7">
        {course.description && <p className="plain text-sm text-ink-2">{course.description}</p>}
        <div className="grid grid-cols-2 gap-3">
          <Button variant="outline" onClick={() => setDialog("edit")}>
            <Pencil className="h-4 w-4" aria-hidden="true" />
            Edit course
          </Button>
          <Button variant="danger" onClick={() => setDialog("delete")}>
            <Trash2 className="h-4 w-4" aria-hidden="true" />
            Delete
          </Button>
        </div>
      </div>
      {dialog === "edit" && <EditCourseDialog course={course} onClose={() => setDialog(null)} />}
      {dialog === "delete" && <DeleteCourseDialog course={course} onClose={() => setDialog(null)} />}
    </Card>
  );
}

/** The enrolled students; the teacher can take one out (their submissions stay). */
export function StudentsCard({ courseId }) {
  const queryClient = useQueryClient();
  const students = useQuery({ queryKey: ["students", courseId], queryFn: () => listStudents(courseId) });
  const remove = useMutation({
    mutationFn: (studentId) => removeStudent(courseId, studentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["students", courseId] });
      queryClient.invalidateQueries({ queryKey: ["course-stats", courseId] });
    },
  });

  return (
    <Card>
      <CardHeader
        icon={Users}
        title="Students"
        subtitle={students.data ? `${students.data.length} enrolled` : undefined}
      />
      {students.isPending && <LoadingState />}
      {students.isError && <FormError>{students.error.message}</FormError>}
      {students.data?.length === 0 && (
        <EmptyState title="No students yet">Share the enrollment code with your class.</EmptyState>
      )}
      <FormError>{remove.isError ? remove.error.message : ""}</FormError>
      {students.data?.length > 0 && (
        <ul className="max-h-96 overflow-y-auto">
          {students.data.map((student) => (
            <li key={student.id} className="dash-top flex items-center gap-3 px-6 py-3">
              <Avatar name={student.full_name} />
              <span className="min-w-0 flex-1">
                <b className="block truncate text-ink">{student.full_name}</b>
                <span className="block truncate font-plain text-xs text-ink-3">
                  {student.email} · joined {formatDay(student.enrolled_at)}
                </span>
              </span>
              <Button
                variant="neutral"
                size="sm"
                aria-label={`Remove ${student.full_name}`}
                disabled={remove.isPending}
                onClick={() =>
                  window.confirm(
                    `Remove ${student.full_name} from the course? Their submissions stay; they can join again with the code.`,
                  ) && remove.mutate(student.id)
                }
              >
                <UserMinus className="h-4 w-4" aria-hidden="true" />
              </Button>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
