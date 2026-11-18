import { screen, within } from "@testing-library/react";
import { Route, Routes } from "react-router-dom";
import { expect, test } from "vitest";

import { mockApi, renderApp, TEACHER } from "../../test/utils.jsx";
import ClassConceptReport from "./ClassConceptReport.jsx";

function renderPage() {
  return renderApp(
    <Routes>
      <Route path="/courses/:courseId/report" element={<ClassConceptReport />} />
    </Routes>,
    { route: "/courses/1/report", user: TEACHER },
  );
}

test("shows the class average and how many students should review each concept", async () => {
  mockApi({
    "GET /courses/1/reports/concepts": {
      course_id: 1,
      course_title: "Procedural Programming",
      students: 4,
      students_with_data: 3,
      thresholds: { review_below: 0.5, mastered_from: 0.8 },
      concepts: [
        {
          concept_id: 1,
          concept: "Negative numbers",
          average_pass_rate: 0.38,
          level: "review",
          students_with_data: 3,
          students_in_review: 2,
          students_mastered: 1,
        },
        {
          concept_id: 2,
          concept: "Loops",
          average_pass_rate: 0.9,
          level: "mastered",
          students_with_data: 3,
          students_in_review: 0,
          students_mastered: 3,
        },
      ],
    },
  });

  renderPage();

  const table = await screen.findByRole("table");
  const rows = within(table).getAllByRole("row");
  expect(within(rows[1]).getByText("Negative numbers")).toBeInTheDocument();
  expect(within(rows[1]).getByText("38%")).toBeInTheDocument();
  expect(within(rows[1]).getByText("2")).toBeInTheDocument();
  expect(within(rows[1]).getAllByText("Review")).toHaveLength(2); // column chip + phone chip
  expect(within(rows[2]).getAllByText("Mastered")).toHaveLength(2); // column chip + phone chip
  expect(screen.getByRole("link", { name: "Concept report" })).toHaveAttribute("aria-current", "page");
  expect(screen.getByText(/Negative numbers 38% \(Review\)/)).toBeInTheDocument(); // chart text twin
});

test("shows an empty state before anyone has results", async () => {
  mockApi({
    "GET /courses/1/reports/concepts": {
      course_id: 1,
      course_title: "Procedural Programming",
      students: 4,
      students_with_data: 0,
      thresholds: { review_below: 0.5, mastered_from: 0.8 },
      concepts: [],
    },
  });

  renderPage();

  expect(await screen.findByText("No results yet")).toBeInTheDocument();
});
