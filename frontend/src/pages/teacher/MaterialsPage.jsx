import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Pencil, Trash2, Upload } from "lucide-react";
import { useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { reindexMaterial } from "../../api/ai.js";
import { deleteMaterial, updateMaterial, uploadMaterial, viewerLink } from "../../api/materials.js";
import { useAiConfig } from "../../components/AiTests.jsx";
import { FileBadge } from "../../components/MaterialBits.jsx";
import { EmptyState, ErrorState, LoadingState } from "../../components/states.jsx";
import { Button, Card, CardHeader, Chip, FormError, PageHeader, TextField } from "../../components/ui.jsx";
import { useCourse } from "../../hooks/useCourses.js";
import { useCourseMaterials } from "../../hooks/useMaterials.js";
import { formatBytes, plural, timeAgo } from "../../lib/format.js";
import { CourseTabs } from "../CoursePage.jsx";

const MAX_MB = 20;
const CATEGORIES = [
  { value: "lecture", label: "Lecture" },
  { value: "lab", label: "Lab" },
];

function titleFromName(name) {
  return name.replace(/\.[^.]+$/, "").replace(/[-_]+/g, " ").trim();
}

function CategorySelect({ value, onChange, id }) {
  return (
    <select id={id} className="field" value={value} onChange={(event) => onChange(event.target.value)}>
      {CATEGORIES.map((item) => (
        <option key={item.value} value={item.value}>
          {item.label}
        </option>
      ))}
    </select>
  );
}

function UploadCard({ courseId }) {
  const queryClient = useQueryClient();
  const inputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState("lecture");
  const [over, setOver] = useState(false);
  const [localError, setLocalError] = useState("");

  const upload = useMutation({
    mutationFn: () => uploadMaterial(courseId, { file, title, category }),
    onSuccess: () => {
      setFile(null);
      setTitle("");
      if (inputRef.current) inputRef.current.value = "";
      queryClient.invalidateQueries({ queryKey: ["materials", courseId] });
    },
  });

  function choose(selected) {
    upload.reset();
    setLocalError("");
    if (!selected) return;
    if (selected.size > MAX_MB * 1024 * 1024) {
      setLocalError(`The file is larger than ${MAX_MB} MB.`);
      return;
    }
    setFile(selected);
    if (!title) setTitle(titleFromName(selected.name));
  }

  const isPptx = file?.name.toLowerCase().endsWith(".pptx");

  return (
    <Card>
      <div className="grid gap-6 p-6 md:grid-cols-2">
        <div
          className={`dropzone ${over ? "over" : ""}`}
          onDragOver={(event) => {
            event.preventDefault();
            setOver(true);
          }}
          onDragLeave={() => setOver(false)}
          onDrop={(event) => {
            event.preventDefault();
            setOver(false);
            choose(event.dataTransfer.files?.[0]);
          }}
        >
          <Upload className="h-6 w-6 text-accent-strong" aria-hidden="true" />
          <h2>Drop a PDF or PPTX here</h2>
          <p className="plain max-w-sm text-sm text-ink-3">
            Up to {MAX_MB} MB. Presentations are converted to PDF so students can read them in the
            browser.
          </p>
          <Button variant="neutral" size="sm" onClick={() => inputRef.current?.click()}>
            Choose a file
          </Button>
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.pptx,application/pdf,application/vnd.openxmlformats-officedocument.presentationml.presentation"
            className="sr-only"
            aria-label="Material file"
            onChange={(event) => choose(event.target.files?.[0])}
          />
        </div>
        <form
          className="grid content-start gap-4"
          onSubmit={(event) => {
            event.preventDefault();
            if (file) upload.mutate();
          }}
        >
          <TextField label="Title" value={title} maxLength={120} onChange={(e) => setTitle(e.target.value)} />
          <div>
            <label className="label" htmlFor="upload-category">
              Category
            </label>
            <CategorySelect id="upload-category" value={category} onChange={setCategory} />
          </div>
          {file && (
            <div className="flex items-center gap-3">
              <FileBadge type={isPptx ? "pptx" : "pdf"} />
              <span className="min-w-0">
                <b className="block truncate text-ink">{file.name}</b>
                <small className="text-ink-3">
                  {formatBytes(file.size)}
                  {upload.isPending && (isPptx ? " · converting to PDF, this can take a few seconds" : " · uploading")}
                </small>
              </span>
            </div>
          )}
          {upload.isPending && <span className="bar" role="progressbar" aria-label="Uploading"><i className="animate-pulse" style={{ "--w": "70%" }} /></span>}
          <FormError>{localError || (upload.isError ? upload.error.message : "")}</FormError>
          {upload.isSuccess && <p className="text-sm text-ok" role="status">Uploaded.</p>}
          <div className="flex justify-end gap-2">
            <Button
              variant="neutral"
              disabled={!file || upload.isPending}
              onClick={() => {
                setFile(null);
                setTitle("");
                upload.reset();
              }}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={!file || upload.isPending}>
              {upload.isPending ? "Uploading…" : "Upload"}
            </Button>
          </div>
        </form>
      </div>
    </Card>
  );
}

function MaterialRow({ material, courseId }) {
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState(material.title);
  const [category, setCategory] = useState(material.category);
  const refresh = () => queryClient.invalidateQueries({ queryKey: ["materials", courseId] });

  const save = useMutation({
    mutationFn: () => updateMaterial(material.id, { title, category }),
    onSuccess: () => {
      setEditing(false);
      refresh();
    },
  });
  const remove = useMutation({ mutationFn: () => deleteMaterial(material.id), onSuccess: refresh });
  const reindex = useMutation({ mutationFn: () => reindexMaterial(material.id), onSuccess: refresh });
  const ai = useAiConfig();

  function confirmDelete() {
    const linked = material.used_in.length
      ? ` It is linked to ${plural(material.used_in.length, "assignment")}; the links go too.`
      : "";
    if (window.confirm(`Delete “${material.title}”?${linked}`)) remove.mutate();
  }

  return (
    <tr>
      <td>
        <span className="flex items-center gap-3">
          <FileBadge type={material.file_type} />
          {editing ? (
            <form
              className="flex flex-wrap items-center gap-2"
              onSubmit={(event) => {
                event.preventDefault();
                save.mutate();
              }}
            >
              <input
                className="field w-64"
                aria-label="New title"
                value={title}
                maxLength={120}
                onChange={(e) => setTitle(e.target.value)}
                autoFocus
              />
              <span className="w-32">
                <CategorySelect value={category} onChange={setCategory} />
              </span>
              <Button type="submit" size="sm" disabled={!title.trim() || save.isPending}>
                Save
              </Button>
              <Button variant="neutral" size="sm" onClick={() => setEditing(false)}>
                Cancel
              </Button>
            </form>
          ) : (
            <span className="min-w-0">
              <Link to={viewerLink(material.id)} className="hover:text-accent-strong">
                <b>{material.title}</b>
              </Link>
              <span className="block text-sm text-ink-3">
                {material.original_filename} · {formatBytes(material.size_bytes)} · {plural(material.page_count, "page")} ·{" "}
                {material.category === "lab" ? "lab" : "lecture"} · {timeAgo(material.created_at)}
              </span>
            </span>
          )}
        </span>
        {ai.data?.ai_available && material.text_pages === 0 && (
          <span className="mt-2 flex flex-wrap items-center gap-2">
            <Chip tone="warn">No text found, link pages manually</Chip>
            <Button variant="ghost" size="sm" onClick={() => reindex.mutate()} disabled={reindex.isPending}>
              {reindex.isPending ? "Reading…" : "Read the text again"}
            </Button>
          </span>
        )}
        {(save.isError || remove.isError) && (
          <div className="mt-2">
            <FormError>{(save.error ?? remove.error).message}</FormError>
          </div>
        )}
      </td>
      <td className="hide-sm">
        {material.used_in.length === 0 ? (
          <span className="text-sm text-ink-3">Not linked yet</span>
        ) : (
          <span className="flex flex-wrap gap-1">
            {material.used_in.map((usage) => (
              <Chip key={usage.assignment_id}>
                {usage.assignment_title}
                {usage.test_count > 0 && ` · ${plural(usage.test_count, "test")}`}
              </Chip>
            ))}
          </span>
        )}
      </td>
      <td className="text-right">
        {!editing && (
          <span className="inline-flex gap-1">
            <Button variant="neutral" size="sm" onClick={() => setEditing(true)} aria-label={`Rename ${material.title}`}>
              <Pencil className="h-4 w-4" aria-hidden="true" />
              Rename
            </Button>
            <Button
              variant="danger"
              size="sm"
              className="icon"
              disabled={remove.isPending}
              onClick={confirmDelete}
              aria-label={`Delete ${material.title}`}
            >
              <Trash2 className="h-4 w-4" aria-hidden="true" />
            </Button>
          </span>
        )}
      </td>
    </tr>
  );
}

/** The teacher's Materials tab (mockup 11): upload, list, rename, delete. */
export default function MaterialsPage() {
  const courseId = Number(useParams().courseId);
  const course = useCourse(courseId);
  const materials = useCourseMaterials(courseId);

  if (course.isPending) return <LoadingState />;
  if (course.isError) return <ErrorState error={course.error} onRetry={course.refetch} />;

  return (
    <>
      <PageHeader
        breadcrumb={
          <Link to="/courses" className="hover:text-ink">
            My courses
          </Link>
        }
        title={course.data.title}
      />
      <CourseTabs courseId={courseId} current="materials" />
      <UploadCard courseId={courseId} />
      <Card>
        <CardHeader
          title="Uploaded materials"
          right={materials.data && <span>{plural(materials.data.length, "file")}</span>}
        />
        {materials.isPending && <LoadingState />}
        {materials.isError && <ErrorState error={materials.error} onRetry={materials.refetch} />}
        {materials.data?.length === 0 && (
          <EmptyState title="No materials yet">Upload a lecture or a lab above.</EmptyState>
        )}
        {materials.data?.length > 0 && (
          <div className="overflow-x-auto">
            <table className="tbl">
              <thead>
                <tr>
                  <th>Material</th>
                  <th className="hide-sm">Used in</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {materials.data.map((material) => (
                  <MaterialRow key={material.id} material={material} courseId={courseId} />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </>
  );
}
