import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route, Routes } from "react-router-dom";
import { expect, test, vi } from "vitest";

import AssignmentEditor from "../pages/teacher/AssignmentEditor.jsx";
import { mockApi, renderApp, TEACHER } from "../test/utils.jsx";
import { AiGeneratePanel, DraftsPanel } from "./AiTests.jsx";

function job(overrides) {
  return {
    id: 4,
    assignment_id: 3,
    status: "running",
    phase: "writing",
    model: "meta/llama-3.3-70b-instruct",
    tests_requested: 8,
    tests_proposed: null,
    tests_kept: null,
    input_tokens: 0,
    output_tokens: 0,
    error_message: null,
    reference_code: null,
    created_at: new Date().toISOString(),
    started_at: null,
    finished_at: null,
    ...overrides,
  };
}

function draft(id, overrides = {}) {
  return {
    id,
    assignment_id: 3,
    name: `Draft ${id}`,
    input_data: "1234\n",
    expected_output: "10\n",
    is_hidden: false,
    weight: 2,
    position: id,
    hint: null,
    concepts: [{ id: 1, name: "Loops" }],
    source: "ai",
    review_status: "draft",
    generation_job_id: 4,
    ai_rationale: "checks a plain number",
    materials: [],
    ...overrides,
  };
}

test("the panel starts a job, follows its phases and reports the result", async () => {
  const states = [
    job({ phase: "writing" }),
    job({ phase: "sandbox", tests_proposed: 8 }),
    job({ status: "done", phase: "done", tests_proposed: 8, tests_kept: 7 }),
  ];
  const { calls } = mockApi({
    "POST /assignments/3/generate-tests": [202, { job_id: 4 }],
    "GET /generation-jobs/4": () => states.shift() ?? job({ status: "done", phase: "done", tests_proposed: 8, tests_kept: 7 }),
  });
  const onFinished = vi.fn();
  const user = userEvent.setup();
  renderApp(<AiGeneratePanel assignmentId={3} hasStatement onFinished={onFinished} interval={20} />, {
    user: TEACHER,
  });

  const button = screen.getByRole("button", { name: "Generate tests with AI" });
  expect(button).toBeDisabled(); // no reference solution yet
  await user.selectOptions(screen.getByLabelText("Number of tests to generate"), "10");
  await user.type(screen.getByLabelText("Your reference solution"), "print(10)");
  await user.click(button);

  expect(await screen.findByText("Proposing test inputs…")).toBeInTheDocument();
  expect(await screen.findByText(/7 tests ready for review \(1 dropped/)).toBeInTheDocument();
  expect(onFinished).toHaveBeenCalledTimes(1);
  const post = calls.find((call) => call.method === "POST");
  expect(JSON.parse(post.body)).toEqual({ count: 10, reference_solution: "print(10)" });
});

test("the button waits for a task statement", () => {
  renderApp(<AiGeneratePanel assignmentId={3} hasStatement={false} />, { user: TEACHER });

  expect(screen.getByRole("button", { name: "Generate tests with AI" })).toBeDisabled();
  expect(screen.getByText(/Save a task statement first/)).toBeInTheDocument();
});

test("a failed job shows its reason", async () => {
  mockApi({
    "POST /assignments/3/generate-tests": [202, { job_id: 4 }],
    "GET /generation-jobs/4": job({ status: "error", phase: "error", error_message: "The reference solution is not deterministic" }),
  });
  const user = userEvent.setup();
  renderApp(<AiGeneratePanel assignmentId={3} hasStatement interval={20} />, { user: TEACHER });

  await user.type(screen.getByLabelText("Your reference solution"), "import random");
  await user.click(screen.getByRole("button", { name: "Generate tests with AI" }));

  expect(await screen.findByRole("alert")).toHaveTextContent("not deterministic");
});

test("drafts can be approved one by one or all at once, and show the reference solution", async () => {
  const { calls } = mockApi({
    "POST /test-cases/7/approve": draft(7, { review_status: "approved" }),
    "POST /assignments/3/tests/approve-all": { approved: 2 },
    "GET /generation-jobs/4": job({ status: "done", phase: "done", reference_code: "print(10)" }),
  });
  const onChanged = vi.fn();
  const user = userEvent.setup();
  renderApp(
    <DraftsPanel
      assignmentId={3}
      drafts={[
        draft(7, {
          materials: [
            { material_id: 5, title: "Lecture 4", category: "lecture", file_type: "pdf", page_count: 28, pages: "12-15", first_page: 12 },
          ],
        }),
        draft(8, { concepts: [] }),
      ]}
      onChanged={onChanged}
    />,
    { user: TEACHER },
  );

  expect(screen.getByText("2 drafts left. Drafts do not count and students do not see them.")).toBeInTheDocument();
  const first = screen.getByRole("listitem", { name: "Draft 1: Draft 7" });
  expect(within(first).getByText("checks a plain number")).toBeInTheDocument();
  expect(within(first).getByRole("link", { name: /Lecture 4/ })).toHaveAttribute(
    "href",
    "/learn/materials/5?page=12&rec=12-15",
  );
  expect(within(screen.getByRole("listitem", { name: "Draft 2: Draft 8" })).getByText("no concept")).toBeInTheDocument();
  expect(await screen.findByText(/Reference solution used/)).toBeInTheDocument();

  await user.click(within(first).getByRole("button", { name: "Approve" }));
  await user.click(screen.getByRole("button", { name: "Approve all" }));

  await waitFor(() => expect(onChanged).toHaveBeenCalledTimes(2));
  expect(calls.filter((call) => call.method === "POST").map((call) => call.path)).toEqual([
    "/test-cases/7/approve",
    "/assignments/3/tests/approve-all",
  ]);
});

test("the editor keeps drafts out of the form, so saving never deletes them", async () => {
  const assignment = {
    id: 3,
    course_id: 1,
    course_title: "Procedural Programming",
    title: "Digit sum",
    description: "Sum the digits.",
    due_at: null,
    time_limit_ms: 2000,
    memory_limit_mb: 128,
    max_submissions: 10,
    is_published: false,
    status: "draft",
    test_count: 1,
    hidden_test_count: 0,
    draft_test_count: 1,
  };
  const manual = draft(1, { name: "Manual", source: "manual", review_status: "approved" });
  const { calls } = mockApi({
    "GET /assignments/3": assignment,
    "GET /assignments/3/test-cases": [manual, draft(2, { name: "AI one" })],
    "GET /courses/1/concepts": [{ id: 1, name: "Loops" }],
    "GET /config": { ai_available: true },
    "GET /generation-jobs/4": job({ status: "done", phase: "done" }),
    "PATCH /assignments/3": assignment,
    "PATCH /test-cases/1": manual,
  });
  const user = userEvent.setup();
  renderApp(
    <Routes>
      <Route path="/teacher/assignments/:assignmentId/edit" element={<AssignmentEditor />} />
    </Routes>,
    { route: "/teacher/assignments/3/edit", user: TEACHER },
  );

  expect(await screen.findByText("1 AI tests still need review")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Generate tests with AI" })).toBeDisabled();
  await user.type(screen.getByLabelText("Your reference solution"), "print(1)");
  expect(screen.getByRole("button", { name: "Generate tests with AI" })).toBeEnabled();
  expect(screen.getByDisplayValue("Manual")).toBeInTheDocument();
  expect(screen.queryByDisplayValue("AI one")).not.toBeInTheDocument(); // not a form row

  await user.click(screen.getByRole("button", { name: "Save draft" }));

  await waitFor(() => expect(calls.some((call) => call.method === "PATCH" && call.path === "/test-cases/1")).toBe(true));
  expect(calls.some((call) => call.method === "DELETE")).toBe(false);
});
