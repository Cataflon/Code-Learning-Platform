// One test of a submission, laid out as in the 8-bit prototype: a square, the name and its
// concept, the verdict and the time. A failed test explains what went wrong underneath and, when
// the course has one, links the page to read.

import { Link } from "react-router-dom";

import { Chip } from "./ui.jsx";
import { verdictClass, verdictLabel } from "./VerdictSquares.jsx";

const FAILURE_TEXT = {
  wrong_answer: "Your output differs from the expected one.",
  time_limit: "Your program ran longer than the time limit.",
  memory_limit: "Your program used more memory than allowed.",
  runtime_error: "Your program stopped with an error.",
  internal_error: "This test could not be run. Try submitting again.",
};

function Block({ label, text }) {
  return (
    <div className="io" style={{ gridTemplateColumns: "minmax(0, 1fr)" }}>
      <div>
        <span>{label}</span>
        <pre className="max-h-40 overflow-auto">{text === "" ? "(empty)" : text}</pre>
      </div>
    </div>
  );
}

/**
 * `running` marks the test that is being executed right now; `material` is the page to read
 * when this test failed ({ to, label }), from the recommendations of the submission.
 */
export default function TestResultRow({ result, running = false, material = null }) {
  const { verdict } = result;
  const passed = verdict === "passed";
  const failed = verdict != null && !passed;

  let chip;
  if (passed) chip = <Chip tone="pass">Passed</Chip>;
  else if (failed) chip = <Chip tone="fail">{verdictLabel(verdict)}</Chip>;
  else if (running) chip = <Chip tone="info">Running</Chip>;
  else chip = <Chip tone="neutral">Waiting</Chip>;

  // Content of public tests only; for hidden tests the API sends nothing to show.
  const hasDetails = failed && result.expected_output != null;

  return (
    <li className={`test ${failed ? "bg-bad/10" : ""}`}>
      <i className={`sq ${running ? "run" : verdictClass(verdict)}`} aria-hidden="true" />
      <span className="min-w-0">
        <b>{result.name}</b>
        {result.concepts.length > 0 && <span className="concept"> {result.concepts.join(", ")}</span>}
      </span>
      {chip}
      <span className="ms">{result.runtime_ms != null ? `${result.runtime_ms} ms` : ""}</span>
      {failed && (
        <div className="hint">
          <p>
            {FAILURE_TEXT[verdict] ?? "This test failed."}
            {result.hint && <> Hint from your teacher: {result.hint}</>}
          </p>
          {hasDetails && (
            <div className="out-grid">
              <Block label="Input" text={result.input_data ?? ""} />
              <Block label="Expected output" text={result.expected_output ?? ""} />
              <Block label="Your output" text={result.actual_output ?? ""} />
            </div>
          )}
          {result.stderr && <Block label="Error output" text={result.stderr} />}
          {material && (
            <Link to={material.to} className="warn-link justify-self-start">
              {material.label}
            </Link>
          )}
        </div>
      )}
    </li>
  );
}
