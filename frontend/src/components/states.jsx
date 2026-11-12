// The three states every page handles the same way: loading, error, empty.

import { AlertTriangle, Inbox, Loader2 } from "lucide-react";

import { buttonClass } from "./ui.jsx";

export function LoadingState({ label = "Loading…" }) {
  return (
    <div className="flex items-center justify-center gap-3 py-16 text-muted" role="status">
      <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}

export function ErrorState({ error, onRetry }) {
  return (
    <div
      className="flex flex-col items-center gap-3 rounded-card border border-fail-line bg-fail-tint px-6 py-10 text-center"
      role="alert"
    >
      <AlertTriangle className="h-6 w-6 text-fail" aria-hidden="true" />
      <p className="text-fail">{error?.message ?? "Something went wrong."}</p>
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
      <Inbox className="h-6 w-6 text-faint" aria-hidden="true" />
      <p className="font-semibold">{title}</p>
      {children && <p className="max-w-md text-sm text-muted">{children}</p>}
      {action && <div className="mt-3">{action}</div>}
    </div>
  );
}
