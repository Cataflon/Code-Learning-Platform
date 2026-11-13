// The row of pixel squares, one per test: green passed, red failed, empty not run,
// blinking violet running. Colour is never the only signal: every square has a title and
// the row has a text label.

export function verdictClass(verdict) {
  if (verdict == null) return "";
  if (verdict === "passed") return "ok";
  if (verdict === "running") return "run";
  return "bad"; // every failing verdict is red
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
 * `total` pads the row with empty squares for tests without a verdict yet.
 * `large` draws the big 32 px squares used on the dashboard's main card.
 */
export default function VerdictSquares({ verdicts = [], total, large = false }) {
  const count = Math.max(total ?? 0, verdicts.length);
  const cells = Array.from({ length: count }, (_, index) => verdicts[index] ?? null);
  const passed = cells.filter((verdict) => verdict === "passed").length;

  return (
    <span className={`sqs ${large ? "lg" : ""}`} role="img" aria-label={`${passed} of ${count} tests passed`}>
      {cells.map((verdict, index) => (
        <i
          key={index}
          title={`Test ${index + 1}: ${verdictLabel(verdict)}`}
          className={`sq ${verdictClass(verdict)}`}
        />
      ))}
    </span>
  );
}
