import { render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import StatusPage from "./StatusPage.jsx";

test("shows that the server is up when /health answers ok", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue({
    ok: true,
    json: async () => ({ status: "ok" }),
  });

  render(<StatusPage />);

  expect(await screen.findByText("Server is up")).toBeInTheDocument();
  expect(globalThis.fetch).toHaveBeenCalledWith("/health");
});

test("shows that the server is unreachable when the request fails", async () => {
  vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("network"));

  render(<StatusPage />);

  expect(await screen.findByText("Server is unreachable")).toBeInTheDocument();
});
