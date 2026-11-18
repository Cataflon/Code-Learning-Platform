import { expect, test } from "vitest";

import { describePages, pageSet, pagesError, parsePages } from "./pages.js";

test("parsePages follows the backend rules", () => {
  expect(parsePages("12-15, 18", 28)).toEqual([
    [12, 15],
    [18, 18],
  ]);
  expect(parsePages("", 28)).toEqual([]);
  expect(pagesError("5-3", 28)).toMatch(/backwards/);
  expect(pagesError("0", 28)).toMatch(/start at 1/);
  expect(pagesError("29", 28)).toMatch(/28 pages/);
  expect(pagesError("12,,15", 28)).toBe("Use a format like 12-15, 18");
  expect(pagesError(" 12 - 15 ", 28)).toBe("");
});

test("pageSet lists the highlighted pages and ignores bad input", () => {
  expect([...pageSet("12-14, 18", 28)]).toEqual([12, 13, 14, 18]);
  expect(pageSet("nonsense", 28).size).toBe(0);
});

test("describePages", () => {
  expect(describePages("12-15")).toBe("Pages 12-15");
  expect(describePages("4")).toBe("Page 4");
  expect(describePages("")).toBe("All pages");
  expect(describePages("", "slides")).toBe("All slides");
});
