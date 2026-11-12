import { Button } from "./ui.jsx";

/** "1–6 of 214" with Previous and Next. `page` starts at 1. */
export default function Pagination({ page, pageSize, total, onPageChange }) {
  if (total === 0) return null;
  const first = (page - 1) * pageSize + 1;
  const last = Math.min(page * pageSize, total);
  const lastPage = Math.ceil(total / pageSize);

  return (
    <nav className="flex items-center justify-between px-7 py-4" aria-label="Pagination">
      <span className="text-sm text-muted">
        {first}–{last} of {total}
      </span>
      <span className="flex gap-3">
        <Button variant="neutral" disabled={page <= 1} onClick={() => onPageChange(page - 1)}>
          Previous
        </Button>
        <Button variant="neutral" disabled={page >= lastPage} onClick={() => onPageChange(page + 1)}>
          Next
        </Button>
      </span>
    </nav>
  );
}
