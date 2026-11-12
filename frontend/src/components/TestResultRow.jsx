import { Check, Clock, Loader2, X } from "lucide-react";

import { Chip } from "./ui.jsx";

const FAILURE_TEXT = {
  wrong_answer: "Your output differs from the expected one.",
  time_limit: "Your program ran longer than the time limit.",
  memory_limit: "Your program used more memory than allowed.",
  runtime_error: "Your program stopped with an error.",
  internal_error: "This test could not be run. Try submitting again.",
};

function Block({ label, text }) {
  return (
    <div className="min-w-0 rounded-lg border border-line bg-raised px-3 py-2">
      <div className="text-xs text-muted">{label}</div>
      <pre className="mt-1 max-h-40 overflow-auto whitespace-pre-wrap break-words font-mono text-sm">
        {text === "" ? "(empty)" : text}
      </pre>
    </div>
  );
}

/**
 * One test of a submission: verdict chip, name, concept chips and runtime.
 * `running` marks the test that is being executed right now.
 */
export default function TestResultRow({ result, running = false }) {
  const { verdict } = result;
  const passed = verdict === "passed";
  const failed = verdict != null && !passed;

  let badge;
  if (passed) badge = <Chip tone="pass" icon={Check}>Passed</Chip>;
  else if (failed) badge = <Chip tone="fail" icon={X}>Failed</Chip>;
  else if (running) badge = <Chip tone="info" icon={Loader2} className="[&>svg]:animate-spin">Running</Chip>;
  else badge = <Chip tone="neutral" icon={Clock}>Waiting</Chip>;

  // Content of public tests only; for hidden tests the API sends nothing to show.
  const hasDetails = failed && result.expected_output != null;

  return (
    <li className={`border-t border-line px-7 py-4 ${failed ? "bg-fail-tint/70" : ""}`}>
      <div className="flex flex-wrap items-center gap-3">
        {badge}
        <span className="font-semibold">{result.name}</span>
        {result.is_hidden && <Chip tone="neutral">hidden</Chip>}
        <span className="ml-auto flex flex-wrap items-center gap-2">
          {result.concepts.map((concept) => (
            <Chip key={concept}>{concept}</Chip>
          ))}
          <span className="w-16 text-right text-sm text-muted">
            {result.runtime_ms != null ? `${result.runtime_ms} ms` : ""}
          </span>
        </span>
      </div>
      {failed && (
        <p className="mt-3 text-sm text-fail">
          {FAILURE_TEXT[verdict] ?? "This test failed."}
          {result.hint && <> Hint from your teacher: {result.hint}</>}
        </p>
      )}
      {hasDetails && (
        <div className="mt-3 grid gap-3 md:grid-cols-3">
          <Block label="Input" text={result.input_data ?? ""} />
          <Block label="Expected output" text={result.expected_output ?? ""} />
          <Block label="Your output" text={result.actual_output ?? ""} />
        </div>
      )}
      {failed && result.stderr && (
        <div className="mt-3">
          <Block label="Error output" text={result.stderr} />
        </div>
      )}
    </li>
  );
}
