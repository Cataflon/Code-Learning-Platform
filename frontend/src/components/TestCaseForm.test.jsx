import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { expect, test, vi } from "vitest";

import { testPayload } from "../pages/teacher/AssignmentEditor.jsx";
import TestCaseForm, { toRow } from "./TestCaseForm.jsx";

const CONCEPTS = [
  { id: 1, name: "Loops" },
  { id: 2, name: "Edge cases" },
];

const SERVER_TEST = {
  id: 7,
  name: "Simple case",
  input_data: "1234\n",
  expected_output: "10\n",
  is_hidden: false,
  weight: 3,
  hint: null,
  concepts: [{ id: 1, name: "Loops" }],
};

/** Holds the rows like the editor page does and exposes the latest value. */
function Harness({ initial, onRows, onCreateConcept = vi.fn() }) {
  const [tests, setTests] = useState(initial);
  onRows(tests);
  return <TestCaseForm tests={tests} onChange={setTests} concepts={CONCEPTS} onCreateConcept={onCreateConcept} />;
}

function setup(initial = [toRow(SERVER_TEST)], extra = {}) {
  let rows = initial;
  render(<Harness initial={initial} onRows={(value) => (rows = value)} {...extra} />);
  return { user: userEvent.setup(), getRows: () => rows };
}

test("adds a row and sends the right structure", async () => {
  const { user, getRows } = setup();

  await user.click(screen.getByRole("button", { name: /Add a test/ }));
  const second = screen.getByRole("region", { name: "Test 2" });
  await user.type(within(second).getByLabelText("Name of test 2"), "Zero");
  await user.type(within(second).getByLabelText("Input"), "0");
  await user.type(within(second).getByLabelText("Expected output"), "0");
  await user.click(within(second).getByRole("switch", { name: "Hide test 2" }));
  await user.type(within(second).getByLabelText(/Hint for students/), "Think about zero.");

  const rows = getRows();
  expect(rows).toHaveLength(2);
  expect(rows[1].id).toBeUndefined(); // new rows have no server id yet
  expect(testPayload(rows[1], 1)).toEqual({
    name: "Zero",
    input_data: "0",
    expected_output: "0",
    is_hidden: true,
    weight: 1,
    position: 1,
    hint: "Think about zero.",
    concept_ids: [],
  });
  // The existing row is untouched and keeps its id and concepts.
  expect(rows[0].id).toBe(7);
  expect(testPayload(rows[0], 0).concept_ids).toEqual([1]);
});

test("removes a row", async () => {
  const { user, getRows } = setup([toRow(SERVER_TEST), toRow({ ...SERVER_TEST, id: 8, name: "Second" })]);

  await user.click(screen.getByRole("button", { name: "Remove test 1" }));

  expect(getRows().map((row) => row.id)).toEqual([8]);
  expect(screen.queryByDisplayValue("Simple case")).not.toBeInTheDocument();
  expect(screen.getByDisplayValue("Second")).toBeInTheDocument();
});

test("total weight follows the rows", async () => {
  const { user } = setup();
  expect(screen.getByText("3", { selector: "strong" })).toBeInTheDocument();

  const weight = screen.getByLabelText("Weight of test 1");
  await user.clear(weight);
  await user.type(weight, "5");
  await user.click(screen.getByRole("button", { name: /Add a test/ }));

  expect(screen.getByText("6", { selector: "strong" })).toBeInTheDocument();
});

test("adds and removes concepts on a test", async () => {
  const { user, getRows } = setup();
  const first = screen.getByRole("region", { name: "Test 1" });

  await user.click(within(first).getByRole("button", { name: "Add concept" }));
  await user.click(within(first).getByRole("button", { name: "+ Edge cases" }));
  expect(getRows()[0].concept_ids).toEqual([1, 2]);

  await user.click(within(first).getByRole("button", { name: "Remove concept Loops" }));
  expect(getRows()[0].concept_ids).toEqual([2]);
});

test("creates a new concept and attaches it", async () => {
  const onCreateConcept = vi.fn().mockResolvedValue({ id: 9, name: "Recursion" });
  const { user, getRows } = setup([toRow(SERVER_TEST)], { onCreateConcept });
  const first = screen.getByRole("region", { name: "Test 1" });

  await user.click(within(first).getByRole("button", { name: "Add concept" }));
  await user.type(within(first).getByLabelText("New concept name"), "Recursion");
  await user.click(within(first).getByRole("button", { name: "Create" }));

  expect(onCreateConcept).toHaveBeenCalledWith("Recursion");
  expect(getRows()[0].concept_ids).toEqual([1, 9]);
});

test("shows the empty state without tests", () => {
  setup([]);

  expect(screen.getByText(/No tests yet/)).toBeInTheDocument();
});
