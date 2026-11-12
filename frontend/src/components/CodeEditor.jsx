// Monaco editor (the engine of VS Code) as a controlled component.
// Monaco is bundled locally instead of being fetched from a CDN, so the demo works offline.

import Editor, { loader } from "@monaco-editor/react";
// Only the editor core and the Python grammar are imported, not every language Monaco ships.
import * as monaco from "monaco-editor/editor/editor.api.js";
import editorWorker from "monaco-editor/editor/editor.worker.js?worker";

import "monaco-editor/languages/definitions/python/register.js";

self.MonacoEnvironment = { getWorker: () => new editorWorker() };
loader.config({ monaco });

monaco.editor.defineTheme("autograder-dark", {
  base: "vs-dark",
  inherit: true,
  rules: [
    { token: "keyword", foreground: "b4b1ff" },
    { token: "number", foreground: "fbbf24" },
    { token: "string", foreground: "4ade80" },
    { token: "comment", foreground: "6b6e8a" },
  ],
  colors: {
    "editor.background": "#171927",
    "editor.lineHighlightBackground": "#1f2133",
    "editorLineNumber.foreground": "#6b6e8a",
    "editorLineNumber.activeForeground": "#b4b1ff",
  },
});

export default function CodeEditor({ value, onChange, readOnly = false, height = 320 }) {
  return (
    <Editor
      height={height}
      language="python"
      theme="autograder-dark"
      value={value}
      onChange={(next) => onChange?.(next ?? "")}
      options={{
        readOnly,
        minimap: { enabled: false },
        fontFamily: "JetBrains Mono, monospace",
        fontSize: 14,
        scrollBeyondLastLine: false,
        tabSize: 4,
        automaticLayout: true,
        padding: { top: 16, bottom: 16 },
      }}
    />
  );
}
