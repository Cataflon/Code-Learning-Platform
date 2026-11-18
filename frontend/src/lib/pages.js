// Page lists such as "12-15, 18", the same rules as the backend (services/pages.py), so the
// teacher sees a mistake while typing instead of after saving.

const PART = /^(\d+)(?:\s*-\s*(\d+))?$/;

/** [[12, 15], [18, 18]], or throws an Error with a readable message. Empty = whole material. */
export function parsePages(text, pageCount) {
  const value = (text ?? "").trim();
  if (!value) return [];
  return value.split(",").map((raw) => {
    const part = raw.trim();
    const match = PART.exec(part);
    if (!match) throw new Error("Use a format like 12-15, 18");
    const start = Number(match[1]);
    const end = Number(match[2] ?? match[1]);
    if (start < 1) throw new Error("Pages start at 1");
    if (end < start) throw new Error(`The range ${start}-${end} goes backwards`);
    if (pageCount && end > pageCount) throw new Error(`The material has ${pageCount} pages`);
    return [start, end];
  });
}

/** Error message for a pages field, or "" when it is fine. */
export function pagesError(text, pageCount) {
  try {
    parsePages(text, pageCount);
    return "";
  } catch (error) {
    return error.message;
  }
}

/** Set of page numbers covered by a list, for highlighting; empty list = nothing highlighted. */
export function pageSet(text, pageCount) {
  const pages = new Set();
  try {
    for (const [start, end] of parsePages(text, pageCount)) {
      for (let page = start; page <= end; page += 1) pages.add(page);
    }
  } catch {
    // an invalid list in the address just highlights nothing
  }
  return pages;
}

/** "Pages 12-15", "Page 4" or "All pages" for a link. */
export function describePages(text, unit = "pages") {
  if (!text) return unit === "slides" ? "All slides" : "All pages";
  const single = /^\d+$/.test(text.trim());
  const word = unit === "slides" ? (single ? "Slide" : "Slides") : single ? "Page" : "Pages";
  return `${word} ${text}`;
}

export function unitOf(material) {
  return material.file_type === "pptx" ? "slides" : "pages";
}
