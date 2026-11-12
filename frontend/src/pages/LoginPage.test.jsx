import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route, Routes } from "react-router-dom";
import { expect, test, vi } from "vitest";

import { ApiError } from "../api/client.js";
import { renderApp, STUDENT } from "../test/utils.jsx";
import LoginPage from "./LoginPage.jsx";

function Tree() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/dashboard" element={<p>Student home</p>} />
    </Routes>
  );
}

async function fillAndSubmit() {
  const user = userEvent.setup();
  await user.type(screen.getByLabelText("Email"), "andrei@example.com");
  await user.type(screen.getByLabelText("Password"), "parola123");
  await user.click(screen.getByRole("button", { name: "Sign in" }));
}

test("shows the server error when sign-in fails", async () => {
  const login = vi.fn().mockRejectedValue(new ApiError(401, "Incorrect email or password"));
  renderApp(<Tree />, { route: "/login", auth: { login } });

  await fillAndSubmit();

  expect(await screen.findByRole("alert")).toHaveTextContent("Incorrect email or password");
  expect(login).toHaveBeenCalledWith("andrei@example.com", "parola123");
});

test("goes to the role home page after a successful sign-in", async () => {
  const login = vi.fn().mockResolvedValue(STUDENT);
  renderApp(<Tree />, { route: "/login", auth: { login } });

  await fillAndSubmit();

  expect(await screen.findByText("Student home")).toBeInTheDocument();
});

test("the submit button stays disabled until both fields are filled", () => {
  renderApp(<Tree />, { route: "/login" });

  expect(screen.getByRole("button", { name: "Sign in" })).toBeDisabled();
});
