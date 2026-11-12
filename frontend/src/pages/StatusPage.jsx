import { useEffect, useState } from "react";

/** Shows whether the backend answers on /health. */
export default function StatusPage() {
  const [state, setState] = useState("loading"); // loading | ok | down

  useEffect(() => {
    let cancelled = false;
    fetch("/health")
      .then((response) => (response.ok ? response.json() : Promise.reject(response)))
      .then((body) => {
        if (!cancelled) setState(body.status === "ok" ? "ok" : "down");
      })
      .catch(() => {
        if (!cancelled) setState("down");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const label = {
    loading: "Checking the server…",
    ok: "Server is up",
    down: "Server is unreachable",
  }[state];
  const dot = { loading: "bg-idle", ok: "bg-pass", down: "bg-fail" }[state];

  return (
    <main className="flex min-h-screen items-center justify-center">
      <section className="rounded-card border border-line bg-surface px-10 py-8 text-center">
        <h1 className="text-2xl font-bold">Autograder</h1>
        <p className="mt-4 flex items-center justify-center gap-3 text-muted" role="status">
          <span className={`inline-block h-3 w-3 rounded-sm ${dot}`} aria-hidden="true" />
          {label}
        </p>
      </section>
    </main>
  );
}
