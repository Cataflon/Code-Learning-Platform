import { Bar, BarChart, Cell, LabelList, ResponsiveContainer, XAxis, YAxis } from "recharts";

import { Chip } from "./ui.jsx";

export const LEVELS = {
  review: { label: "Review", tone: "bad", color: "#ff6684" },
  progress: { label: "In progress", tone: "warn", color: "#ffbe4f" },
  mastered: { label: "Mastered", tone: "ok", color: "#5ee08c" },
};

/** The level is always written out, never shown by colour alone. */
export function LevelChip({ level }) {
  const { label, tone } = LEVELS[level] ?? LEVELS.review;
  return <Chip tone={tone}>{label}</Chip>;
}

export function percent(rate) {
  return `${Math.round(rate * 100)}%`;
}

/**
 * Horizontal bars, one per concept, weakest at the top (the data arrives sorted that way).
 * `items` are {name, rate, level}. A text list repeats the numbers for screen readers.
 */
export function ConceptBars({ items, title = "Pass rate by concept" }) {
  if (items.length === 0) return null;
  const data = items.map((item) => ({ ...item, value: Math.round(item.rate * 100) }));
  const height = Math.max(120, data.length * 44 + 20);

  return (
    <figure>
      <div style={{ height }} aria-hidden="true">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ top: 4, right: 48, left: 8, bottom: 4 }}>
            <XAxis type="number" domain={[0, 100]} hide />
            <YAxis
              type="category"
              dataKey="name"
              width={150}
              tickLine={false}
              axisLine={false}
              tick={{ fill: "#c9c5e6", fontSize: 14, fontFamily: "Pixelify Sans" }}
            />
            <Bar dataKey="value" barSize={16} minPointSize={3} isAnimationActive={false} background={{ fill: "#262c55" }}>
              <LabelList
                dataKey="value"
                position="right"
                formatter={(value) => `${value}%`}
                fill="#f5f2ff"
                fontSize={16}
                fontFamily="VT323"
              />
              {data.map((item) => (
                <Cell key={item.name} fill={LEVELS[item.level]?.color ?? LEVELS.review.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <figcaption className="sr-only">
        {title}:{" "}
        {data.map((item) => `${item.name} ${item.value}% (${LEVELS[item.level]?.label})`).join(", ")}
      </figcaption>
    </figure>
  );
}
