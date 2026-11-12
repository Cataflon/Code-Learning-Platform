import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route, Routes } from "react-router-dom";
import { expect, test } from "vitest";

import { mockApi, renderApp, TEACHER } from "../../test/utils.jsx";
import SubmissionsPage from "./SubmissionsPage.jsx";

const ASSIGNMENT = { id: 3, course_id: 1, course_title: "Procedural Programming", title: "Digit sum" };

const STATS = {
  submission_count: 8,
  submitted_count: 3,
  enrolled_count: 4,
  running_count: 0,
  average_score: 67,
  tests: [
    { test_case_id: 1, name: "Simple case", is_hidden: false, concepts: ["Loops"], passed: 3, total: 3, pass_rate: 1 },
    {
      test_case_id: 2,
      name: "Hidden test",
      is_hidden: true,
      concepts: ["Negative numbers"],
      passed: 1,
      total: 3,
      pass_rate: 1 / 3,
    },
  ],
  score_distribution: [
    { label: "0–25%", count: 1 },
    { label: "26–50%", count: 0 },
    { label: "51–75%", count: 1 },
    { label: "76–99%", count: 0 },
    { label: "100%", count: 1 },
  ],
};

function row(id, name, overrides = {}) {
  return {
    id,
    assignment_id: 3,
    student_id: id,
    student_name: name,
    attempt_number: 1,
    status: "done",
    score: 50,
    passed_count: 1,
    total_count: 2,
    verdicts: ["passed", "wrong_answer"],
    error_excerpt: null,
    created_at: new Date(Date.now() - 3600 * 1000).toISOString(),
    ...overrides,
  };
}

const COUNTS = { all: 8, correct: 2, partial: 4, wrong: 2, running: 0 };

function setup() {
  const api = mockApi({
    "GET /assignments/3": ASSIGNMENT,
    "GET /assignments/3/stats": STATS,
    "GET /assignments/3/submissions": ({ url }) => {
      const params = new URL(url, "http://x").searchParams;
      const page = Number(params.get("page"));
      const verdict = params.get("verdict");
      const items =
        verdict === "wrong"
          ? [row(20, "Sorina Lazar", { score: 0, verdicts: ["wrong_answer", "wrong_answer"], error_excerpt: "IndexError, line 4" })]
          : page === 2
            ? [row(11, "Radu Stan"), row(12, "Mihai Ciobanu")]
            : [row(1, "Ana Pop"), row(2, "Elena Matei", { score: 100, verdicts: ["passed", "passed"] })];
      return { items, total: COUNTS[verdict] ?? 8, page, page_size: 6, counts: COUNTS };
    },
    "GET /submissions/1": {
      ...row(1, "Ana Pop"),
      code: "print(int(input()))",
      error_message: null,
      results: [],
    },
  });
  renderApp(
    <Routes>
      <Route path="/teacher/assignments/:assignmentId/submissions" element={<SubmissionsPage />} />
    </Routes>,
    { route: "/teacher/assignments/3/submissions", user: TEACHER },
  );
  return { ...api, user: userEvent.setup() };
}

function lastListCall(calls) {
  const call = calls.filter((c) => c.path === "/assignments/3/submissions").at(-1);
  return new URL(call.url, "http://x").searchParams;
}

test("shows statistics, pass rates and the weakest test", async () => {
  setup();

  expect(await screen.findByRole("heading", { name: "Submissions and statistics" })).toBeInTheDocument();
  expect(screen.getByText("3 of 4")).toBeInTheDocument();
  expect(screen.getByText("67%")).toBeInTheDocument();
  expect(screen.getByText("33%")).toBeInTheDocument();
  expect(screen.getByText(/Only 33% pass “Hidden test”, which checks the concept “Negative numbers”/)).toBeInTheDocument();
  expect(screen.getByText("51–75%: 1 students")).toBeInTheDocument(); // text twin of the chart
  expect(await screen.findByText("Ana Pop")).toBeInTheDocument();
  expect(screen.getByRole("tab", { name: "Partial 4" })).toBeInTheDocument();
  expect(screen.getByText("1–6 of 8")).toBeInTheDocument();
});

test("filter tabs and pagination change the request", async () => {
  const { user, calls } = setup();
  await screen.findByText("Ana Pop");

  await user.click(screen.getByRole("button", { name: "Next" }));
  expect(await screen.findByText("Radu Stan")).toBeInTheDocument();
  expect(lastListCall(calls).get("page")).toBe("2");
  expect(screen.getByText("7–8 of 8")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Next" })).toBeDisabled();

  await user.click(screen.getByRole("tab", { name: "Wrong 2" }));
  expect(await screen.findByText("Sorina Lazar")).toBeInTheDocument();
  expect(screen.getByText("runtime error: IndexError, line 4")).toBeInTheDocument();
  const params = lastListCall(calls);
  expect(params.get("verdict")).toBe("wrong");
  expect(params.get("page")).toBe("1"); // changing the filter goes back to the first page
});

test("search is sent to the server after a short pause", async () => {
  const { user, calls } = setup();
  await screen.findByText("Ana Pop");

  await user.type(screen.getByLabelText("Search for a student"), "elena");

  await waitFor(() => expect(lastListCall(calls).get("q")).toBe("elena"));
});

test("the Code link opens the submitted code", async () => {
  const { user } = setup();
  await screen.findByText("Ana Pop");

  await user.click(screen.getByRole("button", { name: /Show the code of Ana Pop/ }));

  const dialog = await screen.findByRole("dialog");
  expect(await within(dialog).findByText("print(int(input()))")).toBeInTheDocument();
  await user.keyboard("{Escape}");
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
});
