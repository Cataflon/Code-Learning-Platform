import { Link } from "react-router-dom";

import { buttonClass } from "../components/ui.jsx";

export default function NotFoundPage() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 text-center">
      <p className="font-mono text-6xl font-bold text-accent-soft">404</p>
      <h1 className="text-2xl font-bold">Page not found</h1>
      <p className="text-muted">This page does not exist, or you do not have access to it.</p>
      <Link to="/" className={buttonClass("primary")}>
        Back to the start
      </Link>
    </div>
  );
}
