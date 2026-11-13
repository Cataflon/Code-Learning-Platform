// Shared building blocks of the 8-bit theme (docs/design-8bit/DESIGN.md, section 4).
// The look lives in src/index.css (.card, .btn, .chip, .bar, ...); these components only pick
// the right classes, so every screen draws pixel frames the same way.

import { useId } from "react";

/* ---------- buttons ---------- */

const BUTTON_VARIANTS = {
  primary: "btn primary",
  amber: "btn amber",
  outline: "btn",
  neutral: "btn",
  danger: "btn danger",
  ghost: "linklike",
};

/** Class string for anything that should look like a button (also used on <Link>). */
export function buttonClass(variant = "primary", size = "md", extra = "") {
  const base = BUTTON_VARIANTS[variant] ?? BUTTON_VARIANTS.primary;
  const sized = variant !== "ghost" && size === "sm" ? `${base} sm` : base;
  return `${sized} ${extra}`.trim();
}

/** PixelButton: flat block with relief; lifts on hover, presses down on click. */
export function Button({ variant = "primary", size = "md", className = "", ...props }) {
  return <button type="button" className={buttonClass(variant, size, className)} {...props} />;
}
export const PixelButton = Button;

/* ---------- cards ---------- */

const TINTS = {
  accent: "",
  ok: "t-ok",
  bad: "t-bad",
  warn: "t-warn",
  blue: "t-blue",
  pink: "t-pink",
  edge: "t-edge",
};

/**
 * PixelCard. `tint` says what the card holds: accent = current work, ok = score,
 * bad = to review, blue = submissions, warn = recommendations; `color` sets a course colour.
 * `lift` makes it rise on hover (for cards you can click). `as` renders a link or a section.
 */
export function Card({
  as: Tag = "section",
  tint = "accent",
  color,
  lift = false,
  className = "",
  style,
  children,
  ...props
}) {
  const classes = ["card", TINTS[tint] ?? "", lift ? "lift" : "", className].filter(Boolean).join(" ");
  const merged = color ? { "--tint": color, ...style } : style;
  return (
    <Tag className={classes} style={merged} {...props}>
      {children}
    </Tag>
  );
}
export const PixelCard = Card;

/** A small pixel square holding an icon. */
export function IconBadge({ icon: Icon, tone = "accent" }) {
  const colors = { accent: "var(--accent-strong)", fail: "var(--bad)", bad: "var(--bad)", warn: "var(--warn)" };
  return (
    <span
      className="chip shrink-0 justify-center"
      style={{ "--c": colors[tone] ?? colors.accent, width: 40, height: 40, padding: 0 }}
      aria-hidden="true"
    >
      <Icon style={{ width: 20, height: 20 }} />
    </span>
  );
}

/** Card title row: pixel title on the left, a link or a note on the right, dashed line below. */
export function CardHeader({ title, subtitle, right, border = true, icon: Icon }) {
  return (
    <header className="card-head" style={border ? undefined : { borderBottom: 0, paddingBottom: 6 }}>
      <div className="flex min-w-0 items-center gap-3">
        {Icon && <Icon className="h-4 w-4 shrink-0 text-ink-3" aria-hidden="true" />}
        <div className="min-w-0">
          <h2>{title}</h2>
          {subtitle && <p className="mt-1 text-[13.5px] text-ink-3">{subtitle}</p>}
        </div>
      </div>
      {right && <div className="aside flex shrink-0 items-center gap-2">{right}</div>}
    </header>
  );
}

/* ---------- chips, bars, stats ---------- */

const CHIP_TONES = {
  accent: "",
  neutral: "idle",
  idle: "idle",
  pass: "ok",
  ok: "ok",
  fail: "bad",
  bad: "bad",
  warn: "warn",
  info: "blue",
  blue: "blue",
  pink: "pink",
};

export function Chip({ tone = "accent", icon: Icon, className = "", style, children }) {
  const classes = ["chip", CHIP_TONES[tone] ?? "", className].filter(Boolean).join(" ");
  return (
    <span className={classes} style={style}>
      {Icon && <Icon aria-hidden="true" />}
      {children}
    </span>
  );
}

/** Segmented progress bar: 8 px blocks with 2 px gaps. `value` is 0..100. */
export function ProgressBar({ value = 0, color, label, className = "" }) {
  const clamped = Math.max(0, Math.min(100, value));
  return (
    <span
      className={`bar ${className}`}
      style={color ? { "--tint": color } : undefined}
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={Math.round(clamped)}
      aria-label={label}
    >
      <i style={{ "--w": `${clamped}%` }} />
    </span>
  );
}

/** Big number with a caption, for page headers. */
export function Stat({ value, label, tone }) {
  const color = { fail: "var(--bad)", bad: "var(--bad)", ok: "var(--ok)" }[tone] ?? "var(--ink)";
  return (
    <div>
      <div className="num font-display text-[22px] leading-none" style={{ color }}>
        {value}
      </div>
      <div className="mt-2 text-sm text-ink-3">{label}</div>
    </div>
  );
}

/** Statistic card of the dashboard: caption on the left, pixel number on the right. */
export function StatCard({ value, label, tint = "accent", as, ...props }) {
  return (
    <Card tint={tint} lift as={as} className="stat" {...props}>
      <div className="pad">
        <span>{label}</span>
        <b className="num">{value}</b>
      </div>
    </Card>
  );
}

/* ---------- form fields ---------- */

export const inputClass = "field";

export function TextField({ label, error, hint, className = "", inputClassName = "", ...props }) {
  const id = useId();
  return (
    <div className={className}>
      <label htmlFor={id} className="label">
        {label}
      </label>
      <input
        id={id}
        className={`field ${inputClassName}`}
        aria-invalid={error ? "true" : undefined}
        {...props}
      />
      {error && <p className="mt-2 font-plain text-sm text-bad">{error}</p>}
      {!error && hint && <p className="mt-2 text-sm text-ink-3">{hint}</p>}
    </div>
  );
}

/** Inline form or action error, in a pixel frame. */
export function FormError({ children }) {
  if (!children) return null;
  return (
    <p
      className="chip bad h-auto whitespace-normal px-4 py-3 font-plain text-sm leading-snug"
      role="alert"
    >
      {children}
    </p>
  );
}

/* ---------- people and brand ---------- */

export function initialsOf(name = "") {
  const parts = name
    .replace(/^(dr|prof|assoc)\.?\s+/gi, "")
    .trim()
    .split(/\s+/)
    .filter(Boolean);
  return ((parts[0]?.[0] ?? "") + (parts.length > 1 ? parts.at(-1)[0] : "")).toUpperCase() || "?";
}

export function Avatar({ name, size = "md" }) {
  return (
    <span className={`avatar ${size === "lg" ? "lg" : ""}`} aria-hidden="true">
      {initialsOf(name)}
    </span>
  );
}

/** Four squares, one hollow; they rotate and change colours on hover. */
export function Logo() {
  return (
    <span className="brand">
      <span className="mark" aria-hidden="true">
        <i />
        <i />
        <i />
        <i />
      </span>
      Autograder
    </span>
  );
}

/** Page title with an optional breadcrumb above and content on the right. */
export function PageHeader({ breadcrumb, title, subtitle, right, badge }) {
  return (
    <div className="page-head">
      {breadcrumb && <div className="crumb">{breadcrumb}</div>}
      <div className="line">
        <div className="min-w-0">
          <h1 className="flex flex-wrap items-center gap-4">
            {title}
            {badge}
          </h1>
          {subtitle && <p className="lede mt-3">{subtitle}</p>}
        </div>
        {right}
      </div>
    </div>
  );
}
