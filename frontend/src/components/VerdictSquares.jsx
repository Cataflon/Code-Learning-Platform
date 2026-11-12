import { Check, X } from "lucide-react";

const COLORS = {
  passed: "bg-pass",
  running: "bg-info/60",
  pending: "bg-idle",
};

export function verdictColor(verdict) {
  if (verdict == null) return COLORS.pending;
  return COLORS[verdict] ?? "bg-fail"; // every failing verdict is red
}

export function verdictLabel(verdict) {
  return (
    {
      passed: "Passed",
      wrong_answer: "Wrong answer",
      time_limit: "Time limit exceeded",
      memory_limit: "Memory limit exceeded",
      runtime_error: "Runtime error",
      internal_error: "Internal error",
      running: "Running",
    }[verdict] ?? "Not run yet"
  );
}

/**
 * The row of colored squares, one per test, in test order.
 * `total` pads the row with empty squares for tests that have no verdict yet.
 * `large` draws the bigger squares with a check or a cross inside.
 */
export default function VerdictSquares({ verdicts = [], total, large = false }) {
  const count = Math.max(total ?? 0, verdicts.length);
  const cells = Array.from({ length: count }, (_, index) => verdicts[index] ?? null);
  const passed = cells.filter((verdict) => verdict === "passed").length;
  const size = large ? "h-9 w-9 rounded-lg" : "h-4 w-4 rounded";

  return (
    <span
      className={`inline-flex flex-wrap ${large ? "gap-2" : "gap-1.5"}`}
      role="img"
      aria-label={`${passed} of ${count} tests passed`}
    >
      {cells.map((verdict, index) => (
        <span
          key={index}
          title={`Test ${index + 1}: ${verdictLabel(verdict)}`}
          className={`flex items-center justify-center ${size} ${verdictColor(verdict)}`}
        >
          {large && verdict === "passed" && <Check className="h-4 w-4 text-pass-tint" strokeWidth={3} />}
          {large && verdict && verdict !== "passed" && verdict !== "running" && (
            <X className="h-4 w-4 text-fail-tint" strokeWidth={3} />
          )}
        </span>
      ))}
    </span>
  );
}
