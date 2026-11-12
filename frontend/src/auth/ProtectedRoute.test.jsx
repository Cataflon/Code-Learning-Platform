import { screen } from "@testing-library/react";
import { Route, Routes } from "react-router-dom";
import { expect, test } from "vitest";

import { renderApp, STUDENT, TEACHER } from "../test/utils.jsx";
import ProtectedRoute from "./ProtectedRoute.jsx";

function Tree() {
  return (
    <Routes>
      <Route path="/login" element={<p>Login page</p>} />
      <Route path="/dashboard" element={<p>Student home</p>} />
      <Route path="/courses" element={<p>Teacher home</p>} />
      <Route element={<ProtectedRoute roles={["teacher"]} />}>
        <Route path="/teacher-only" element={<p>Secret teacher page</p>} />
      </Route>
    </Routes>
  );
}

test("redirects an anonymous visitor to the login page", () => {
  renderApp(<Tree />, { route: "/teacher-only", user: null });

  expect(screen.getByText("Login page")).toBeInTheDocument();
  expect(screen.queryByText("Secret teacher page")).not.toBeInTheDocument();
});

test("lets the right role through", () => {
  renderApp(<Tree />, { route: "/teacher-only", user: TEACHER });

  expect(screen.getByText("Secret teacher page")).toBeInTheDocument();
});

test("sends the wrong role to its own home page", () => {
  renderApp(<Tree />, { route: "/teacher-only", user: STUDENT });

  expect(screen.getByText("Student home")).toBeInTheDocument();
});

test("waits while the stored token is being checked", () => {
  renderApp(<Tree />, { route: "/teacher-only", user: null, status: "loading" });

  expect(screen.getByRole("status")).toHaveTextContent("Signing you in");
});
