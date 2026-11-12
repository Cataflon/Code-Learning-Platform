import { Logo } from "./ui.jsx";
import VerdictSquares from "./VerdictSquares.jsx";

/** Two-column frame shared by Sign in and Create account (mockup 01). */
export default function AuthShell({ children }) {
  return (
    <div className="grid min-h-screen lg:grid-cols-[1.25fr_1fr]">
      <aside className="relative hidden flex-col justify-between overflow-hidden bg-gradient-to-b from-[#9d97f5] via-[#5a4fe0] to-[#2b2298] p-12 lg:flex">
        <Logo light />
        <div className="max-w-xl">
          <h1 className="text-6xl font-bold leading-[1.15]">
            Write code.
            <br />
            Get a verdict on every test.
          </h1>
          <p className="mt-6 text-lg leading-relaxed text-white/85">
            Your code runs in isolation within seconds. You also see which concepts you still need
            to review.
          </p>
          <div className="mt-8 max-w-sm rounded-card border border-white/10 bg-[#2a2766]/90 p-5">
            <div className="flex items-baseline justify-between">
              <span className="font-semibold">Digit sum</span>
              <span className="text-sm text-white/70">third attempt</span>
            </div>
            <div className="mt-4">
              <VerdictSquares verdicts={["passed", "passed", "passed", "wrong_answer"]} large />
            </div>
            <p className="mt-4 text-sm text-white/85">
              <strong className="text-white">3 of 4 tests passed.</strong> The hidden test checks
              negative numbers.
            </p>
          </div>
        </div>
        <p className="text-sm text-white/70">Software Engineering project, UTCN</p>
      </aside>
      <main className="flex items-center justify-center bg-header px-6 py-12">
        <div className="w-full max-w-sm">{children}</div>
      </main>
    </div>
  );
}
