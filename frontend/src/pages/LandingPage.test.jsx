import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test } from "vitest";

import { AppRoutes } from "../App.jsx";
import { renderApp, STUDENT, TEACHER } from "../test/utils.jsx";

test("visitors see the landing page with its sections and calls to action", () => {
  renderApp(<AppRoutes />);

  expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("From task to verdict.");
  for (const name of ["Features", "How it works", "Students & teachers", "Sandbox"]) {
    expect(screen.getByRole("navigation", { name: "Sections" })).toHaveTextContent(name);
  }
  for (const link of screen.getAllByRole("link", { name: /Create a free account/ })) {
    expect(link).toHaveAttribute("href", "/register");
  }
  expect(screen.getAllByRole("link", { name: "Sign in" })[0]).toHaveAttribute("href", "/login");
  expect(screen.getByText("AI drafts the tests. The sandbox decides the answers.")).toBeInTheDocument();
  expect(screen.getByRole("img", { name: "3 of 4 tests passed" })).toBeInTheDocument();
});

test("the role tabs switch with a click and with the arrow keys", async () => {
  const user = userEvent.setup();
  renderApp(<AppRoutes />);

  const students = screen.getByRole("tab", { name: "For students" });
  const teachers = screen.getByRole("tab", { name: "For teachers" });
  expect(students).toHaveAttribute("aria-selected", "true");
  expect(screen.getByRole("tabpanel")).toHaveTextContent("Where you go wrong");

  await user.click(teachers);
  expect(teachers).toHaveAttribute("aria-selected", "true");
  expect(screen.getByRole("tabpanel")).toHaveTextContent("AI drafts");

  await user.keyboard("{ArrowRight}");
  expect(students).toHaveAttribute("aria-selected", "true");
  expect(students).toHaveFocus();
});

test("signed-in users go straight to their home page", () => {
  const { unmount } = renderApp(<AppRoutes />, { user: STUDENT });
  expect(screen.queryByText(/From task to verdict/)).not.toBeInTheDocument();
  unmount();

  renderApp(<AppRoutes />, { user: TEACHER, status: "loading" });
  expect(screen.getByText("Signing you in…")).toBeInTheDocument();
});
