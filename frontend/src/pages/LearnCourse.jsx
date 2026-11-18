import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { downloadOriginal, viewerLink } from "../api/materials.js";
import { CourseCover, courseColor, FileBadge } from "../components/MaterialBits.jsx";
import { EmptyState, ErrorState, LoadingState } from "../components/states.jsx";
import { Button, buttonClass, Card, Chip } from "../components/ui.jsx";
import { useCourse } from "../hooks/useCourses.js";
import { useCourseMaterials } from "../hooks/useMaterials.js";
import { plural, timeAgo } from "../lib/format.js";
import { unitOf } from "../lib/pages.js";

const FILTERS = [
  { key: "all", label: "All" },
  { key: "lecture", label: "Lectures" },
  { key: "lab", label: "Labs" },
];

function MaterialRow({ material, number, color }) {
  const [error, setError] = useState("");
  return (
    <Card lift className="lesson" color={color}>
      <span className="no num">{number}</span>
      <FileBadge type={material.file_type} />
      <span className="min-w-0">
        <Link to={viewerLink(material.id)} className="hover:text-accent-strong">
          <b>{material.title}</b>
        </Link>
        <small>
          {material.original_filename} · {plural(material.page_count, unitOf(material).slice(0, -1))} · added{" "}
          {timeAgo(material.created_at)}
        </small>
        {error && <small className="block text-bad">{error}</small>}
      </span>
      <span className="extra flex flex-wrap gap-1">
        {material.used_in.map((usage) => (
          <Chip key={usage.assignment_id} tone="accent">
            Used in: {usage.assignment_title}
          </Chip>
        ))}
      </span>
      <span className="flex flex-wrap justify-end gap-1">
        <Link to={viewerLink(material.id)} className={buttonClass("primary", "sm")}>
          Open
        </Link>
        <Button
          variant="neutral"
          size="sm"
          onClick={() => downloadOriginal(material).catch((err) => setError(err.message))}
          aria-label={`Download ${material.title}`}
        >
          Download
        </Button>
      </span>
    </Card>
  );
}

/** The materials of one course (mockup 07, in the 8-bit style of the prototype). */
export default function LearnCourse() {
  const courseId = Number(useParams().courseId);
  const course = useCourse(courseId);
  const materials = useCourseMaterials(courseId);
  const [filter, setFilter] = useState("all");

  if (course.isPending || materials.isPending) return <LoadingState />;
  if (course.isError) return <ErrorState error={course.error} onRetry={course.refetch} />;
  if (materials.isError) return <ErrorState error={materials.error} onRetry={materials.refetch} />;

  const all = materials.data;
  const counts = {
    all: all.length,
    lecture: all.filter((m) => m.category === "lecture").length,
    lab: all.filter((m) => m.category === "lab").length,
  };
  const shown = filter === "all" ? all : all.filter((m) => m.category === filter);
  const color = courseColor(course.data.color);

  return (
    <>
      <p className="crumb">
        <Link to="/learn">Learn</Link>
        <span>/</span>
        <span>{course.data.title}</span>
      </p>
      <Card className="c-hero" color={color}>
        <CourseCover course={course.data} />
        <div className="pad grid content-center gap-3">
          <h1>{course.data.title}</h1>
          <p>
            {course.data.teacher_name}, {plural(all.length, "material")}
          </p>
        </div>
      </Card>
      <nav className="tabs" aria-label="Filter materials">
        {FILTERS.map((item) => (
          <button
            key={item.key}
            type="button"
            className="tab"
            aria-selected={filter === item.key}
            onClick={() => setFilter(item.key)}
          >
            {item.label} {counts[item.key]}
          </button>
        ))}
      </nav>
      {shown.length === 0 ? (
        <Card>
          <EmptyState title="Nothing here yet">
            {all.length === 0
              ? "Your teacher has not uploaded any material for this course."
              : "No materials in this category."}
          </EmptyState>
        </Card>
      ) : (
        <div className="lessons">
          {shown.map((material, index) => (
            <MaterialRow key={material.id} material={material} number={index + 1} color={color} />
          ))}
        </div>
      )}
    </>
  );
}
