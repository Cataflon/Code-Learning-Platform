// The three states every page handles the same way: loading, error, empty.

import { AlertTriangle, Inbox, Loader2 } from "lucide-react";

import { buttonClass } from "./ui.jsx";

export function LoadingState({ label = "Loading…" }) {
  return (
    <div className="flex items-center justify-center gap-3 py-16 text-ink-3" role="status">
      <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}

export function ErrorState({ error, onRetry }) {
  return (
    <div className="card t-bad flex flex-col items-center gap-3 px-6 py-10 text-center" role="alert">
      <AlertTriangle className="h-6 w-6 text-bad" aria-hidden="true" />
      <p className="font-plain text-bad">{error?.message ?? "Something went wrong."}</p>
      {onRetry && (
        <button type="button" className={buttonClass("neutral", "sm")} onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  );
}

export function EmptyState({ title, children, action }) {
  return (
    <div className="flex flex-col items-center gap-2 px-6 py-12 text-center">
      <Inbox className="h-6 w-6 text-ink-3" aria-hidden="true" />
      <h2>{title}</h2>
      {children && <p className="max-w-md font-plain text-sm text-ink-3">{children}</p>}
      {action && <div className="mt-3">{action}</div>}
    </div>
  );
}
