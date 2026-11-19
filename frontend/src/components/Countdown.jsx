// "28:00:30 left": the time to a deadline, ticking every second, in the terminal font of the
// prototype. Shown only when the deadline is less than three days away.

import { useEffect, useState } from "react";

const SHOW_WITHIN_MS = 72 * 3600 * 1000;

function timeLeft(due, now = Date.now()) {
  const ms = new Date(due).getTime() - now;
  if (!(ms > 0) || ms > SHOW_WITHIN_MS) return null;
  const total = Math.floor(ms / 1000);
  const pad = (n) => String(n).padStart(2, "0");
  return `${pad(Math.floor(total / 3600))}:${pad(Math.floor((total % 3600) / 60))}:${pad(total % 60)}`;
}

export default function Countdown({ due }) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);
  const text = due ? timeLeft(due, now) : null;
  if (!text) return null;
  return (
    <span className="clock num" role="timer" aria-label={`${text} left until the deadline`}>
      {text} left
    </span>
  );
}
