import { expect, test } from "vitest";

import { formatDay, formatSeconds, ordinal, plural, timeAgo } from "./format.js";

const NOW = new Date(2026, 9, 11, 15, 0, 0); // Sunday, October 11, 2026, 15:00 local time

test("formatDay names nearby days and falls back to the date", () => {
  expect(formatDay(new Date(2026, 9, 11, 14, 22), NOW)).toBe("today, 14:22");
  expect(formatDay(new Date(2026, 9, 12, 23, 59), NOW)).toBe("tomorrow, 23:59");
  expect(formatDay(new Date(2026, 9, 10, 20, 41), NOW)).toBe("yesterday, 20:41");
  expect(formatDay(new Date(2026, 9, 16, 23, 59), NOW)).toBe("Friday, 23:59");
  expect(formatDay(new Date(2026, 9, 4, 23, 59), NOW)).toBe("October 4, 23:59");
});

test("timeAgo picks a readable unit", () => {
  const ago = (ms) => timeAgo(new Date(NOW - ms), NOW);
  expect(ago(3_000)).toBe("just now");
  expect(ago(30_000)).toBe("30 s ago");
  expect(ago(2 * 60_000)).toBe("2 minutes ago");
  expect(ago(60 * 60_000)).toBe("1 hour ago");
  expect(ago(2 * 24 * 3600_000)).toBe("2 days ago");
  expect(ago(7 * 24 * 3600_000)).toBe("last week");
  expect(ago(21 * 24 * 3600_000)).toBe("3 weeks ago");
});

test("small helpers", () => {
  expect(ordinal(4)).toBe("fourth");
  expect(ordinal(22)).toBe("22nd");
  expect(plural(1, "test")).toBe("1 test");
  expect(plural(3, "test")).toBe("3 tests");
  expect(formatSeconds(2000)).toBe("2 s");
  expect(formatSeconds(1500)).toBe("1.5 s");
});
