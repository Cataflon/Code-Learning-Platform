// Date and number formatting shared by all pages. Pure functions: `now` can be injected in tests.

const DAY_MS = 24 * 60 * 60 * 1000;
const WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
const MONTHS = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
];

function startOfDay(date) {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

/** Whole days from `now` to `date`, by calendar day (today = 0, tomorrow = 1, yesterday = -1). */
export function dayDifference(date, now = new Date()) {
  return Math.round((startOfDay(date) - startOfDay(now)) / DAY_MS);
}

export function formatTime(date) {
  return `${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
}

/** "today, 14:22", "yesterday, 20:41", "Friday, 23:59", "October 4, 23:59". */
export function formatDay(value, now = new Date()) {
  const date = new Date(value);
  const diff = dayDifference(date, now);
  let day;
  if (diff === 0) day = "today";
  else if (diff === 1) day = "tomorrow";
  else if (diff === -1) day = "yesterday";
  else if (diff > 1 && diff < 7) day = WEEKDAYS[date.getDay()];
  else day = `${MONTHS[date.getMonth()]} ${date.getDate()}`;
  return `${day}, ${formatTime(date)}`;
}

export function capitalize(text) {
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/** "2 minutes ago", "3 days ago", "last week", "just now". */
export function timeAgo(value, now = new Date()) {
  const seconds = Math.max(0, Math.round((now - new Date(value)) / 1000));
  if (seconds < 10) return "just now";
  if (seconds < 60) return `${seconds} s ago`;
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes} ${minutes === 1 ? "minute" : "minutes"} ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} ${hours === 1 ? "hour" : "hours"} ago`;
  const days = Math.round(hours / 24);
  if (days < 7) return `${days} ${days === 1 ? "day" : "days"} ago`;
  const weeks = Math.round(days / 7);
  if (weeks === 1) return "last week";
  if (weeks < 5) return `${weeks} weeks ago`;
  const date = new Date(value);
  return `on ${MONTHS[date.getMonth()]} ${date.getDate()}`;
}

export function monthYear(value) {
  const date = new Date(value);
  return `${MONTHS[date.getMonth()]} ${date.getFullYear()}`;
}

export function ordinal(n) {
  const words = ["zeroth", "first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth"];
  if (n < words.length) return words[n];
  const tail = n % 100;
  const suffix = tail >= 11 && tail <= 13 ? "th" : (["th", "st", "nd", "rd"][n % 10] ?? "th");
  return `${n}${suffix}`;
}

export function plural(count, singular, pluralForm = `${singular}s`) {
  return `${count} ${count === 1 ? singular : pluralForm}`;
}

export function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/** "2 s per test" from milliseconds, without a trailing ".0". */
export function formatSeconds(ms) {
  return `${Number((ms / 1000).toFixed(1))} s`;
}

/** Local value for <input type="datetime-local"> from an ISO string, and back. */
export function toLocalInput(value) {
  if (!value) return "";
  const date = new Date(value);
  const pad = (n) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

export function fromLocalInput(value) {
  return value ? new Date(value).toISOString() : null;
}
