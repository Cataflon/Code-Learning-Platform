// The profile's activity grid: one column per week, one square per day, darker = fewer.

const LEVEL_CLASSES = ["bg-[#22244a]", "bg-[#34367a]", "bg-[#4b4bb0]", "bg-[#6a66ee]", "bg-[#a5a1ff]"];
const ROW_LABELS = ["Mon", "", "Wed", "", "Fri", "", "Sun"];

function isoDay(date) {
  const pad = (n) => String(n).padStart(2, "0");
  return `${date.getUTCFullYear()}-${pad(date.getUTCMonth() + 1)}-${pad(date.getUTCDate())}`;
}

function levelOf(count, max) {
  if (count === 0) return 0;
  if (max <= 4) return Math.min(count, 4);
  return Math.max(1, Math.ceil((count / max) * 4));
}

/**
 * Build the grid: `weeks` columns ending with the current week, rows Monday..Sunday.
 * Days after `today` are null. Dates are compared as UTC days, like the API reports them.
 */
export function buildActivityGrid(days, weeks, today = new Date()) {
  const counts = new Map(days.map((day) => [day.date, day.count]));
  const end = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate()));
  const mondayOffset = (end.getUTCDay() + 6) % 7; // Monday = 0
  const start = new Date(end);
  start.setUTCDate(end.getUTCDate() - mondayOffset - (weeks - 1) * 7);

  const columns = [];
  for (let week = 0; week < weeks; week++) {
    const column = [];
    for (let weekday = 0; weekday < 7; weekday++) {
      const date = new Date(start);
      date.setUTCDate(start.getUTCDate() + week * 7 + weekday);
      column.push(date > end ? null : { date: isoDay(date), count: counts.get(isoDay(date)) ?? 0 });
    }
    columns.push(column);
  }
  return columns;
}

export default function ActivityGrid({ days, weeks }) {
  const columns = buildActivityGrid(days, weeks);
  const max = Math.max(0, ...days.map((day) => day.count));

  return (
    <div>
      <div className="flex gap-3" role="img" aria-label={`Submissions per day in the last ${weeks} weeks`}>
        <div className="grid grid-rows-7 gap-1.5 text-xs text-muted">
          {ROW_LABELS.map((label, index) => (
            <span key={index} className="h-5 leading-5">
              {label}
            </span>
          ))}
        </div>
        {columns.map((column, index) => (
          <div key={index} className="grid grid-rows-7 gap-1.5">
            {column.map((cell, row) =>
              cell ? (
                <span
                  key={row}
                  title={`${cell.date}: ${cell.count} ${cell.count === 1 ? "submission" : "submissions"}`}
                  className={`h-5 w-5 rounded ${LEVEL_CLASSES[levelOf(cell.count, max)]}`}
                />
              ) : (
                <span key={row} className="h-5 w-5" />
              ),
            )}
          </div>
        ))}
      </div>
      <p className="mt-4 flex items-center gap-1.5 text-sm text-muted">
        less
        {LEVEL_CLASSES.map((cls) => (
          <span key={cls} className={`h-3.5 w-3.5 rounded ${cls}`} />
        ))}
        more
      </p>
    </div>
  );
}
