import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route, Routes } from "react-router-dom";
import { expect, test } from "vitest";

import { mockApi, renderApp, STUDENT } from "../test/utils.jsx";
import ConceptReport, { describeFailures } from "./ConceptReport.jsx";

const COURSES = [
  { id: 1, title: "Procedural Programming", color: "indigo", teacher_name: "Dr. Maria Ionescu", assignment_count: 2 },
  { id: 2, title: "Basic Algorithms", color: "blue", teacher_name: "Dr. Radu Pop", assignment_count: 1 },
];

function test_(id, assignment, verdict, extra = {}) {
  return {
    assignment_id: assignment.id,
    assignment_title: assignment.title,
    test_case_id: id,
    test_name: `Test ${id}`,
    is_hidden: false,
    verdict,
    ...extra,
  };
}

const DIGIT_SUM = { id: 3, title: "Digit sum" };
const IO = { id: 4, title: "Input and output" };

const REPORT = {
  course_id: 1,
  course_title: "Procedural Programming",
  assignment_count: 2,
  tests_total: 5,
  tests_passed: 3,
  verdicts: ["passed", "passed", "wrong_answer", "passed", "wrong_answer"],
  thresholds: { review_below: 0.5, mastered_from: 0.8 },
  concepts: [
    {
      concept_id: 10,
      concept: "Negative numbers",
      total: 3,
      passed: 1,
      pass_rate: 1 / 3,
      level: "review",
      assignment_count: 2,
      tests: [
        test_(1, DIGIT_SUM, "passed"),
        test_(2, DIGIT_SUM, "wrong_answer", { test_name: "Hidden test #1", is_hidden: true }),
        test_(5, IO, "wrong_answer"),
      ],
    },
    {
      concept_id: 11,
      concept: "Loops",
      total: 2,
      passed: 2,
      pass_rate: 1,
      level: "mastered",
      assignment_count: 1,
      tests: [test_(1, DIGIT_SUM, "passed"), test_(4, DIGIT_SUM, "passed")],
    },
  ],
};

function renderReport(route = "/report") {
  return renderApp(
    <Routes>
      <Route path="/report" element={<ConceptReport />} />
    </Routes>,
    { route, user: STUDENT },
  );
}

test("shows concepts with levels, the review list and links back to assignments", async () => {
  mockApi({ "GET /courses": COURSES, "GET /courses/1/reports/concepts/me": REPORT });

  renderReport();

  expect(await screen.findByRole("heading", { name: "Where you go wrong" })).toBeInTheDocument();
  expect(await screen.findByText("3 of 5 tests passed across 2 assignments")).toBeInTheDocument();
  const table = screen.getByRole("table");
  expect(within(table).getByText("Negative numbers")).toBeInTheDocument();
  expect(within(table).getByText("33%")).toBeInTheDocument();
  expect(within(table).getAllByText("Review")).toHaveLength(2); // column chip + phone chip
  expect(within(table).getAllByText("Mastered")).toHaveLength(2); // column chip + phone chip
  expect(
    screen.getByText("You failed the hidden test in Digit sum and “Test 5” in Input and output."),
  ).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Reopen Digit sum" })).toHaveAttribute("href", "/assignments/3");
  expect(screen.getByRole("link", { name: "Reopen Input and output" })).toHaveAttribute(
    "href",
    "/assignments/4",
  );
  expect(screen.getByText(/Below 50% you should review/)).toBeInTheDocument();
});

test("switching the course asks for that course's report", async () => {
  const { calls } = mockApi({
    "GET /courses": COURSES,
    "GET /courses/1/reports/concepts/me": REPORT,
    "GET /courses/2/reports/concepts/me": { ...REPORT, course_id: 2, course_title: "Basic Algorithms", concepts: [] },
  });
  const user = userEvent.setup();
  renderReport();
  await screen.findByText("3 of 5 tests passed across 2 assignments");

  await user.selectOptions(screen.getByLabelText("Course"), "2");

  expect(await screen.findByText("Nothing to report yet")).toBeInTheDocument();
  expect(calls.some((call) => call.path === "/courses/2/reports/concepts/me")).toBe(true);
});

test("opens the course named in the address", async () => {
  const { calls } = mockApi({
    "GET /courses": COURSES,
    "GET /courses/2/reports/concepts/me": { ...REPORT, course_id: 2, concepts: [] },
  });

  renderReport("/report?course=2");

  expect(await screen.findByText("Nothing to report yet")).toBeInTheDocument();
  expect(calls.some((call) => call.path === "/courses/1/reports/concepts/me")).toBe(false);
});

test("a student without courses gets a clear empty state", async () => {
  mockApi({ "GET /courses": [] });

  renderReport();

  expect(await screen.findByText("No courses yet")).toBeInTheDocument();
});

test("describeFailures groups failed tests per assignment", () => {
  const concept = {
    tests: [test_(1, DIGIT_SUM, "wrong_answer"), test_(2, DIGIT_SUM, "time_limit"), test_(3, IO, "passed")],
  };

  expect(describeFailures(concept)).toBe("You failed 2 tests in Digit sum.");
  expect(describeFailures({ tests: [test_(3, IO, "passed")] })).toBe("No failed tests.");
});
