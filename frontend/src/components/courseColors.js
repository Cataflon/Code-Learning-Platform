// Course.color is one name from a fixed palette; this is the only place that maps it to classes.

export const COURSE_COLORS = ["indigo", "blue", "purple", "green", "amber", "rose"];

const BAR = {
  indigo: "bg-accent",
  blue: "bg-blue",
  purple: "bg-pink",
  green: "bg-ok",
  amber: "bg-warn",
  rose: "bg-bad",
};

export function courseBarClass(color) {
  return BAR[color] ?? BAR.indigo;
}

// The same palette as CSS colours, for the dots and row accents of the 8-bit prototype.
const VAR = {
  indigo: "var(--course-violet)",
  blue: "var(--course-blue)",
  purple: "var(--course-lilac)",
  green: "var(--ok)",
  amber: "var(--warn)",
  rose: "var(--bad)",
};

export function courseColorVar(color) {
  return VAR[color] ?? VAR.indigo;
}
