import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route, Routes } from "react-router-dom";
import { expect, test } from "vitest";

import { mockApi, renderApp, STUDENT } from "../test/utils.jsx";
import Learn from "./Learn.jsx";
import LearnCourse from "./LearnCourse.jsx";

const EMPTY_DASHBOARD = {
  stats: { to_submit: 0, average_best_score: null, concepts_to_review: 0 },
  courses: [],
  assignments: [],
  recent_submissions: [],
  concepts_to_review: [],
};

test("Learn shows one card per course, with an empty state for courses without materials", async () => {
  mockApi({
    "GET /me/dashboard": EMPTY_DASHBOARD,
    "GET /me/learn": [
      { id: 1, title: "Procedural Programming", color: "indigo", teacher_name: "Dr. Maria Ionescu", material_count: 12, last_material_at: new Date().toISOString() },
      { id: 3, title: "Data Structures", color: "purple", teacher_name: "Dr. Ioana Matei", material_count: 0, last_material_at: null },
    ],
  });

  renderApp(<Learn />, { user: STUDENT });

  const link = await screen.findByRole("link", { name: "Procedural Programming, 12 materials" });
  expect(link).toHaveAttribute("href", "/learn/courses/1");
  expect(screen.getByText(/No materials yet/)).toBeInTheDocument();
  expect(screen.queryByRole("link", { name: /Data Structures/ })).not.toBeInTheDocument();
});

test("Learn recommends the top material after the latest imperfect submission", async () => {
  mockApi({
    "GET /me/dashboard": {
      ...EMPTY_DASHBOARD,
      recent_submissions: [
        { id: 41, assignment_id: 3, assignment_title: "Digit sum", status: "done", score: 75, verdicts: [], created_at: new Date().toISOString() },
      ],
    },
    "GET /me/learn": [],
    "GET /submissions/41/recommendations": {
      submission_id: 41,
      assignment_id: 3,
      failed_tests: [{ test_case_id: 9, name: "Hidden test #1", is_hidden: true, concepts: [] }],
      materials: [
        { material_id: 5, title: "Lecture 4", category: "lecture", file_type: "pdf", page_count: 28, pages: "12-15", first_page: 12, test_count: 1, tests: ["Hidden test #1"], from_assignment: false },
      ],
    },
  });

  renderApp(<Learn />, { user: STUDENT });

  const open = await screen.findByRole("link", { name: "Open at page 12" });
  expect(open.getAttribute("href")).toBe("/learn/materials/5?page=12&rec=12-15&from=Digit+sum");
  expect(screen.getByText(/covers what failed in Digit sum/)).toBeInTheDocument();
});

test("the course page filters lectures and labs and shows where a material is used", async () => {
  const material = (id, title, category, used = []) => ({
    id,
    course_id: 1,
    title,
    category,
    file_type: category === "lab" ? "pptx" : "pdf",
    original_filename: `${title}.pdf`,
    size_bytes: 1000,
    page_count: 10,
    created_at: new Date().toISOString(),
    used_in: used,
  });
  mockApi({
    "GET /courses/1": { id: 1, title: "Procedural Programming", color: "indigo", teacher_name: "Dr. Maria Ionescu", assignment_count: 1 },
    "GET /courses/1/materials": [
      material(2, "Lecture 4", "lecture", [{ assignment_id: 3, assignment_title: "Digit sum", for_assignment: true, test_count: 1 }]),
      material(1, "Lab 3", "lab"),
    ],
  });
  const user = userEvent.setup();
  renderApp(
    <Routes>
      <Route path="/learn/courses/:courseId" element={<LearnCourse />} />
    </Routes>,
    { route: "/learn/courses/1", user: STUDENT },
  );

  expect(await screen.findByText("Used in: Digit sum")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Lab 3" })).toHaveAttribute("href", "/learn/materials/1");

  await user.click(screen.getByRole("button", { name: "Labs 1" }));

  const list = screen.getByText("Lab 3").closest(".lessons");
  expect(within(list).queryByText("Lecture 4")).not.toBeInTheDocument();
});
