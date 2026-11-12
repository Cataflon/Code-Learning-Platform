import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route, Routes } from "react-router-dom";
import { expect, test, vi } from "vitest";

import { mockApi, renderApp, STUDENT } from "../test/utils.jsx";
import AssignmentPage from "./AssignmentPage.jsx";

// Monaco cannot run in jsdom: a textarea stands in for it.
vi.mock("../components/CodeEditor.jsx", () => ({
  default: ({ value, onChange }) => (
    <textarea aria-label="Code editor" value={value} onChange={(e) => onChange(e.target.value)} />
  ),
}));

const ASSIGNMENT = {
  id: 3,
  course_id: 1,
  course_title: "Procedural Programming",
  title: "Digit sum",
  description: "Read an integer and print the **sum of its digits**.",
  time_limit_ms: 2000,
  memory_limit_mb: 128,
  due_at: null,
  max_submissions: 10,
  submissions_left: 8,
  status: "open",
  test_count: 2,
  hidden_test_count: 1,
};

const TESTS = [
  { id: 7, name: "Simple case", input_data: "1234\n", expected_output: "10\n", position: 0, concepts: [] },
];

function result(overrides) {
  return {
    test_case_id: 7,
    name: "Simple case",
    position: 0,
    is_hidden: false,
    verdict: null,
    runtime_ms: null,
    concepts: ["Loops"],
    hint: null,
    input_data: "1234\n",
    expected_output: "10\n",
    actual_output: null,
    stderr: null,
    ...overrides,
  };
}

function submission(overrides) {
  return {
    id: 41,
    assignment_id: 3,
    attempt_number: 2,
    status: "done",
    score: 50,
    passed_count: 1,
    total_count: 2,
    verdicts: ["passed", "wrong_answer"],
    error_message: null,
    created_at: new Date().toISOString(),
    code: "print(1)",
    results: [
      result({ verdict: "passed", runtime_ms: 31 }),
      result({
        test_case_id: 9,
        name: "Hidden test #1",
        is_hidden: true,
        verdict: "wrong_answer",
        runtime_ms: 29,
        concepts: ["Negative numbers"],
        hint: "Check the sign.",
        input_data: null,
        expected_output: null,
      }),
    ],
    ...overrides,
  };
}

function renderPage() {
  return renderApp(
    <Routes>
      <Route path="/assignments/:assignmentId" element={<AssignmentPage />} />
    </Routes>,
    { route: "/assignments/3", user: STUDENT },
  );
}

test("shows the problem, the limits and the latest result", async () => {
  mockApi({
    "GET /assignments/3": ASSIGNMENT,
    "GET /assignments/3/test-cases": TESTS,
    "GET /assignments/3/submissions": [submission()],
    "GET /submissions/41": submission(),
  });

  renderPage();

  expect(await screen.findByRole("heading", { name: "Digit sum" })).toBeInTheDocument();
  expect(screen.getByText("sum of its digits")).toBeInTheDocument(); // Markdown rendered
  expect(screen.getByText("8 of 10 attempts left")).toBeInTheDocument();
  expect(screen.getByText("2 s per test, 128 MB")).toBeInTheDocument();
  expect(screen.getByText(/Some tests are hidden/)).toBeInTheDocument();
  expect(await screen.findByText("Result of attempt 2")).toBeInTheDocument();
  expect(screen.getByText("1 of 2 passed")).toBeInTheDocument();
  expect(screen.getByText(/Hint from your teacher: Check the sign/)).toBeInTheDocument();
  expect(screen.getByText("This will be your second attempt")).toBeInTheDocument();
});

test("submitting sends the code and shows the tests while they run", async () => {
  const queued = submission({
    id: 42,
    attempt_number: 1,
    status: "queued",
    score: null,
    passed_count: 0,
    verdicts: [null, null],
    results: [result(), result({ test_case_id: 9, name: "Hidden test #1", is_hidden: true })],
  });
  const done = submission({ id: 42, attempt_number: 1 });
  let polls = 0;
  const { calls } = mockApi({
    "GET /assignments/3": ASSIGNMENT,
    "GET /assignments/3/test-cases": TESTS,
    "GET /assignments/3/submissions": [],
    "POST /assignments/3/submissions": [202, queued],
    "GET /submissions/42": () => (polls++ === 0 ? { ...queued, status: "running" } : done),
  });
  const user = userEvent.setup();
  renderPage();
  const editor = await screen.findByLabelText("Code editor");

  await user.clear(editor);
  await user.type(editor, "print(10)");
  await user.click(screen.getByRole("button", { name: /Submit/ }));

  // Right after the 202 answer: both tests are listed without a verdict.
  expect(await screen.findByText("Result of attempt 1")).toBeInTheDocument();
  expect(screen.getAllByText("Waiting").length).toBeGreaterThan(0);
  expect(screen.getByRole("button", { name: /Submit/ })).toBeDisabled();
  const post = calls.find((call) => call.method === "POST");
  expect(JSON.parse(post.body)).toEqual({ code: "print(10)" });
  // Polling brings the final result without any further action.
  await waitFor(() => expect(screen.getByText("1 of 2 passed")).toBeInTheDocument(), {
    timeout: 4000,
  });
  expect(screen.getByText("Passed")).toBeInTheDocument();
  expect(screen.getByText("Failed")).toBeInTheDocument();
});

test("keeps the draft in localStorage", async () => {
  mockApi({
    "GET /assignments/3": ASSIGNMENT,
    "GET /assignments/3/test-cases": TESTS,
    "GET /assignments/3/submissions": [],
  });
  const user = userEvent.setup();
  renderPage();
  const editor = await screen.findByLabelText("Code editor");

  await user.clear(editor);
  await user.type(editor, "x = 1");

  expect(localStorage.getItem("autograder.draft.3")).toBe("x = 1");
});

test("no attempts left disables submitting", async () => {
  mockApi({
    "GET /assignments/3": { ...ASSIGNMENT, submissions_left: 0 },
    "GET /assignments/3/test-cases": TESTS,
    "GET /assignments/3/submissions": [],
  });

  renderPage();

  expect(await screen.findByText("You have used all your attempts.")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /Submit/ })).toBeDisabled();
});

test("a server refusal such as 429 is shown next to the button", async () => {
  mockApi({
    "GET /assignments/3": ASSIGNMENT,
    "GET /assignments/3/test-cases": TESTS,
    "GET /assignments/3/submissions": [],
    "POST /assignments/3/submissions": [
      429,
      { detail: "Wait 4 more second(s) before submitting again", code: "too_many_requests" },
    ],
  });
  const user = userEvent.setup();
  renderPage();
  await screen.findByLabelText("Code editor");

  await user.click(screen.getByRole("button", { name: /Submit/ }));

  expect(await screen.findByRole("alert")).toHaveTextContent("Wait 4 more second(s)");
});
