import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { getAssignment, listTestCases } from "../../api/assignments.js";
import { getAssignmentMaterials, setAssignmentMaterials, setTestCaseMaterials } from "../../api/materials.js";
import MaterialPicker, { linksAreValid } from "../../components/MaterialPicker.jsx";
import { EmptyState, ErrorState, LoadingState } from "../../components/states.jsx";
import { Button, Card, CardHeader, Chip, FormError, PageHeader } from "../../components/ui.jsx";
import { useCourseMaterials } from "../../hooks/useMaterials.js";

function toLinks(items) {
  return items.map((item) => ({ material_id: item.material_id, pages: item.pages }));
}

function EditorForm({ assignment, tests, materials, initialAssignmentLinks, onSaved, saved }) {
  const [assignmentLinks, setAssignmentLinksState] = useState(() => toLinks(initialAssignmentLinks));
  const [testLinks, setTestLinks] = useState(() =>
    Object.fromEntries(tests.map((test) => [test.id, toLinks(test.materials ?? [])])),
  );
  const [state, setState] = useState({ busy: false, error: "", saved: false });
  const valid = linksAreValid([assignmentLinks, ...Object.values(testLinks)], materials);

  async function save() {
    setState({ busy: true, error: "", saved: false });
    try {
      await setAssignmentMaterials(assignment.id, assignmentLinks);
      for (const test of tests) await setTestCaseMaterials(test.id, testLinks[test.id]);
      await onSaved(); // remounts the form with what the server stored
    } catch (error) {
      setState({ busy: false, error: error.message, saved: false });
    }
  }

  return (
    <>
      <PageHeader
        breadcrumb={
          <>
            <Link to="/courses" className="hover:text-ink">
              My courses
            </Link>{" "}
            /{" "}
            <Link to={`/courses/${assignment.course_id}`} className="hover:text-ink">
              {assignment.course_title}
            </Link>{" "}
            /{" "}
            <Link to={`/teacher/assignments/${assignment.id}/edit`} className="hover:text-ink">
              {assignment.title}
            </Link>
          </>
        }
        title="Study materials"
        subtitle="Choose where students can find what they need. Failed tests send them to the right pages."
        right={
          <Button size="lg" onClick={save} disabled={!valid || state.busy}>
            {state.busy ? "Saving…" : "Save"}
          </Button>
        }
      />
      <FormError>{state.error}</FormError>
      {saved && !state.busy && (
        <p className="text-ok" role="status">
          Saved.
        </p>
      )}
      <Card tint="warn">
        <CardHeader title="Materials for the whole assignment" />
        {assignmentLinks.length === 0 && (
          <p className="px-6 pt-4 text-sm text-ink-3">No materials yet. Students see this list on the assignment page.</p>
        )}
        <MaterialPicker links={assignmentLinks} onChange={setAssignmentLinksState} materials={materials} />
      </Card>
      <Card>
        <CardHeader title="Materials per test" right={<span>A test without materials uses the ones above.</span>} />
        <div className="sep">
          {tests.map((test, index) => (
            <section key={test.id} className="py-4" aria-label={`Materials for test ${index + 1}`}>
              <h3 className="flex flex-wrap items-center gap-2 px-6 pb-2">
                <b className="text-ink">{test.name}</b>
                {test.is_hidden && <Chip tone="neutral">hidden</Chip>}
                {test.concepts.map((concept) => (
                  <Chip key={concept.id}>{concept.name}</Chip>
                ))}
              </h3>
              {testLinks[test.id].length === 0 && (
                <p className="px-6 text-sm text-ink-3">
                  No materials of its own. Students are sent to the assignment materials.
                </p>
              )}
              <MaterialPicker
                links={testLinks[test.id]}
                onChange={(links) => setTestLinks((old) => ({ ...old, [test.id]: links }))}
                materials={materials}
                addLabel="Add to this test"
                label={`Add a material to ${test.name}`}
              />
            </section>
          ))}
        </div>
        {tests.length === 0 && <EmptyState title="No tests yet">Add tests in the assignment editor first.</EmptyState>}
      </Card>
    </>
  );
}

/** Link materials, with pages, to an assignment and to each of its tests (mockup 13). */
export default function StudyMaterialsEditor() {
  const assignmentId = Number(useParams().assignmentId);
  const [version, setVersion] = useState(0);
  const [saved, setSaved] = useState(false);
  const assignment = useQuery({ queryKey: ["assignment", assignmentId], queryFn: () => getAssignment(assignmentId) });
  const tests = useQuery({ queryKey: ["test-cases", assignmentId], queryFn: () => listTestCases(assignmentId) });
  const links = useQuery({
    queryKey: ["assignment-materials", assignmentId],
    queryFn: () => getAssignmentMaterials(assignmentId),
  });
  const materials = useCourseMaterials(assignment.data?.course_id);

  for (const query of [assignment, tests, links, materials]) {
    if (query.isError) return <ErrorState error={query.error} onRetry={query.refetch} />;
  }
  if (assignment.isPending || tests.isPending || links.isPending || materials.isPending) return <LoadingState />;

  if (materials.data.length === 0) {
    return (
      <Card>
        <EmptyState
          title="This course has no materials yet"
          action={
            <Link to={`/courses/${assignment.data.course_id}/materials`} className="btn primary">
              Upload materials
            </Link>
          }
        >
          Upload lectures and labs in the Materials tab, then link them here.
        </EmptyState>
      </Card>
    );
  }

  return (
    <EditorForm
      key={version}
      assignment={assignment.data}
      tests={tests.data}
      materials={materials.data}
      initialAssignmentLinks={links.data}
      saved={saved}
      onSaved={async () => {
        await Promise.all([tests.refetch(), links.refetch(), materials.refetch()]);
        setVersion((n) => n + 1);
        setSaved(true);
      }}
    />
  );
}
