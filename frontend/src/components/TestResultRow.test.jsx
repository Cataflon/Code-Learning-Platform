import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";

import TestResultRow from "./TestResultRow.jsx";

const BASE = {
  test_case_id: 1,
  name: "Simple case",
  position: 0,
  is_hidden: false,
  verdict: "passed",
  runtime_ms: 31,
  concepts: ["Loops"],
  hint: null,
  input_data: "1234\n",
  expected_output: "10\n",
  actual_output: "10\n",
  stderr: "",
};

function renderRow(overrides = {}, props = {}) {
  return render(
    <ul>
      <TestResultRow result={{ ...BASE, ...overrides }} {...props} />
    </ul>,
  );
}

test("a passed test shows the verdict, the concept and the runtime", () => {
  renderRow();

  expect(screen.getByText("Passed")).toBeInTheDocument();
  expect(screen.getByText("Simple case")).toBeInTheDocument();
  expect(screen.getByText("Loops")).toBeInTheDocument();
  expect(screen.getByText("31 ms")).toBeInTheDocument();
  expect(screen.queryByText(/Hint from your teacher/)).not.toBeInTheDocument();
});

test("a failed public test shows the reason and the outputs", () => {
  renderRow({ verdict: "wrong_answer", actual_output: "11\n" });

  expect(screen.getByText("Failed")).toBeInTheDocument();
  expect(screen.getByText(/Your output differs from the expected one/)).toBeInTheDocument();
  expect(screen.getByText("Expected output")).toBeInTheDocument();
  expect(screen.getByText("Your output")).toBeInTheDocument();
});

test("a failed hidden test shows the hint but no test content", () => {
  renderRow({
    name: "Hidden test #1",
    is_hidden: true,
    verdict: "wrong_answer",
    hint: "Check what happens to the sign.",
    input_data: null,
    expected_output: null,
    actual_output: null,
    stderr: null,
  });

  expect(screen.getByText("hidden")).toBeInTheDocument();
  expect(screen.getByText(/Hint from your teacher: Check what happens to the sign/)).toBeInTheDocument();
  expect(screen.queryByText("Expected output")).not.toBeInTheDocument();
});

test.each([
  ["time_limit", /longer than the time limit/],
  ["memory_limit", /more memory than allowed/],
  ["runtime_error", /stopped with an error/],
])("verdict %s has its own explanation", (verdict, text) => {
  renderRow({ verdict });

  expect(screen.getByText(text)).toBeInTheDocument();
});

test("a test without a verdict is waiting, or running when it is the current one", () => {
  const { unmount } = renderRow({ verdict: null, runtime_ms: null });
  expect(screen.getByText("Waiting")).toBeInTheDocument();
  unmount();

  renderRow({ verdict: null, runtime_ms: null }, { running: true });
  expect(screen.getByText("Running")).toBeInTheDocument();
});
