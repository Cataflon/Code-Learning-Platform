import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { getDashboard } from "../api/dashboard.js";
import { getRecommendations, viewerLink } from "../api/materials.js";
import { CourseCover, courseColor } from "../components/MaterialBits.jsx";
import { EmptyState, ErrorState, LoadingState } from "../components/states.jsx";
import { buttonClass, Card, Chip, PageHeader } from "../components/ui.jsx";
import { useLearn } from "../hooks/useMaterials.js";
import { plural, timeAgo } from "../lib/format.js";
import { describePages } from "../lib/pages.js";

/** "Recommended after your last attempt": the top material for the latest imperfect submission. */
function useLatestRecommendation() {
  const dashboard = useQuery({ queryKey: ["dashboard"], queryFn: getDashboard });
  const latest = dashboard.data?.recent_submissions.find(
    (submission) => submission.status === "done" && submission.score !== 100,
  );
  const recommendations = useQuery({
    queryKey: ["recommendations", latest?.id],
    queryFn: () => getRecommendations(latest.id),
    enabled: latest != null,
  });
  const top = recommendations.data?.materials[0];
  return top ? { material: top, assignment: latest.assignment_title } : null;
}

function RecommendationBand({ recommendation }) {
  const { material, assignment } = recommendation;
  return (
    <Card tint="warn">
      <div className="pad reco">
        <p className="plain">
          <b>Recommended after your last attempt.</b> {material.title},{" "}
          {describePages(material.pages).toLowerCase()}, covers what failed in {assignment}.
        </p>
        <Link
          to={viewerLink(material.material_id, {
            page: material.first_page,
            pages: material.pages,
            from: assignment,
          })}
          className={buttonClass("amber")}
        >
          {material.pages ? `Open at page ${material.first_page}` : "Open"}
        </Link>
      </div>
    </Card>
  );
}

function CourseCard({ course }) {
  const empty = course.material_count === 0;
  const body = (
    <>
      <div className="relative">
        <CourseCover course={course} />
        <span className="absolute left-3 top-3">
          <Chip className="bg-black/60 text-white">{plural(course.material_count, "material")}</Chip>
        </span>
      </div>
      <div className="body">
        <h3>{course.title}</h3>
        <div className="meta">
          <span>{course.teacher_name}</span>
          <span>{course.last_material_at ? `added ${timeAgo(course.last_material_at)}` : ""}</span>
        </div>
        {empty && (
          <p className="plain text-sm text-ink-3">
            No materials yet. Your teacher has not uploaded anything for this course.
          </p>
        )}
      </div>
    </>
  );
  if (empty) {
    return (
      <Card className="course" color={courseColor(course.color)}>
        {body}
      </Card>
    );
  }
  return (
    <Card
      as={Link}
      to={`/learn/courses/${course.id}`}
      lift
      className="course"
      color={courseColor(course.color)}
      aria-label={`${course.title}, ${plural(course.material_count, "material")}`}
    >
      {body}
    </Card>
  );
}

/** Learn: one card per course the student is enrolled in. */
export default function Learn() {
  const { data: courses, isPending, isError, error, refetch } = useLearn();
  const recommendation = useLatestRecommendation();

  return (
    <>
      <PageHeader title="Learn" subtitle="Lecture and lab materials from your teachers, one card per course." />
      {recommendation && <RecommendationBand recommendation={recommendation} />}
      {isPending && <LoadingState />}
      {isError && <ErrorState error={error} onRetry={refetch} />}
      {courses?.length === 0 && (
        <Card>
          <EmptyState title="No courses yet">Join a course from your profile to see its materials.</EmptyState>
        </Card>
      )}
      {courses?.length > 0 && (
        <div className="courses">
          {courses.map((course) => (
            <CourseCard key={course.id} course={course} />
          ))}
        </div>
      )}
    </>
  );
}
