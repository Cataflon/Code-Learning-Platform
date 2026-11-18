// The PDF renderer (react-pdf / pdf.js). Loaded lazily: it is large and only the viewer needs it.

import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

import { Document, Page, pdfjs } from "react-pdf";

// pdf.js parses the file in a web worker; Vite bundles the worker from pdfjs-dist.
pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url,
).toString();

export default function PdfSheet({ file, page, width, onLoad, onError }) {
  return (
    <Document
      file={file}
      onLoadSuccess={(document) => onLoad?.(document.numPages)}
      onLoadError={onError}
      loading={<p className="text-ink-3">Opening the file…</p>}
      error={<p className="text-bad">The file could not be displayed.</p>}
    >
      <div className="sheet">
        <Page pageNumber={page} width={width} renderAnnotationLayer={false} renderTextLayer />
      </div>
    </Document>
  );
}
