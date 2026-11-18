import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { expect, test } from "vitest";

import MaterialPicker, { linksAreValid } from "./MaterialPicker.jsx";

const MATERIALS = [
  { id: 1, title: "Lecture 4", file_type: "pdf", page_count: 28 },
  { id: 2, title: "Lab 3", file_type: "pptx", page_count: 16 },
];

function Harness({ initial = [], onLinks }) {
  const [links, setLinks] = useState(initial);
  onLinks?.(links);
  return <MaterialPicker links={links} onChange={setLinks} materials={MATERIALS} />;
}

test("adds a material, edits its pages and removes it", async () => {
  let current = [];
  const user = userEvent.setup();
  render(<Harness onLinks={(links) => (current = links)} />);

  await user.selectOptions(screen.getByLabelText("Add a material from this course"), "1");
  await user.click(screen.getByRole("button", { name: /Add/ }));
  await user.type(screen.getByLabelText("Pages (empty = all)"), "12-15, 18");

  expect(current).toEqual([{ material_id: 1, pages: "12-15, 18" }]);
  expect(screen.queryByRole("option", { name: "Lecture 4" })).not.toBeInTheDocument(); // not twice

  await user.click(screen.getByRole("button", { name: "Remove Lecture 4" }));
  expect(current).toEqual([]);
});

test("shows the format error under an invalid pages field", async () => {
  const user = userEvent.setup();
  render(<Harness initial={[{ material_id: 2, pages: "" }]} />);

  await user.type(screen.getByLabelText("Pages (empty = all)"), "20");

  expect(screen.getByText("The material has 16 pages")).toBeInTheDocument();
  expect(screen.getByLabelText("Pages (empty = all)")).toHaveAttribute("aria-invalid", "true");
});

test("linksAreValid checks every list", () => {
  expect(linksAreValid([[{ material_id: 1, pages: "12-15" }], []], MATERIALS)).toBe(true);
  expect(linksAreValid([[{ material_id: 1, pages: "15-12" }]], MATERIALS)).toBe(false);
});
