// Fundalul animat: o "maree" din caractere ASCII pe negru, in stilul React Bits "Glyph Tide".
// Este o recreare proprie (Glyph Tide original e in React Bits Pro, cu licenta).
// Daca proiectul are licenta Pro, se poate folosi componenta originala:
//   npx shadcn@latest add @reactbits-starter/glyph-tide-tw
// cu: colors={["#8f80ff", "#ffc6f4"]} backgroundColor="#000000" interactive={false} clickRipples={false}
// si o perioada lenta (tidePeriod ~60). Altfel se foloseste componenta de mai jos.
//
// Folosire: <GlyphTideBackground /> o singura data, in layout-ul aplicatiei (sub header si continut).
// Se pune pe pozitie fixa, in spatele paginii (z-index 0), fara pointer events.

import { useEffect, useRef } from "react";

const RAMP = " .:~+*#%@";
const WATER = "#8f80ff"; // apa (violet)
const FOAM = "#ffc6f4"; // spuma de la mal (roz)
const LAND = "rgba(150,140,215,.34)"; // nisipul descoperit

function hash(x, y) {
  const n = Math.sin(x * 127.1 + y * 311.7) * 43758.5453;
  return n - Math.floor(n);
}
function vnoise(x, y) {
  const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi;
  const u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf);
  const a = hash(xi, yi), b = hash(xi + 1, yi), c = hash(xi, yi + 1), d = hash(xi + 1, yi + 1);
  return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v;
}

export default function GlyphTideBackground({
  opacity = 0.34,      // cat de vizibil e fundalul (0..1)
  tidePeriod = 60,     // secunde pentru o urcare + coborare a apei
  swellSpeed = 0.5,    // viteza valurilor
  fontSize = 12,
}) {
  const ref = useRef(null);

  useEffect(() => {
    const cv = ref.current;
    const cx = cv.getContext("2d");
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const LH = Math.round(fontSize * 1.25);
    let W = 0, H = 0, CW = 7.2, cols = 0, rows = 0, hmap = null, raf = 0, last = 0;

    function size() {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      W = window.innerWidth; H = window.innerHeight;
      cv.width = W * dpr; cv.height = H * dpr;
      cx.setTransform(dpr, 0, 0, dpr, 0, 0);
      cx.font = `${fontSize}px "JetBrains Mono", ui-monospace, Menlo, Consolas, monospace`;
      cx.textBaseline = "top";
      CW = cx.measureText("@").width || 7.2;
      cols = Math.ceil(W / CW) + 1; rows = Math.ceil(H / LH) + 1;
      hmap = new Float32Array(cols * rows);
      let lo = 1, hi = 0;
      for (let y = 0; y < rows; y++) for (let x = 0; x < cols; x++) {
        const px = (x * CW) / 260, py = (y * LH) / 260;
        const h = 0.55 * vnoise(px, py) + 0.28 * vnoise(px * 2.1 + 9, py * 2.1 + 4) + 0.17 * vnoise(px * 4.3 + 31, py * 4.3 + 17);
        hmap[y * cols + x] = h; if (h < lo) lo = h; if (h > hi) hi = h;
      }
      for (let i = 0; i < hmap.length; i++) hmap[i] = (hmap[i] - lo) / (hi - lo);
    }

    function draw(now) {
      const t = now / 1000;
      const level = 0.5 + 0.2 * Math.sin((t * 2 * Math.PI) / tidePeriod);
      cx.fillStyle = "#000"; cx.fillRect(0, 0, W, H);
      for (let y = 0; y < rows; y++) {
        let water = "", foam = "", land = "";
        for (let x = 0; x < cols; x++) {
          const h = hmap[y * cols + x];
          const swell = Math.sin(x * 0.11 + y * 0.19 - t * swellSpeed + h * 9) * 0.5 + 0.5;
          const d = level + (swell - 0.5) * 0.035 - h;
          let w = " ", f = " ", l = " ";
          if (d > 0) {
            if (d < 0.022) f = d < 0.008 ? "@" : d < 0.015 ? "%" : "#";
            else { const k = swell * (1 - Math.min(1, d * 2.2) * 0.6); w = RAMP[1 + Math.floor(k * 4.99)]; }
          } else {
            let c = h * 16; c -= Math.floor(c);
            if (h < 0.7 && c < 0.09) l = (x + y) % 2 ? "." : " ";
            else if (-d < 0.05) l = hash(x, y) > 0.55 ? ":" : ".";
          }
          water += w; foam += f; land += l;
        }
        const yy = y * LH;
        cx.fillStyle = WATER; cx.fillText(water, 0, yy);
        cx.fillStyle = FOAM; cx.fillText(foam, 0, yy);
        cx.fillStyle = LAND; cx.fillText(land, 0, yy);
      }
    }

    function frame(now) {
      if (now - last > 45) { last = now; draw(now); } // ~22 fps, suficient si ieftin
      raf = requestAnimationFrame(frame);
    }
    function onVisibility() {
      cancelAnimationFrame(raf);
      if (!document.hidden && !reduce) raf = requestAnimationFrame(frame);
    }
    function onResize() { size(); if (reduce) draw(9000); }

    size();
    if (reduce) draw(9000); else raf = requestAnimationFrame(frame);
    document.addEventListener("visibilitychange", onVisibility);
    window.addEventListener("resize", onResize);
    return () => {
      cancelAnimationFrame(raf);
      document.removeEventListener("visibilitychange", onVisibility);
      window.removeEventListener("resize", onResize);
    };
  }, [tidePeriod, swellSpeed, fontSize]);

  return (
    <canvas
      ref={ref}
      aria-hidden="true"
      style={{ position: "fixed", inset: 0, width: "100%", height: "100%", zIndex: 0, pointerEvents: "none", opacity }}
    />
  );
}
