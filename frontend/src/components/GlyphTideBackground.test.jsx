import { render } from "@testing-library/react";
import { expect, test } from "vitest";

import GlyphTideBackground from "./GlyphTideBackground.jsx";

test("renders a decorative canvas even where canvas and matchMedia are missing", () => {
  const saved = window.matchMedia;
  window.matchMedia = undefined;
  try {
    const { container } = render(<GlyphTideBackground />);

    const canvas = container.querySelector("canvas");
    expect(canvas).toHaveAttribute("aria-hidden", "true");
    expect(canvas.style.pointerEvents).toBe("none");
  } finally {
    window.matchMedia = saved;
  }
});
