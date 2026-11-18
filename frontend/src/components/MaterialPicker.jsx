import { Plus, X } from "lucide-react";
import { useId, useState } from "react";

import { FileBadge } from "./MaterialBits.jsx";
import { Button } from "./ui.jsx";
import { pagesError } from "../lib/pages.js";

/**
 * A list of {material_id, pages} links for an assignment or a test, edited in place.
 * `materials` is the course's list; `links` and `onChange` are owned by the parent.
 */
export default function MaterialPicker({ links, onChange, materials, addLabel = "Add", label }) {
  const selectId = useId();
  const [choice, setChoice] = useState("");
  const byId = new Map(materials.map((material) => [material.id, material]));
  const available = materials.filter((material) => !links.some((link) => link.material_id === material.id));

  function update(materialId, pages) {
    onChange(links.map((link) => (link.material_id === materialId ? { ...link, pages } : link)));
  }

  return (
    <div className="grid gap-1">
      {links.map((link) => {
        const material = byId.get(link.material_id);
        if (!material) return null;
        const error = pagesError(link.pages, material.page_count);
        const fieldId = `${selectId}-${link.material_id}`;
        return (
          <div key={link.material_id} className="mat items-start">
            <FileBadge type={material.file_type} />
            <span className="min-w-0 self-center">
              <b>{material.title}</b>
              <small>
                {material.page_count} {material.file_type === "pptx" ? "slides" : "pages"}
              </small>
            </span>
            <span className="flex items-start gap-2">
              <span className="w-44">
                <label className="label text-sm" htmlFor={fieldId}>
                  Pages (empty = all)
                </label>
                <input
                  id={fieldId}
                  className="field mono"
                  value={link.pages}
                  placeholder="e.g. 12-15, 18"
                  aria-invalid={error ? "true" : undefined}
                  onChange={(event) => update(link.material_id, event.target.value)}
                />
                {error && <span className="mt-1 block font-plain text-sm text-bad">{error}</span>}
              </span>
              <Button
                variant="neutral"
                size="sm"
                className="icon mt-7"
                aria-label={`Remove ${material.title}`}
                onClick={() => onChange(links.filter((other) => other.material_id !== link.material_id))}
              >
                <X className="h-4 w-4" aria-hidden="true" />
              </Button>
            </span>
          </div>
        );
      })}
      {available.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 px-6 py-3">
          <select
            id={selectId}
            className="field max-w-md"
            aria-label={label ?? "Add a material from this course"}
            value={choice}
            onChange={(event) => setChoice(event.target.value)}
          >
            <option value="">Add a material from this course…</option>
            {available.map((material) => (
              <option key={material.id} value={material.id}>
                {material.title}
              </option>
            ))}
          </select>
          <Button
            variant="neutral"
            size="sm"
            disabled={!choice}
            onClick={() => {
              onChange([...links, { material_id: Number(choice), pages: "" }]);
              setChoice("");
            }}
          >
            <Plus className="h-4 w-4" aria-hidden="true" />
            {addLabel}
          </Button>
        </div>
      )}
    </div>
  );
}

/** True when every pages field of every list is valid. */
export function linksAreValid(lists, materials) {
  const byId = new Map(materials.map((material) => [material.id, material]));
  return lists.every((links) =>
    links.every((link) => !pagesError(link.pages, byId.get(link.material_id)?.page_count)),
  );
}
