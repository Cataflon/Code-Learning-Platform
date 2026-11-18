import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route, Routes, useLocation } from "react-router-dom";
import { expect, test, vi } from "vitest";

import { mockApi, renderApp, STUDENT } from "../test/utils.jsx";
import MaterialViewer from "./MaterialViewer.jsx";

// pdf.js needs a real browser; the test only checks which page is asked for.
vi.mock("../components/PdfSheet.jsx", () => ({
  default: ({ page }) => <p>Showing page {page}</p>,
}));

const MATERIAL = {
  id: 7,
  course_id: 1,
  title: "Lecture 4: Loops",
  category: "lecture",
  file_type: "pdf",
  original_filename: "lecture-04.pdf",
  size_bytes: 2_100_000,
  page_count: 28,
  created_at: new Date().toISOString(),
  used_in: [{ assignment_id: 3, assignment_title: "Digit sum", for_assignment: true, test_count: 1 }],
};

function Address() {
  const location = useLocation();
  return <output aria-label="address">{location.pathname + location.search}</output>;
}

function setup(route) {
  mockApi({
    "GET /materials/7": MATERIAL,
    "GET /courses/1": { id: 1, title: "Procedural Programming", color: "indigo", teacher_name: "Dr. Maria Ionescu" },
    "GET /materials/7/preview": () => ({ ok: true, status: 200, blob: async () => new Blob(["%PDF-"]) }),
  });
  vi.spyOn(globalThis, "fetch").mockImplementation(async (url) => {
    const path = String(url).replace("/api/v1", "");
    if (path === "/materials/7/preview") return { ok: true, status: 200, blob: async () => new Blob(["%PDF-"]) };
    if (path === "/materials/7") return { ok: true, status: 200, json: async () => MATERIAL };
    return {
      ok: true,
      status: 200,
      json: async () => ({ id: 1, title: "Procedural Programming", color: "indigo", teacher_name: "Dr. Maria Ionescu" }),
    };
  });
  return renderApp(
    <Routes>
      <Route
        path="/learn/materials/:materialId"
        element={
          <>
            <MaterialViewer />
            <Address />
          </>
        }
      />
    </Routes>,
    { route, user: STUDENT },
  );
}

test("opens at the page in the address and highlights the recommended pages", async () => {
  setup("/learn/materials/7?page=12&rec=12-15&from=Digit%20sum");

  expect(await screen.findByText("Showing page 12")).toBeInTheDocument();
  expect(screen.getByText("Recommended pages 12-15")).toBeInTheDocument();
  expect(screen.getByText("Opened from your Digit sum result")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Page 14, recommended" })).toHaveClass("rec");
  expect(screen.getByRole("button", { name: "Page 12, recommended" })).toHaveAttribute("aria-current", "page");
  expect(screen.getByRole("button", { name: "Page 16" })).not.toHaveClass("rec");
  expect(screen.getByText("Digit sum")).toBeInTheDocument(); // "Used in"
});

test("arrows and page buttons move through the file and update the address", async () => {
  const user = userEvent.setup();
  setup("/learn/materials/7?page=12");
  await screen.findByText("Showing page 12");

  await user.click(screen.getByRole("button", { name: "Next page" }));
  expect(await screen.findByText("Showing page 13")).toBeInTheDocument();

  await user.keyboard("{ArrowLeft}{ArrowLeft}");
  expect(await screen.findByText("Showing page 11")).toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "Page 28" }));
  expect(await screen.findByText("Showing page 28")).toBeInTheDocument();
  expect(screen.getByLabelText("address")).toHaveTextContent("page=28");
  expect(screen.getByRole("button", { name: "Next page" })).toBeDisabled();
});

test("a page number outside the file is clamped", async () => {
  setup("/learn/materials/7?page=99");

  expect(await screen.findByText("Showing page 28")).toBeInTheDocument();
});
