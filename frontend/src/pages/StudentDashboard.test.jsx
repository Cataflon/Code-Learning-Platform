import { screen, within } from "@testing-library/react";
import { expect, test } from "vitest";

import { mockApi, renderApp, STUDENT } from "../test/utils.jsx";
import StudentDashboard, { nextDeadline } from "./StudentDashboard.jsx";

const inDays = (days) => new Date(Date.now() + days * 24 * 3600 * 1000).toISOString();

function assignment(overrides) {
  return {
    id: 1,
    title: "Digit sum",
    course_id: 1,
    course_title: "Procedural Programming",
    course_color: "indigo",
    due_at: inDays(1),
    status: "open",
    test_count: 4,
    max_submissions: 10,
    attempts_used: 3,
    best_score: 75,
    last_verdicts: ["passed", "passed", "passed", "wrong_answer"],
    last_submission_status: "done",
    ...overrides,
  };
}

const DASHBOARD = {
  stats: { to_submit: 2, average_best_score: 88, concepts_to_review: 1 },
  courses: [{ id: 1, title: "Procedural Programming", color: "indigo", teacher_name: "Dr. Maria Ionescu" }],
  assignments: [
    assignment(),
    assignment({
      id: 2,
      title: "Binary search",
      due_at: inDays(4),
      best_score: null,
      attempts_used: 0,
      last_verdicts: [],
      last_submission_status: null,
      test_count: 6,
    }),
    assignment({ id: 3, title: "Input and output", due_at: inDays(-3), status: "closed", best_score: 100 }),
  ],
  recent_submissions: [
    {
      id: 9,
      assignment_id: 1,
      assignment_title: "Digit sum",
      status: "done",
      score: 75,
      verdicts: ["passed", "passed", "passed", "wrong_answer"],
      created_at: new Date().toISOString(),
    },
  ],
  concepts_to_review: [
    { concept: "Negative numbers", passed: 1, total: 3, verdicts: ["passed", "wrong_answer", "wrong_answer"] },
  ],
};

test("renders the dashboard with assignments, scores and the next deadline", async () => {
  mockApi({ "GET /me/dashboard": DASHBOARD });

  renderApp(<StudentDashboard />, { user: STUDENT });

  expect(await screen.findByText(/Andrei\. Your next deadline:/)).toBeInTheDocument();
  expect(screen.getByRole("heading", { level: 1, name: "Digit sum" })).toBeInTheDocument();
  expect(screen.getByText("88%")).toBeInTheDocument();
  expect(screen.getByText(/due tomorrow at/)).toBeInTheDocument();
  expect(screen.getByRole("timer")).toHaveTextContent(/\d\d:\d\d:\d\d left/);
  expect(screen.getByText("3 of 4 tests pass.")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: /Continue solving/ })).toHaveAttribute("href", "/assignments/1");
  expect(screen.getByRole("link", { name: /Concepts to review/ })).toHaveAttribute("href", "/report");

  const table = screen.getByRole("table");
  expect(within(table).getByText("Binary search")).toBeInTheDocument();
  expect(within(table).getByText("New")).toBeInTheDocument();
  expect(within(table).getByText("75%")).toBeInTheDocument();
  expect(within(table).getByText("100%")).toBeInTheDocument();
  expect(within(table).getByText("Submitted")).toBeInTheDocument();

  expect(screen.getByText("Negative numbers")).toBeInTheDocument();
  expect(screen.getByText("1 of 3 tests pass")).toBeInTheDocument();
});

test("renders empty states when the student has nothing yet", async () => {
  mockApi({
    "GET /me/dashboard": {
      stats: { to_submit: 0, average_best_score: null, concepts_to_review: 0 },
      courses: [],
      assignments: [],
      recent_submissions: [],
      concepts_to_review: [],
    },
  });

  renderApp(<StudentDashboard />, { user: STUDENT });

  expect(await screen.findByText("No assignments yet")).toBeInTheDocument();
  expect(screen.getByText("Nothing to review right now.")).toBeInTheDocument();
  expect(screen.getByText("Your submissions will appear here.")).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "All caught up" })).toBeInTheDocument();
  expect(screen.queryByText(/Your next deadline/)).not.toBeInTheDocument();
});

test("shows the error state when the request fails", async () => {
  mockApi({ "GET /me/dashboard": [500, { detail: "Database is down", code: "http_500" }] });

  renderApp(<StudentDashboard />, { user: STUDENT });

  expect(await screen.findByRole("alert")).toHaveTextContent("Database is down");
});

test("the hero names the failing test and links the recommended pages", async () => {
  mockApi({
    "GET /me/dashboard": {
      ...DASHBOARD,
      assignments: [assignment({ last_submission_id: 9 })],
    },
    "GET /submissions/9/recommendations": {
      submission_id: 9,
      assignment_id: 1,
      failed_tests: [{ test_case_id: 4, name: "Hidden test #1", is_hidden: true, concepts: ["Negative numbers"] }],
      materials: [
        {
          material_id: 5,
          title: "Lecture 4",
          category: "lecture",
          file_type: "pdf",
          page_count: 28,
          pages: "12-15",
          first_page: 12,
          test_count: 1,
          tests: ["Hidden test #1"],
          from_assignment: false,
        },
      ],
    },
  });

  renderApp(<StudentDashboard />, { user: STUDENT });

  expect(await screen.findByText(/“Hidden test #1” fails on negative numbers\./)).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Read Lecture 4, pages 12-15" })).toHaveAttribute(
    "href",
    "/learn/materials/5?page=12&rec=12-15",
  );
});

test("nextDeadline skips solved, closed and past assignments", () => {
  const items = [
    assignment({ id: 1, due_at: inDays(-1) }),
    assignment({ id: 2, due_at: inDays(2), best_score: 100 }),
    assignment({ id: 3, due_at: inDays(5) }),
    assignment({ id: 4, due_at: inDays(3) }),
    assignment({ id: 5, due_at: inDays(1), status: "closed" }),
  ];

  expect(nextDeadline(items).id).toBe(4);
  expect(nextDeadline([])).toBeNull();
});
