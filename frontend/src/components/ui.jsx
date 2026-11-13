// Shared building blocks of mockup variant D: buttons, cards, chips, fields, avatar, logo.

import { useId } from "react";

const BUTTON_BASE =
  "inline-flex items-center justify-center gap-2 font-semibold transition-colors " +
  "focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-strong " +
  "disabled:cursor-not-allowed disabled:opacity-50";

const BUTTON_VARIANTS = {
  primary: "bg-accent text-white hover:bg-accent",
  outline: "border border-accent-strong/70 text-accent-strong hover:bg-accent/20",
  neutral: "border border-edge text-ink hover:bg-black/35",
  danger: "border border-bad/70 text-bad hover:bg-bad/15",
  ghost: "text-accent-strong hover:text-white",
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
    <section className={`border border-edge bg-card ${className}`} {...props}>
      {children}
    </section>
  );
}

/** The round icon that opens every card title in the mockups. */
export function IconBadge({ icon: Icon, tone = "accent" }) {
  const tones = {
    accent: "border-accent/50 bg-accent/20 text-accent-strong",
    fail: "border-bad/40 bg-bad/15 text-bad",
    warn: "border-warn/40 bg-warn/15 text-warn",
  };
  return (
    <span
      className={`flex h-11 w-11 shrink-0 items-center justify-center border ${tones[tone]}`}
      aria-hidden="true"
    >
      <Icon className="h-5 w-5" />
    </span>
  );
}

export function CardHeader({ icon, tone, title, subtitle, right, border = true }) {
  return (
    <header
      className={`flex items-center gap-4 px-7 py-5 ${border ? "border-b border-edge" : ""}`}
    >
      {icon && <IconBadge icon={icon} tone={tone} />}
      <div className="min-w-0 flex-1">
        <h2 className="text-lg font-semibold">{title}</h2>
        {subtitle && <p className="text-sm text-ink-3">{subtitle}</p>}
      </div>
      {right}
    </header>
  );
}

const CHIP_TONES = {
  accent: "border-accent/50 bg-accent/20 text-accent-strong",
  neutral: "border-edge bg-black/35 text-ink-3",
  pass: "border-ok/40 bg-ok/15 text-ok",
  fail: "border-bad/40 bg-bad/15 text-bad",
  warn: "border-warn/40 bg-warn/15 text-warn",
  info: "border-blue/40 bg-blue/15 text-blue",
};

export function Chip({ tone = "accent", icon: Icon, className = "", children }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 whitespace-nowrap border px-2.5 py-1 text-xs font-semibold ${CHIP_TONES[tone]} ${className}`}
    >
      {Icon && <Icon className="h-3.5 w-3.5" aria-hidden="true" />}
      {children}
    </span>
  );
}

export const inputClass =
  "w-full border border-edge bg-black/35 px-4 py-3 text-ink placeholder:text-ink-3 " +
  "focus:border-accent-strong focus:outline-none disabled:text-ink-3";

export function TextField({ label, error, hint, className = "", inputClassName = "", ...props }) {
  const id = useId();
  return (
    <div className={className}>
      <label htmlFor={id} className="mb-2 block text-sm font-semibold text-ink-2">
        {label}
      </label>
      <input
        id={id}
        className={`${inputClass} ${inputClassName}`}
        aria-invalid={error ? "true" : undefined}
        {...props}
      />
      {error && <p className="mt-1.5 text-sm text-bad">{error}</p>}
      {!error && hint && <p className="mt-1.5 text-sm text-ink-3">{hint}</p>}
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
      className={`flex shrink-0 items-center justify-center border border-accent/50 bg-accent/20 font-semibold text-accent-strong ${sizes[size]}`}
      aria-hidden="true"
    >
      {initialsOf(name)}
    </span>
  );
}

/** The four squares, one of them hollow. */
export function Logo({ light = false }) {
  const fill = light ? "bg-white" : "bg-accent";
  const ring = light ? "border-white" : "border-accent";
  return (
    <span className="inline-flex items-center gap-3">
      <span className="grid grid-cols-2 gap-1" aria-hidden="true">
        <span className={`h-4 w-4 ${fill}`} />
        <span className={`h-4 w-4 ${fill}`} />
        <span className={`h-4 w-4 ${fill}`} />
        <span className={`h-4 w-4 border-2 ${ring}`} />
      </span>
      <span className="text-xl font-bold">Autograder</span>
    </span>
  );
}

/** Inline form or action error. */
export function FormError({ children }) {
  if (!children) return null;
  return (
    <p className="border border-bad/40 bg-bad/15 px-4 py-3 text-sm text-bad" role="alert">
      {children}
    </p>
  );
}

/** Page title with an optional breadcrumb line above and content on the right. */
export function PageHeader({ breadcrumb, title, subtitle, right, badge }) {
  return (
    <div className="mb-8 flex flex-wrap items-end justify-between gap-6">
      <div className="min-w-0">
        {breadcrumb && <div className="mb-1 text-sm text-ink-3">{breadcrumb}</div>}
        <h1 className="flex flex-wrap items-center gap-3 text-4xl font-bold">
          {title}
          {badge}
        </h1>
        {subtitle && <p className="mt-2 max-w-3xl text-ink-3">{subtitle}</p>}
      </div>
      {right}
    </div>
  );
}

/** Big number with a caption, used in page headers. */
export function Stat({ value, label, tone }) {
  return (
    <div>
      <div className={`text-3xl font-bold ${tone === "fail" ? "text-bad" : ""}`}>{value}</div>
      <div className="text-sm text-ink-3">{label}</div>
    </div>
  );
}
