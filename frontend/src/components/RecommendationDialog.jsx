import { BookOpen } from "lucide-react";
import { Link } from "react-router-dom";

import { viewerLink } from "../api/materials.js";
import { FileBadge } from "./MaterialBits.jsx";
import Modal from "./Modal.jsx";
import { Button, buttonClass, Chip, IconBadge } from "./ui.jsx";
import { describePages, unitOf } from "../lib/pages.js";
import { plural } from "../lib/format.js";

const SEEN_PREFIX = "autograder.reco.";

/** The popup shows once per submission (remembered for the browser tab, a convenience only). */
export function alreadyShown(submissionId) {
  try {
    return sessionStorage.getItem(`${SEEN_PREFIX}${submissionId}`) === "1";
  } catch {
    return false;
  }
}

export function markShown(submissionId) {
  try {
    sessionStorage.setItem(`${SEEN_PREFIX}${submissionId}`, "1");
  } catch {
    // storage blocked: the popup may simply show again
  }
}

/** "Review before your next attempt" (mockup 04). */
export default function RecommendationDialog({ recommendations, attemptNumber, assignmentTitle, onClose }) {
  const { failed_tests: failed, materials } = recommendations;

  return (
    <Modal
      icon={<IconBadge icon={BookOpen} tone="warn" />}
      title="Review before your next attempt"
      subtitle={`${plural(failed.length, "test")} failed in attempt ${attemptNumber}. These materials cover it.`}
      onClose={onClose}
      footer={
        <Button variant="neutral" onClick={onClose}>
          Close
        </Button>
      }
    >
      <p className="flex flex-wrap items-center gap-2 px-6 pb-4 text-ink-3">
        Failed:
        {failed.map((test) => (
          <span key={test.test_case_id} className="flex flex-wrap items-center gap-2">
            <b className="text-ink">{test.name}</b>
            {test.concepts.map((concept) => (
              <Chip key={concept}>{concept}</Chip>
            ))}
          </span>
        ))}
      </p>
      <ul>
        {materials.map((material) => {
          const where = describePages(material.pages, unitOf(material));
          const why = material.from_assignment
            ? "from the assignment materials"
            : `helps with ${plural(material.test_count, "failed test")}`;
          return (
            <li key={material.material_id} className="mat">
              <FileBadge type={material.file_type} />
              <span className="min-w-0">
                <b>{material.title}</b>
                <small>
                  {where} · {why}
                </small>
              </span>
              <Link
                to={viewerLink(material.material_id, {
                  page: material.first_page,
                  pages: material.pages,
                  from: assignmentTitle,
                })}
                className={buttonClass(material.pages ? "primary" : "neutral", "sm")}
                onClick={onClose}
              >
                {material.pages ? `Open at page ${material.first_page}` : "Open"}
              </Link>
            </li>
          );
        })}
      </ul>
    </Modal>
  );
}
