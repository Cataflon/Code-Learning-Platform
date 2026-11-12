import { X } from "lucide-react";
import { useEffect, useId, useRef } from "react";

/** Centered dialog over a dimmed page. Closes with Escape, the X button or a click outside. */
export default function Modal({ title, subtitle, icon, onClose, children, footer, wide = false }) {
  const titleId = useId();
  const panelRef = useRef(null);

  useEffect(() => {
    function onKeyDown(event) {
      if (event.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKeyDown);
    panelRef.current?.focus();
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/70 px-4 py-24"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        className={`w-full rounded-card border border-line bg-surface shadow-2xl outline-none ${
          wide ? "max-w-4xl" : "max-w-2xl"
        }`}
      >
        <header className="flex items-start gap-4 px-7 py-6">
          {icon}
          <div className="min-w-0 flex-1">
            <h2 id={titleId} className="text-xl font-semibold">
              {title}
            </h2>
            {subtitle && <p className="mt-1 text-muted">{subtitle}</p>}
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close dialog"
            className="rounded-lg border border-line p-2 text-muted hover:text-ink"
          >
            <X className="h-4 w-4" />
          </button>
        </header>
        {children}
        {footer && <footer className="flex justify-end gap-3 border-t border-line px-7 py-5">{footer}</footer>}
      </div>
    </div>
  );
}
