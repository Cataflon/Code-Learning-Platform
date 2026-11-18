// Small pieces shared by the material screens: the PDF/PPTX label and the course cover.

/** "PDF" in red or "PPTX" in amber, in the pixel terminal font. */
export function FileBadge({ type }) {
  return <span className={`ext ${type === "pptx" ? "pptx" : ""}`}>{type.toUpperCase()}</span>;
}

const COVER_COLORS = {
  indigo: "#b1a6ff",
  blue: "#a3cdff",
  purple: "#efbaff",
  green: "#9be7b4",
  amber: "#ffd699",
  rose: "#ffb3c1",
};

export function courseColor(color) {
  return COVER_COLORS[color] ?? COVER_COLORS.indigo;
}

const GLYPHS = ["while n > 0:", "O(log n)", "{ key: value }", "def f(n):", "for x in xs:", "print(x)"];

/**
 * Generated course cover, as in the prototype: the course colour fading to black, a field of
 * pale squares and one line of code. The same course always gets the same picture.
 */
export function CourseCover({ course, className = "" }) {
  let seed = (course.id * 9301 + 49297) % 233280;
  const random = () => {
    seed = (seed * 9301 + 49297) % 233280;
    return seed / 233280;
  };
  const color = courseColor(course.color);
  const squares = [];
  for (let y = 0; y < 8; y += 1) {
    for (let x = 0; x < 13; x += 1) {
      const value = random();
      if (value < 0.45) continue;
      squares.push(
        <rect
          key={`${x}-${y}`}
          x={x * 25 + 3}
          y={y * 25 + 3}
          width="20"
          height="20"
          fill="#fff"
          opacity={(0.05 + (value - 0.45) * 0.38).toFixed(2)}
        />,
      );
    }
  }
  const gradient = `cover-${course.id}`;
  return (
    <div className={`cover ${className}`} aria-hidden="true">
      <svg viewBox="0 0 320 200" preserveAspectRatio="xMinYMax slice">
        <defs>
          <linearGradient id={gradient} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor={color} />
            <stop offset=".95" stopColor="#14141f" />
          </linearGradient>
        </defs>
        <rect width="320" height="200" fill={`url(#${gradient})`} />
        {squares}
        <text
          x="20"
          y="172"
          fontFamily="'Press Start 2P', 'Courier New', monospace"
          fontSize="15"
          fill="#fff"
          opacity=".95"
          stroke="#0b0b18"
          strokeWidth="5"
          strokeLinejoin="miter"
          style={{ paintOrder: "stroke" }}
        >
          {GLYPHS[course.id % GLYPHS.length]}
        </text>
      </svg>
    </div>
  );
}
