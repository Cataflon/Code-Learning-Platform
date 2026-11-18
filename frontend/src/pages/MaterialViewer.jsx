import { useQuery } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight, Download } from "lucide-react";
import { lazy, Suspense, useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";

import { downloadOriginal, fetchPreview } from "../api/materials.js";
import { courseColor, FileBadge } from "../components/MaterialBits.jsx";
import { ErrorState, LoadingState } from "../components/states.jsx";
import { Button, Card, CardHeader, Chip, FormError } from "../components/ui.jsx";
import { useCourse } from "../hooks/useCourses.js";
import { useMaterial } from "../hooks/useMaterials.js";
import { formatBytes, plural, timeAgo } from "../lib/format.js";
import { pageSet, unitOf } from "../lib/pages.js";

const PdfSheet = lazy(() => import("../components/PdfSheet.jsx"));

function clampPage(value, last) {
  const page = Number.parseInt(value, 10);
  if (!Number.isFinite(page) || page < 1) return 1;
  return last ? Math.min(page, last) : page;
}

/** Width of the PDF page: the stage's width minus its padding, measured on resize. */
function useStageWidth() {
  const ref = useRef(null);
  const [width, setWidth] = useState(640);
  useLayoutEffect(() => {
    const element = ref.current;
    if (!element) return undefined;
    const measure = () => setWidth(Math.max(240, Math.min(900, element.clientWidth - 40)));
    measure();
    if (typeof ResizeObserver === "undefined") return undefined;
    const observer = new ResizeObserver(measure);
    observer.observe(element);
    return () => observer.disconnect();
  }, []);
  return [ref, width];
}

function AboutCard({ material, course }) {
  const rows = [
    ["Course", course?.title ?? "…"],
    ["Teacher", course?.teacher_name ?? "…"],
    ["File", `${material.file_type.toUpperCase()}, ${plural(material.page_count, unitOf(material).slice(0, -1))}`],
    ["Size", formatBytes(material.size_bytes)],
    ["Added", timeAgo(material.created_at)],
    ["Used in", material.used_in.map((u) => u.assignment_title).join(", ") || "No assignment yet"],
  ];
  return (
    <Card>
      <CardHeader title="About this file" />
      <dl className="info">
        {rows.map(([label, value]) => (
          <div key={label}>
            <dt>{label}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
    </Card>
  );
}

/** The page viewer (mockup 08): opens at ?page=N and highlights the recommended pages ?rec=. */
export default function MaterialViewer() {
  const materialId = Number(useParams().materialId);
  const [params, setParams] = useSearchParams();
  const material = useMaterial(materialId);
  const course = useCourse(material.data?.course_id);
  const preview = useQuery({
    queryKey: ["material-preview", materialId],
    queryFn: () => fetchPreview(materialId),
    staleTime: Infinity,
  });
  const [stageRef, width] = useStageWidth();
  const [downloadError, setDownloadError] = useState("");

  const last = material.data?.page_count;
  const page = clampPage(params.get("page"), last);
  const recommended = params.get("rec") ?? "";
  const from = params.get("from");
  const highlighted = pageSet(recommended, last);

  const go = useCallback(
    (target) => {
      const next = clampPage(target, last);
      setParams(
        (old) => {
          const copy = new URLSearchParams(old);
          copy.set("page", next);
          return copy;
        },
        { replace: true },
      );
    },
    [last, setParams],
  );

  // Arrow keys turn the pages, except while typing in a field.
  useEffect(() => {
    function onKey(event) {
      if (event.target.closest?.("input, textarea, select")) return;
      if (event.key === "ArrowRight") go(page + 1);
      if (event.key === "ArrowLeft") go(page - 1);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [go, page]);

  // Keep the current page button in view in the strip.
  const stripRef = useRef(null);
  useEffect(() => {
    const strip = stripRef.current;
    const current = strip?.querySelector(".cur");
    if (strip && current) strip.scrollLeft = current.offsetLeft - strip.clientWidth / 2;
  }, [page]);

  if (material.isPending) return <LoadingState />;
  if (material.isError) return <ErrorState error={material.error} onRetry={material.refetch} />;

  const item = material.data;
  const color = courseColor(course.data?.color);
  const backTo = course.data ? `/learn/courses/${course.data.id}` : "/learn";

  return (
    <>
      <div className="page-head">
        <p className="crumb">
          <Link to="/learn">Learn</Link>
          <span>/</span>
          <Link to={backTo}>{course.data?.title ?? "Course"}</Link>
        </p>
        <div className="line">
          <h1 className="flex flex-wrap items-center gap-4 text-[clamp(17px,2.2vw,24px)]">
            <FileBadge type={item.file_type} />
            {item.title}
          </h1>
          <div className="meta-line">
            {recommended && <Chip tone="warn">Recommended pages {recommended}</Chip>}
            <Button
              variant="neutral"
              onClick={() => downloadOriginal(item).catch((err) => setDownloadError(err.message))}
            >
              <Download className="h-4 w-4" aria-hidden="true" />
              Download original
            </Button>
          </div>
        </div>
        <FormError>{downloadError}</FormError>
      </div>
      <div className="reader">
        <Card color={color}>
          <div className="v-bar">
            <Button variant="neutral" className="icon" aria-label="Previous page" disabled={page <= 1} onClick={() => go(page - 1)}>
              <ChevronLeft aria-hidden="true" />
            </Button>
            <span className="pg num" aria-live="polite">
              {page} / {item.page_count}
            </span>
            <Button
              variant="neutral"
              className="icon"
              aria-label="Next page"
              disabled={page >= item.page_count}
              onClick={() => go(page + 1)}
            >
              <ChevronRight aria-hidden="true" />
            </Button>
            <span className="flex-1" />
            {from && <span className="hidden text-sm text-ink-3 md:inline">Opened from your {from} result</span>}
          </div>
          <div className="stage" ref={stageRef}>
            {preview.isPending && <LoadingState label="Opening the file…" />}
            {preview.isError && <FormError>{preview.error.message}</FormError>}
            {preview.data && (
              <Suspense fallback={<LoadingState label="Opening the viewer…" />}>
                <PdfSheet file={preview.data} page={page} width={width} />
              </Suspense>
            )}
          </div>
          <div className="thumbs" ref={stripRef} aria-label="Pages">
            {Array.from({ length: item.page_count }, (_, index) => index + 1).map((number) => (
              <button
                key={number}
                type="button"
                className={`num ${number === page ? "cur" : highlighted.has(number) ? "rec" : ""}`}
                aria-label={`Page ${number}${highlighted.has(number) ? ", recommended" : ""}`}
                aria-current={number === page ? "page" : undefined}
                onClick={() => go(number)}
              >
                {number}
              </button>
            ))}
          </div>
        </Card>
        <aside className="stack">
          <AboutCard material={item} course={course.data} />
          {recommended && (
            <Card tint="warn">
              <CardHeader title="Recommended" />
              <p className="pad plain text-ink-2">
                Pages <span className="pages">{recommended}</span> explain what your failed tests check.
                They are marked in the page strip.
              </p>
            </Card>
          )}
        </aside>
      </div>
    </>
  );
}
