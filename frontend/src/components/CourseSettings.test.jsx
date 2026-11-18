import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route, Routes } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";

import CoursesPage from "../pages/CoursesPage.jsx";
import { mockApi, renderApp, STUDENT, TEACHER } from "../test/utils.jsx";
import { CourseSettingsCard, StudentsCard } from "./CourseSettings.jsx";

const COURSE = {
  id: 1,
  title: "Procedural Programming",
  description: "Python basics",
  color: "indigo",
  join_code: "PP4K7MAB",
  teacher_name: "Dr. Maria Ionescu",
  assignment_count: 2,
};

afterEach(() => vi.restoreAllMocks());

test("the teacher edits the title, description and colour of a course", async () => {
  const { calls } = mockApi({ "PATCH /courses/1": { ...COURSE, title: "Algorithms" } });
  const user = userEvent.setup();
  renderApp(<CourseSettingsCard course={COURSE} />, { user: TEACHER });

  await user.click(screen.getByRole("button", { name: /Edit course/ }));
  const dialog = screen.getByRole("dialog", { name: "Edit course" });
  await user.clear(within(dialog).getByLabelText("Title"));
  await user.type(within(dialog).getByLabelText("Title"), "Algorithms");
  await user.click(within(dialog).getByRole("radio", { name: "green" }));
  await user.click(within(dialog).getByRole("button", { name: "Save" }));

  await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
  expect(JSON.parse(calls.find((call) => call.method === "PATCH").body)).toEqual({
    title: "Algorithms",
    description: "Python basics",
    color: "green",
  });
});

test("deleting a course needs its title typed, then goes back to My courses", async () => {
  const { calls } = mockApi({ "DELETE /courses/1": [204, null] });
  const user = userEvent.setup();
  renderApp(
    <Routes>
      <Route path="/courses/1" element={<CourseSettingsCard course={COURSE} />} />
      <Route path="/courses" element={<p>My courses page</p>} />
    </Routes>,
    { route: "/courses/1", user: TEACHER },
  );

  await user.click(screen.getByRole("button", { name: "Delete" }));
  const dialog = screen.getByRole("dialog", { name: "Delete this course?" });
  const confirm = within(dialog).getByRole("button", { name: /Delete course/ });
  expect(confirm).toBeDisabled();
  await user.type(within(dialog).getByRole("textbox"), "Procedural Programming");
  await user.click(confirm);

  expect(await screen.findByText("My courses page")).toBeInTheDocument();
  expect(calls.some((call) => call.method === "DELETE" && call.path === "/courses/1")).toBe(true);
});

test("the teacher removes a student from the course", async () => {
  vi.spyOn(window, "confirm").mockReturnValue(true);
  const students = [
    { id: 5, full_name: "Andrei Pop", email: "andrei@example.com", enrolled_at: "2026-11-01T10:00:00Z" },
    { id: 6, full_name: "Elena Matei", email: "elena@example.com", enrolled_at: "2026-11-02T10:00:00Z" },
  ];
  const { calls } = mockApi({
    "GET /courses/1/students": () => students,
    "DELETE /courses/1/students/5": [204, null],
  });
  const user = userEvent.setup();
  renderApp(<StudentsCard courseId={1} />, { user: TEACHER });

  expect(await screen.findByText("2 enrolled")).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Remove Andrei Pop" }));

  await waitFor(() =>
    expect(calls.some((call) => call.method === "DELETE" && call.path === "/courses/1/students/5")).toBe(true),
  );
});

test("a student leaves a course from the Courses page", async () => {
  vi.spyOn(window, "confirm").mockReturnValue(true);
  let enrolled = [COURSE];
  const { calls } = mockApi({
    "GET /courses": () => enrolled,
    "GET /courses/1/assignments": [],
    "DELETE /courses/1/enrollment": () => {
      enrolled = [];
      return [204, null];
    },
  });
  const user = userEvent.setup();
  renderApp(<CoursesPage />, { user: STUDENT });

  await user.click(await screen.findByRole("button", { name: /Leave course/ }));

  expect(await screen.findByText("You are not enrolled in any course yet")).toBeInTheDocument();
  expect(calls.some((call) => call.path === "/courses/1/enrollment")).toBe(true);
});
