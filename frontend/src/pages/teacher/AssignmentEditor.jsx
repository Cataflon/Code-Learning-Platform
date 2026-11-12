import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Pencil } from "lucide-react";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import * as assignmentsApi from "../../api/assignments.js";
import { createConcept, listConcepts } from "../../api/courses.js";
import { ErrorState, LoadingState } from "../../components/states.jsx";
import TestCaseForm, { toRow } from "../../components/TestCaseForm.jsx";
import { Button, Card, CardHeader, Chip, FormError, inputClass, PageHeader, TextField } from "../../components/ui.jsx";
import { fromLocalInput, toLocalInput } from "../../lib/format.js";

function detailsOf(assignment) {
  return {
    title: assignment.title,
    description: assignment.description,
    due_at: toLocalInput(assignment.due_at),
    seconds: assignment.time_limit_ms / 1000,
    memory_limit_mb: assignment.memory_limit_mb,
    max_submissions: assignment.max_submissions,
  };
}

/** What the form sends for one test row. */
export function testPayload(row, position) {
  return {
    name: row.name.trim(),
    input_data: row.input_data,
    expected_output: row.expected_output,
    is_hidden: row.is_hidden,
    weight: Number(row.weight) || 1,
    position,
    hint: row.hint.trim() || null,
    concept_ids: row.concept_ids,
  };
}

/**
 * Save everything: the assignment details first, then the tests.
 * Rows without an id are created, rows with an id are updated, and tests that were on the
 * server but are no longer in the form are deleted.
 */
export async function saveAssignment(assignmentId, details, tests, originalIds, extra = {}) {
  await assignmentsApi.updateAssignment(assignmentId, {
    title: details.title.trim(),
    description: details.description,
    due_at: fromLocalInput(details.due_at),
    time_limit_ms: Math.round(Number(details.seconds) * 1000),
    memory_limit_mb: Number(details.memory_limit_mb),
    max_submissions: Number(details.max_submissions),
    ...extra,
  });
  const keptIds = new Set(tests.filter((row) => row.id != null).map((row) => row.id));
  for (const id of originalIds) {
    if (!keptIds.has(id)) await assignmentsApi.deleteTestCase(id);
  }
  for (const [position, row] of tests.entries()) {
    const payload = testPayload(row, position);
    if (row.id != null) await assignmentsApi.updateTestCase(row.id, payload);
    else await assignmentsApi.createTestCase(assignmentId, payload);
  }
}

function validate(details, tests) {
  if (!details.title.trim()) return "The assignment needs a title.";
  const unnamed = tests.findIndex((row) => !row.name.trim());
  if (unnamed !== -1) return `Test ${unnamed + 1} needs a name.`;
  return "";
}

function EditorForm({ assignment, initialTests, concepts, onSaved, onCreateConcept }) {
  const [details, setDetails] = useState(() => detailsOf(assignment));
  const [tests, setTests] = useState(() => initialTests.map(toRow));
  const [state, setState] = useState({ busy: false, error: "", saved: false });
  const set = (field) => (event) => setDetails((old) => ({ ...old, [field]: event.target.value }));
  const published = assignment.is_published;

  async function save(extra) {
    const problem = validate(details, tests);
    if (problem) {
      setState({ busy: false, error: problem, saved: false });
      return;
    }
    setState({ busy: true, error: "", saved: false });
    try {
      await saveAssignment(assignment.id, details, tests, initialTests.map((test) => test.id), extra);
      await onSaved(); // reloads from the server, which remounts this form with fresh ids
    } catch (err) {
      setState({ busy: false, error: err.message, saved: false });
    }
  }

  return (
    <>
      <PageHeader
        breadcrumb={
          <>
            <Link to={`/courses/${assignment.course_id}`} className="hover:text-ink">
              {assignment.course_title}
            </Link>{" "}
            / Assignments
          </>
        }
        title={details.title || "Untitled assignment"}
        badge={<Chip tone={published ? "info" : "neutral"}>{published ? "Published" : "Draft"}</Chip>}
        subtitle="Students see the problem and the visible tests. For hidden tests they only see the verdict, the concept and your hint."
        right={
          <div className="flex gap-3">
            <Button variant="neutral" size="lg" disabled={state.busy} onClick={() => save({})}>
              {published ? "Save changes" : "Save draft"}
            </Button>
            <Button size="lg" disabled={state.busy} onClick={() => save({ is_published: !published })}>
              {published ? "Unpublish" : "Publish assignment"}
            </Button>
          </div>
        }
      />
      <div className="mb-6">
        <FormError>{state.error}</FormError>
      </div>
      <div className="grid gap-9 lg:grid-cols-[360px_1fr]">
        <Card className="self-start">
          <CardHeader icon={Pencil} title="Details" border={false} />
          <div className="space-y-5 px-7 pb-7">
            <TextField label="Title" value={details.title} onChange={set("title")} maxLength={200} />
            <label className="block text-sm font-semibold text-accent-soft/90">
              Problem, in Markdown
              <textarea
                className={`${inputClass} mt-2 min-h-44 resize-y font-normal`}
                value={details.description}
                onChange={set("description")}
              />
            </label>
            <TextField label="Due" type="datetime-local" value={details.due_at} onChange={set("due_at")} />
            <label className="block text-sm font-semibold text-accent-soft/90">
              Language
              <select className={`${inputClass} mt-2 font-normal`} value="python" disabled>
                <option value="python">Python 3.12</option>
              </select>
            </label>
            <div className="grid grid-cols-3 gap-3">
              <TextField label="Seconds" type="number" min="0.1" max="10" step="0.1" value={details.seconds} onChange={set("seconds")} />
              <TextField label="Memory, MB" type="number" min="16" max="512" value={details.memory_limit_mb} onChange={set("memory_limit_mb")} />
              <TextField label="Attempts" type="number" min="1" max="100" value={details.max_submissions} onChange={set("max_submissions")} />
            </div>
          </div>
        </Card>
        <div className="min-w-0">
          <TestCaseForm tests={tests} onChange={setTests} concepts={concepts} onCreateConcept={onCreateConcept} />
        </div>
      </div>
    </>
  );
}

/** Teacher editor for one assignment and its tests (mockup 12). */
export default function AssignmentEditor() {
  const assignmentId = Number(useParams().assignmentId);
  const queryClient = useQueryClient();
  const [version, setVersion] = useState(0);
  const [savedAt, setSavedAt] = useState(null);

  const assignment = useQuery({
    queryKey: ["assignment", assignmentId],
    queryFn: () => assignmentsApi.getAssignment(assignmentId),
  });
  const tests = useQuery({
    queryKey: ["test-cases", assignmentId],
    queryFn: () => assignmentsApi.listTestCases(assignmentId),
  });
  const courseId = assignment.data?.course_id;
  const concepts = useQuery({
    queryKey: ["concepts", courseId],
    queryFn: () => listConcepts(courseId),
    enabled: courseId != null,
  });

  if (assignment.isError) return <ErrorState error={assignment.error} onRetry={assignment.refetch} />;
  if (tests.isError) return <ErrorState error={tests.error} onRetry={tests.refetch} />;
  if (assignment.isPending || tests.isPending || concepts.isPending) return <LoadingState />;

  async function handleSaved() {
    await Promise.all([assignment.refetch(), tests.refetch()]);
    queryClient.invalidateQueries({ queryKey: ["assignments", courseId] });
    setVersion((n) => n + 1);
    setSavedAt(new Date());
  }

  async function handleCreateConcept(name) {
    const concept = await createConcept(courseId, name);
    await concepts.refetch();
    return concept;
  }

  return (
    <>
      {savedAt && (
        <p className="mb-4 rounded-lg border border-pass-line bg-pass-tint px-4 py-3 text-sm text-pass" role="status">
          Saved.
        </p>
      )}
      <EditorForm
        key={version}
        assignment={assignment.data}
        initialTests={tests.data}
        concepts={concepts.data ?? []}
        onSaved={handleSaved}
        onCreateConcept={handleCreateConcept}
      />
    </>
  );
}
