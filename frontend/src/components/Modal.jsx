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
      className="overlay"
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
        className={`card w-full outline-none ${wide ? "max-w-4xl" : "max-w-2xl"}`}
        style={{ background: "var(--card)" }}
      >
        <header className="card-head items-start">
          {icon}
          <div className="min-w-0 flex-1">
            <h2 id={titleId}>
              {title}
            </h2>
            {subtitle && <p className="mt-2 text-ink-3">{subtitle}</p>}
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close dialog"
            className="btn icon"
          >
            <X className="h-4 w-4" />
          </button>
        </header>
        {children}
        {footer && <footer className="dash-top flex justify-end gap-3 px-6 py-4">{footer}</footer>}
      </div>
    </div>
  );
}
