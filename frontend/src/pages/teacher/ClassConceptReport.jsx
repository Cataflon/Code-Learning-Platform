import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { getClassConceptReport } from "../../api/reports.js";
import { ConceptBars, LevelChip, percent } from "../../components/ConceptLevel.jsx";
import { CourseTabs } from "../CoursePage.jsx";
import { EmptyState, ErrorState, LoadingState } from "../../components/states.jsx";
import { Card, CardHeader, PageHeader, ProgressBar, Stat } from "../../components/ui.jsx";

const LEVEL_COLORS = { review: "var(--bad)", progress: "var(--warn)", mastered: "var(--ok)" };

/** The class view of the concept report: one row per concept, weakest first. */
export default function ClassConceptReport() {
  const courseId = Number(useParams().courseId);
  const { data, isPending, isError, error, refetch } = useQuery({
    queryKey: ["class-concept-report", courseId],
    queryFn: () => getClassConceptReport(courseId),
  });

  if (isPending) return <LoadingState />;
  if (isError) return <ErrorState error={error} onRetry={refetch} />;

  return (
    <>
      <PageHeader
        breadcrumb={
          <Link to="/courses" className="hover:text-ink">
            My courses
          </Link>
        }
        title={data.course_title}
        right={
          <div className="flex gap-12">
            <Stat value={data.students} label="students" />
            <Stat value={data.students_with_data} label="with results" />
          </div>
        }
      />
      <CourseTabs courseId={courseId} current="report" />
      {data.concepts.length === 0 ? (
        <Card>
          <EmptyState title="No results yet">
            The report fills in when students submit assignments whose tests have concepts.
          </EmptyState>
        </Card>
      ) : (
        <div className="cols">
          <Card>
            <CardHeader
              title="Concepts in this class"
              subtitle="Average of each student's pass rate, from their latest submission per assignment."
            />
            <div className="overflow-x-auto">
            <table className="tbl">
              <thead>
                <tr>
                  <th>Concept</th>
                  <th>Average pass rate</th>
                  <th className="hide-sm">Students to review</th>
                  <th className="hide-sm text-right">Level</th>
                </tr>
              </thead>
              <tbody>
                {data.concepts.map((concept) => (
                  <tr key={concept.concept_id}>
                    <td>
                      <b className="flex flex-wrap items-center gap-2">
                  {concept.concept}
                  <span className="show-sm">
                    <LevelChip level={concept.level} />
                  </span>
                </b>
                      <span className="block text-sm text-ink-3">
                        {concept.students_with_data} of {data.students} students with results
                      </span>
                    </td>
                    <td className="min-w-40">
                      <span className="flex items-center gap-3">
                        <ProgressBar
                          value={concept.average_pass_rate * 100}
                          color={LEVEL_COLORS[concept.level]}
                          label={`${concept.concept} average pass rate`}
                          className="flex-1"
                        />
                        <span className="num term w-12 text-right text-xl text-ink">
                          {percent(concept.average_pass_rate)}
                        </span>
                      </span>
                    </td>
                    <td className="hide-sm">
                      <span className={concept.students_in_review > 0 ? "text-bad" : "text-ink-3"}>
                        {concept.students_in_review}
                      </span>
                      <span className="text-ink-3"> · {concept.students_mastered} mastered</span>
                    </td>
                    <td className="hide-sm text-right">
                      <LevelChip level={concept.level} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            </div>
          </Card>
          <Card tint="bad">
            <CardHeader title="Class pass rate" />
            <div className="pad">
              <ConceptBars
                title="Class average pass rate by concept"
                items={data.concepts.map((c) => ({
                  name: c.concept,
                  rate: c.average_pass_rate,
                  level: c.level,
                }))}
              />
            </div>
          </Card>
        </div>
      )}
    </>
  );
}
