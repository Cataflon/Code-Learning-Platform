// Course.color is one name from a fixed palette; this is the only place that maps it to classes.

export const COURSE_COLORS = ["indigo", "blue", "purple", "green", "amber", "rose"];

const BAR = {
  indigo: "bg-accent",
  blue: "bg-info",
  purple: "bg-hidden",
  green: "bg-pass",
  amber: "bg-warn",
  rose: "bg-fail",
};

export function courseBarClass(color) {
  return BAR[color] ?? BAR.indigo;
}
