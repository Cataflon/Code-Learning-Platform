import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route, Routes } from "react-router-dom";
import { expect, test, vi } from "vitest";

import { mockApi, renderApp, TEACHER } from "../../test/utils.jsx";
import MaterialsPage from "./MaterialsPage.jsx";

const COURSE = { id: 1, title: "Procedural Programming", color: "indigo", teacher_name: "Dr. Maria Ionescu", join_code: "PP4K7MAB" };
const MATERIAL = {
  id: 5,
  course_id: 1,
  title: "Lecture 4",
  category: "lecture",
  file_type: "pdf",
  original_filename: "lecture-04.pdf",
  size_bytes: 2_100_000,
  page_count: 28,
  created_at: new Date().toISOString(),
  used_in: [{ assignment_id: 3, assignment_title: "Digit sum", for_assignment: false, test_count: 1 }],
};

function renderPage() {
  return renderApp(
    <Routes>
      <Route path="/courses/:courseId/materials" element={<MaterialsPage />} />
    </Routes>,
    { route: "/courses/1/materials", user: TEACHER },
  );
}

test("lists materials with where they are used", async () => {
  mockApi({ "GET /courses/1": COURSE, "GET /courses/1/materials": [MATERIAL] });

  renderPage();

  expect(await screen.findByText("Lecture 4")).toBeInTheDocument();
  expect(screen.getByText("Digit sum · 1 test")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Materials" })).toHaveAttribute("aria-current", "page");
});

test("uploads a file as multipart with the title taken from its name", async () => {
  const { calls } = mockApi({
    "GET /courses/1": COURSE,
    "GET /courses/1/materials": [],
    "POST /courses/1/materials": [201, MATERIAL],
  });
  const user = userEvent.setup();
  renderPage();
  await screen.findByText("No materials yet");

  const file = new File(["%PDF-1.7"], "lecture-05-functions.pdf", { type: "application/pdf" });
  await user.upload(screen.getByLabelText("Material file"), file);
  expect(screen.getByLabelText("Title")).toHaveValue("lecture 05 functions");
  await user.selectOptions(screen.getByLabelText("Category"), "lab");
  await user.click(screen.getByRole("button", { name: "Upload" }));

  expect(await screen.findByText("Uploaded.")).toBeInTheDocument();
  const post = calls.find((call) => call.method === "POST");
  expect(post.body).toBeInstanceOf(FormData);
  expect(post.body.get("category")).toBe("lab");
  expect(post.body.get("file").name).toBe("lecture-05-functions.pdf");
});

test("shows the server's reason when a file is refused", async () => {
  mockApi({
    "GET /courses/1": COURSE,
    "GET /courses/1/materials": [],
    "POST /courses/1/materials": [415, { detail: "Only PDF and PPTX files are accepted", code: "unsupported_media_type" }],
  });
  const user = userEvent.setup();
  renderPage();
  await screen.findByText("No materials yet");

  await user.upload(screen.getByLabelText("Material file"), new File(["hi"], "notes.pdf"));
  await user.click(screen.getByRole("button", { name: "Upload" }));

  expect(await screen.findByRole("alert")).toHaveTextContent("Only PDF and PPTX files are accepted");
});

test("deleting asks for confirmation first", async () => {
  const { calls } = mockApi({
    "GET /courses/1": COURSE,
    "GET /courses/1/materials": [MATERIAL],
    "DELETE /materials/5": [204, null],
  });
  const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
  const user = userEvent.setup();
  renderPage();

  await user.click(await screen.findByRole("button", { name: "Delete Lecture 4" }));

  expect(confirm).toHaveBeenCalledWith(expect.stringContaining("linked to 1 assignment"));
  expect(calls.some((call) => call.method === "DELETE")).toBe(false);
});
