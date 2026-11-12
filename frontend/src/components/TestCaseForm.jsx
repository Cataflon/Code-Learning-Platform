import { Eye, FlaskConical, Plus, Trash2, X } from "lucide-react";
import { useState } from "react";

import { Card, Chip, IconBadge, inputClass } from "./ui.jsx";

let nextKey = 1;

/** A blank test row. `key` is a client-side identity for rows that have no id yet. */
export function emptyTest() {
  return {
    key: `new-${nextKey++}`,
    name: "",
    input_data: "",
    expected_output: "",
    is_hidden: false,
    weight: 1,
    hint: "",
    concept_ids: [],
  };
}

/** Turn a test from the API into an editable row. */
export function toRow(test) {
  return {
    key: `id-${test.id}`,
    id: test.id,
    name: test.name,
    input_data: test.input_data,
    expected_output: test.expected_output,
    is_hidden: test.is_hidden,
    weight: test.weight,
    hint: test.hint ?? "",
    concept_ids: test.concepts.map((concept) => concept.id),
  };
}

const SEGMENT_TONES = ["bg-accent-tint border-accent/50 text-accent-soft", "bg-info-tint border-info-line text-info"];

function WeightBar({ tests }) {
  const total = tests.reduce((sum, test) => sum + (Number(test.weight) || 0), 0);
  if (tests.length === 0 || total === 0) return null;
  return (
    <div className="flex gap-1.5 px-7 pb-6">
      {tests.map((test, index) => (
        <span
          key={test.key}
          style={{ flexGrow: Number(test.weight) || 0 }}
          className={`min-w-0 basis-0 truncate rounded-md border px-3 py-1.5 text-xs font-semibold ${
            test.is_hidden
              ? "border-dashed border-hidden bg-hidden-tint text-hidden"
              : SEGMENT_TONES[index % SEGMENT_TONES.length]
          }`}
        >
          {test.name || `Test ${index + 1}`}, {test.weight}
        </span>
      ))}
    </div>
  );
}

function Toggle({ checked, onChange, label }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      onClick={() => onChange(!checked)}
      className={`relative h-7 w-12 rounded-full transition-colors ${checked ? "bg-accent" : "bg-idle"}`}
    >
      <span
        className={`absolute top-1 h-5 w-5 rounded-full bg-white transition-all ${checked ? "left-6" : "left-1"}`}
      />
    </button>
  );
}

function ConceptPicker({ selectedIds, concepts, onChange, onCreateConcept }) {
  const [adding, setAdding] = useState(false);
  const [newName, setNewName] = useState("");
  const [error, setError] = useState("");
  const selected = concepts.filter((concept) => selectedIds.includes(concept.id));
  const available = concepts.filter((concept) => !selectedIds.includes(concept.id));

  async function createAndAdd() {
    const name = newName.trim();
    if (!name) return;
    try {
      const concept = await onCreateConcept(name);
      onChange([...selectedIds, concept.id]);
      setNewName("");
      setAdding(false);
      setError("");
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div>
      <div className="flex flex-wrap items-center gap-2">
        <span className="mr-1 text-sm font-semibold text-accent-soft/90">Concepts</span>
        {selected.map((concept) => (
          <Chip key={concept.id}>
            {concept.name}
            <button
              type="button"
              aria-label={`Remove concept ${concept.name}`}
              onClick={() => onChange(selectedIds.filter((id) => id !== concept.id))}
              className="hover:text-white"
            >
              <X className="h-3 w-3" />
            </button>
          </Chip>
        ))}
        {!adding && (
          <button type="button" className="px-2 text-sm text-muted hover:text-ink" onClick={() => setAdding(true)}>
            Add concept
          </button>
        )}
      </div>
      {adding && (
        <div className="mt-3 flex flex-wrap items-center gap-2">
          {available.map((concept) => (
            <button
              key={concept.id}
              type="button"
              onClick={() => onChange([...selectedIds, concept.id])}
              className="rounded-md border border-line px-2.5 py-1 text-xs font-semibold text-muted hover:border-accent-soft hover:text-accent-soft"
            >
              + {concept.name}
            </button>
          ))}
          <input
            className={`${inputClass} w-48 py-1.5 text-sm`}
            aria-label="New concept name"
            placeholder="New concept"
            value={newName}
            maxLength={80}
            onChange={(event) => setNewName(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                createAndAdd();
              }
            }}
          />
          <button type="button" className="text-sm font-semibold text-accent-soft" onClick={createAndAdd}>
            Create
          </button>
          <button type="button" className="text-sm text-muted" onClick={() => setAdding(false)}>
            Done
          </button>
        </div>
      )}
      {error && <p className="mt-2 text-sm text-fail">{error}</p>}
    </div>
  );
}

const areaClass = `${inputClass} min-h-24 resize-y font-mono text-sm`;

function TestRow({ test, index, concepts, onChange, onRemove, onCreateConcept }) {
  const set = (field) => (value) => onChange({ ...test, [field]: value });
  const fromEvent = (field) => (event) => set(field)(event.target.value);
  const label = `test ${index + 1}`;

  return (
    <Card className={`overflow-hidden ${test.is_hidden ? "border-hidden" : ""}`} aria-label={`Test ${index + 1}`}>
      <header
        className={`flex flex-wrap items-center gap-4 border-b border-line px-6 py-4 ${
          test.is_hidden ? "bg-hidden-tint" : "bg-raised"
        }`}
      >
        <span
          className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-sm font-semibold ${
            test.is_hidden ? "bg-hidden text-bg" : "bg-accent-tint text-accent-soft"
          }`}
        >
          {index + 1}
        </span>
        <input
          className="min-w-0 flex-1 bg-transparent font-semibold placeholder:text-faint focus:outline-none"
          aria-label={`Name of ${label}`}
          placeholder="Test name"
          value={test.name}
          maxLength={120}
          onChange={fromEvent("name")}
        />
        <label className="flex items-center gap-3 text-sm text-muted">
          Weight
          <input
            type="number"
            min="1"
            max="100"
            className={`${inputClass} w-20 py-2 text-center`}
            aria-label={`Weight of ${label}`}
            value={test.weight}
            onChange={(event) => set("weight")(event.target.value === "" ? "" : Number(event.target.value))}
          />
        </label>
        <span className="flex items-center gap-3 text-sm text-muted">
          Hidden
          <Toggle checked={test.is_hidden} onChange={set("is_hidden")} label={`Hide ${label}`} />
        </span>
        <button
          type="button"
          onClick={onRemove}
          aria-label={`Remove ${label}`}
          className="rounded-lg border border-fail/60 p-2 text-fail hover:bg-fail-tint"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </header>
      <div className="space-y-5 p-6">
        {test.is_hidden && (
          <p className="flex items-center gap-3 text-sm text-hidden">
            <Eye className="h-4 w-4" aria-hidden="true" />
            Students never see this test's input or expected output.
          </p>
        )}
        <div className="grid gap-5 md:grid-cols-2">
          <label className="block text-sm font-semibold text-accent-soft/90">
            Input
            <textarea className={`${areaClass} mt-2`} value={test.input_data} onChange={fromEvent("input_data")} />
          </label>
          <label className="block text-sm font-semibold text-accent-soft/90">
            Expected output
            <textarea
              className={`${areaClass} mt-2`}
              value={test.expected_output}
              onChange={fromEvent("expected_output")}
            />
          </label>
        </div>
        <label className="block text-sm font-semibold text-accent-soft/90">
          Hint for students, optional
          <input className={`${inputClass} mt-2 font-normal`} value={test.hint} maxLength={500} onChange={fromEvent("hint")} />
          <span className="mt-1.5 block font-normal text-muted">Shown only when this test fails.</span>
        </label>
        <ConceptPicker
          selectedIds={test.concept_ids}
          concepts={concepts}
          onChange={set("concept_ids")}
          onCreateConcept={onCreateConcept}
        />
      </div>
    </Card>
  );
}

/**
 * The list of tests as dynamic rows. The state is an array of objects owned by the parent;
 * adding, editing and removing a row are immutable updates of that array.
 */
export default function TestCaseForm({ tests, onChange, concepts, onCreateConcept }) {
  const totalWeight = tests.reduce((sum, test) => sum + (Number(test.weight) || 0), 0);

  return (
    <div className="space-y-6">
      <Card>
        <header className="flex items-center gap-4 px-7 py-5">
          <IconBadge icon={FlaskConical} />
          <h2 className="flex-1 text-lg font-semibold">Tests</h2>
          <span className="text-muted">
            total weight <strong className="text-ink">{totalWeight}</strong>
          </span>
        </header>
        <WeightBar tests={tests} />
        {tests.length === 0 && (
          <p className="px-7 pb-6 text-sm text-muted">No tests yet. Students cannot submit until there is one.</p>
        )}
      </Card>
      {tests.map((test, index) => (
        <TestRow
          key={test.key}
          test={test}
          index={index}
          concepts={concepts}
          onCreateConcept={onCreateConcept}
          onChange={(updated) => onChange(tests.map((row) => (row.key === test.key ? updated : row)))}
          onRemove={() => onChange(tests.filter((row) => row.key !== test.key))}
        />
      ))}
      <button
        type="button"
        onClick={() => onChange([...tests, emptyTest()])}
        className="flex w-full items-center justify-center gap-3 rounded-card border border-dashed border-line py-6 font-semibold text-accent-soft hover:border-accent-soft"
      >
        <Plus className="h-4 w-4" aria-hidden="true" />
        Add a test
      </button>
    </div>
  );
}
