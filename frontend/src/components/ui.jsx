// Shared building blocks of mockup variant D: buttons, cards, chips, fields, avatar, logo.

import { useId } from "react";

const BUTTON_BASE =
  "inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-colors " +
  "focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-soft " +
  "disabled:cursor-not-allowed disabled:opacity-50";

const BUTTON_VARIANTS = {
  primary: "bg-accent text-white hover:bg-accent-hover",
  outline: "border border-accent-soft/70 text-accent-soft hover:bg-accent-tint",
  neutral: "border border-line text-ink hover:bg-raised",
  danger: "border border-fail/70 text-fail hover:bg-fail-tint",
  ghost: "text-accent-soft hover:text-white",
};

const BUTTON_SIZES = {
  sm: "px-3 py-1.5 text-sm",
  md: "px-4 py-2.5 text-sm",
  lg: "px-6 py-3.5 text-base",
};

/** Class string for anything that should look like a button (also used on <Link>). */
export function buttonClass(variant = "primary", size = "md", extra = "") {
  return `${BUTTON_BASE} ${BUTTON_VARIANTS[variant]} ${BUTTON_SIZES[size]} ${extra}`;
}

export function Button({ variant = "primary", size = "md", className = "", ...props }) {
  return <button type="button" className={buttonClass(variant, size, className)} {...props} />;
}

export function Card({ className = "", children, ...props }) {
  return (
    <section className={`rounded-card border border-line bg-surface ${className}`} {...props}>
      {children}
    </section>
  );
}

/** The round icon that opens every card title in the mockups. */
export function IconBadge({ icon: Icon, tone = "accent" }) {
  const tones = {
    accent: "border-accent/50 bg-accent-tint text-accent-soft",
    fail: "border-fail-line bg-fail-tint text-fail",
    warn: "border-warn-line bg-warn-tint text-warn",
  };
  return (
    <span
      className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-full border ${tones[tone]}`}
      aria-hidden="true"
    >
      <Icon className="h-5 w-5" />
    </span>
  );
}

export function CardHeader({ icon, tone, title, subtitle, right, border = true }) {
  return (
    <header
      className={`flex items-center gap-4 px-7 py-5 ${border ? "border-b border-line" : ""}`}
    >
      {icon && <IconBadge icon={icon} tone={tone} />}
      <div className="min-w-0 flex-1">
        <h2 className="text-lg font-semibold">{title}</h2>
        {subtitle && <p className="text-sm text-muted">{subtitle}</p>}
      </div>
      {right}
    </header>
  );
}

const CHIP_TONES = {
  accent: "border-accent/50 bg-accent-tint text-accent-soft",
  neutral: "border-line bg-raised text-muted",
  pass: "border-pass-line bg-pass-tint text-pass",
  fail: "border-fail-line bg-fail-tint text-fail",
  warn: "border-warn-line bg-warn-tint text-warn",
  info: "border-info-line bg-info-tint text-info",
};

export function Chip({ tone = "accent", icon: Icon, className = "", children }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-md border px-2.5 py-1 text-xs font-semibold ${CHIP_TONES[tone]} ${className}`}
    >
      {Icon && <Icon className="h-3.5 w-3.5" aria-hidden="true" />}
      {children}
    </span>
  );
}

export const inputClass =
  "w-full rounded-lg border border-line bg-raised px-4 py-3 text-ink placeholder:text-faint " +
  "focus:border-accent-soft focus:outline-none disabled:text-muted";

export function TextField({ label, error, hint, className = "", inputClassName = "", ...props }) {
  const id = useId();
  return (
    <div className={className}>
      <label htmlFor={id} className="mb-2 block text-sm font-semibold text-accent-soft/90">
        {label}
      </label>
      <input
        id={id}
        className={`${inputClass} ${inputClassName}`}
        aria-invalid={error ? "true" : undefined}
        {...props}
      />
      {error && <p className="mt-1.5 text-sm text-fail">{error}</p>}
      {!error && hint && <p className="mt-1.5 text-sm text-muted">{hint}</p>}
    </div>
  );
}

export function initialsOf(name = "") {
  const parts = name
    .replace(/^(dr|prof|assoc)\.?\s+/gi, "")
    .trim()
    .split(/\s+/)
    .filter(Boolean);
  return ((parts[0]?.[0] ?? "") + (parts.length > 1 ? parts.at(-1)[0] : "")).toUpperCase() || "?";
}

export function Avatar({ name, size = "md" }) {
  const sizes = { sm: "h-10 w-10 text-xs", md: "h-12 w-12 text-sm", lg: "h-24 w-24 text-2xl" };
  return (
    <span
      className={`flex shrink-0 items-center justify-center rounded-full border border-accent/50 bg-accent-tint font-semibold text-accent-soft ${sizes[size]}`}
      aria-hidden="true"
    >
      {initialsOf(name)}
    </span>
  );
}

/** The four rounded squares, one of them hollow. */
export function Logo({ light = false }) {
  const fill = light ? "bg-white" : "bg-accent";
  const ring = light ? "border-white" : "border-accent";
  return (
    <span className="inline-flex items-center gap-3">
      <span className="grid grid-cols-2 gap-1" aria-hidden="true">
        <span className={`h-4 w-4 rounded ${fill}`} />
        <span className={`h-4 w-4 rounded ${fill}`} />
        <span className={`h-4 w-4 rounded ${fill}`} />
        <span className={`h-4 w-4 rounded border-2 ${ring}`} />
      </span>
      <span className="text-xl font-bold">Autograder</span>
    </span>
  );
}

/** Inline form or action error. */
export function FormError({ children }) {
  if (!children) return null;
  return (
    <p className="rounded-lg border border-fail-line bg-fail-tint px-4 py-3 text-sm text-fail" role="alert">
      {children}
    </p>
  );
}

/** Page title with an optional breadcrumb line above and content on the right. */
export function PageHeader({ breadcrumb, title, subtitle, right, badge }) {
  return (
    <div className="mb-8 flex flex-wrap items-end justify-between gap-6">
      <div className="min-w-0">
        {breadcrumb && <div className="mb-1 text-sm text-muted">{breadcrumb}</div>}
        <h1 className="flex flex-wrap items-center gap-3 text-4xl font-bold">
          {title}
          {badge}
        </h1>
        {subtitle && <p className="mt-2 max-w-3xl text-muted">{subtitle}</p>}
      </div>
      {right}
    </div>
  );
}

/** Big number with a caption, used in page headers. */
export function Stat({ value, label, tone }) {
  return (
    <div>
      <div className={`text-3xl font-bold ${tone === "fail" ? "text-fail" : ""}`}>{value}</div>
      <div className="text-sm text-muted">{label}</div>
    </div>
  );
}
