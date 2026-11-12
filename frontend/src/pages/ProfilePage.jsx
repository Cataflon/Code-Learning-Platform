import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { KeyRound, LogOut, MessageSquare, User } from "lucide-react";
import { useState } from "react";

import * as authApi from "../api/auth.js";
import { leaveCourse } from "../api/courses.js";
import { getActivity } from "../api/dashboard.js";
import { useAuth } from "../auth/AuthContext.jsx";
import ActivityGrid from "../components/ActivityGrid.jsx";
import { courseBarClass } from "../components/courseColors.js";
import { LoadingState } from "../components/states.jsx";
import { Avatar, Button, Card, CardHeader, FormError, PageHeader, Stat, TextField } from "../components/ui.jsx";
import { useCourses } from "../hooks/useCourses.js";
import { monthYear, plural } from "../lib/format.js";
import { JoinCourseForm } from "./CoursesPage.jsx";

const WEEKS = 14;

function Saved({ children }) {
  return (
    <p className="text-sm text-pass" role="status">
      {children}
    </p>
  );
}

function PersonalDetails() {
  const { user, setUser } = useAuth();
  const [name, setName] = useState(user.full_name);
  const save = useMutation({
    mutationFn: () => authApi.updateMe(name),
    onSuccess: (updated) => setUser(updated),
  });

  return (
    <Card>
      <CardHeader icon={User} title="Personal details" border={false} />
      <form
        className="space-y-5 px-7 pb-7"
        onSubmit={(event) => {
          event.preventDefault();
          save.mutate();
        }}
      >
        <TextField label="Display name" value={name} onChange={(e) => setName(e.target.value)} maxLength={120} />
        <TextField label="Email" value={user.email} disabled hint="Used to sign in, so it can't be changed." />
        <FormError>{save.isError ? save.error.message : ""}</FormError>
        {save.isSuccess && <Saved>Name saved.</Saved>}
        <Button
          type="submit"
          variant="outline"
          size="lg"
          className="w-full"
          disabled={save.isPending || !name.trim() || name.trim() === user.full_name}
        >
          Save name
        </Button>
      </form>
    </Card>
  );
}

function ChangePassword() {
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const change = useMutation({
    mutationFn: () => authApi.changePassword(current, next),
    onSuccess: () => {
      setCurrent("");
      setNext("");
    },
  });

  return (
    <Card>
      <CardHeader icon={KeyRound} title="Change password" border={false} />
      <form
        className="space-y-5 px-7 pb-7"
        onSubmit={(event) => {
          event.preventDefault();
          change.mutate();
        }}
      >
        <TextField
          label="Current password"
          type="password"
          autoComplete="current-password"
          value={current}
          onChange={(e) => setCurrent(e.target.value)}
        />
        <TextField
          label="New password"
          type="password"
          autoComplete="new-password"
          placeholder="At least 8 characters"
          value={next}
          onChange={(e) => setNext(e.target.value)}
        />
        <FormError>{change.isError ? change.error.message : ""}</FormError>
        {change.isSuccess && <Saved>Password changed.</Saved>}
        <Button
          type="submit"
          variant="outline"
          size="lg"
          className="w-full"
          disabled={change.isPending || !current || next.length < 8}
        >
          Change password
        </Button>
      </form>
    </Card>
  );
}

function YourCourses({ isStudent }) {
  const queryClient = useQueryClient();
  const { data: courses, isPending } = useCourses();
  const leave = useMutation({
    mutationFn: (courseId) => leaveCourse(courseId),
    onSuccess: () => queryClient.invalidateQueries(),
  });

  function handleLeave(course) {
    if (window.confirm(`Leave ${course.title}? Your submissions stay, but you lose access.`)) {
      leave.mutate(course.id);
    }
  }

  return (
    <Card className="overflow-hidden">
      <CardHeader icon={MessageSquare} title="Your courses" />
      {isPending && <LoadingState />}
      {courses?.length === 0 && (
        <p className="px-7 py-6 text-sm text-muted">
          {isStudent ? "You are not enrolled in any course yet." : "You have not created a course yet."}
        </p>
      )}
      <ul>
        {courses?.map((course) => (
          <li key={course.id} className="flex items-center gap-4 border-b border-line px-7 py-4">
            <span className={`h-12 w-1 shrink-0 rounded-full ${courseBarClass(course.color)}`} aria-hidden="true" />
            <span className="min-w-0 flex-1">
              <span className="block font-semibold">{course.title}</span>
              <span className="block text-sm text-muted">
                {course.teacher_name}, {plural(course.assignment_count, "assignment")}
              </span>
            </span>
            {isStudent && (
              <Button variant="neutral" onClick={() => handleLeave(course)} disabled={leave.isPending}>
                Leave course
              </Button>
            )}
          </li>
        ))}
      </ul>
      {leave.isError && (
        <div className="px-7 py-4">
          <FormError>{leave.error.message}</FormError>
        </div>
      )}
      {isStudent && (
        <div className="bg-raised/60 px-7 py-6">
          <JoinCourseForm />
        </div>
      )}
    </Card>
  );
}

export default function ProfilePage() {
  const { user, logout } = useAuth();
  const isStudent = user.role === "student";
  const activity = useQuery({
    queryKey: ["activity", WEEKS],
    queryFn: () => getActivity(WEEKS),
    enabled: isStudent,
  });
  const totals = activity.data?.totals;

  return (
    <>
      <PageHeader
        title="Your profile"
        subtitle="Manage your account, your courses and your password."
        right={
          <div className="text-right">
            <div className="font-semibold capitalize">{user.role}</div>
            <div className="text-sm text-muted">Member since {monthYear(user.created_at)}</div>
          </div>
        }
      />
      <div className="grid gap-9 lg:grid-cols-[1fr_360px]">
        <div className="min-w-0 space-y-9">
          <Card>
            <div className="flex flex-wrap items-center gap-7 p-7">
              <Avatar name={user.full_name} size="lg" />
              <div className="min-w-0 flex-1">
                <h2 className="text-2xl font-semibold">{user.full_name}</h2>
                <p className="text-muted">{user.email}</p>
              </div>
              {isStudent && totals && (
                <div className="flex gap-10">
                  <Stat value={totals.submissions} label="submissions" />
                  <Stat value={totals.solved} label="solved at 100%" />
                  <Stat value={totals.concepts_mastered} label="concepts mastered" />
                </div>
              )}
            </div>
            {isStudent && (
              <div className="border-t border-line p-7">
                <div className="mb-5 flex items-baseline justify-between">
                  <h3 className="font-semibold">Activity</h3>
                  <span className="text-sm text-muted">submissions per day, last {WEEKS} weeks</span>
                </div>
                {activity.isPending && <LoadingState />}
                {activity.isError && <FormError>{activity.error.message}</FormError>}
                {activity.data && <ActivityGrid days={activity.data.days} weeks={WEEKS} />}
              </div>
            )}
          </Card>
          <YourCourses isStudent={isStudent} />
        </div>
        <div className="space-y-9">
          <PersonalDetails />
          <ChangePassword />
          {/* JWT is stateless: signing out only removes the token from this browser. */}
          <Button variant="danger" size="lg" className="w-full" onClick={logout}>
            <LogOut className="h-4 w-4" aria-hidden="true" />
            Sign out
          </Button>
        </div>
      </div>
    </>
  );
}
