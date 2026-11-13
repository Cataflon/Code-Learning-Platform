import GlyphTideBackground from "./GlyphTideBackground.jsx";
import { Card, Logo } from "./ui.jsx";
import VerdictSquares from "./VerdictSquares.jsx";

/**
 * Frame shared by Sign in and Create account. There is no 8-bit mock-up for these screens,
 * so they reuse the dashboard's pieces: the tide background, a hero card with stars and the
 * big squares, and a pixel card for the form.
 */
export default function AuthShell({ children }) {
  return (
    <>
      <GlyphTideBackground />
      <div className="app">
        <main className="page">
          <div className="wrap grid items-center gap-10 lg:min-h-[calc(100vh-112px)] lg:grid-cols-[minmax(0,1.25fr)_minmax(0,1fr)]">
            <section className="hidden gap-8 lg:grid">
              <Logo />
              <h1 className="text-[clamp(26px,3vw,38px)]">
                Write code.
                <br />
                Get a verdict on every test.
              </h1>
              <p className="lede font-plain">
                Your code runs in isolation within seconds. You also see which concepts you still
                need to review.
              </p>
              <Card className="hero max-w-md">
                <div className="pad">
                  <i
                    className="spark"
                    style={{ right: "9%", top: "18%", "--c": "#ffbe4f" }}
                    aria-hidden="true"
                  />
                  <i
                    className="spark s"
                    style={{ right: "18%", top: "60%", "--c": "#ff92d4", animationDelay: "-.8s" }}
                    aria-hidden="true"
                  />
                  <div className="flex items-baseline justify-between gap-4">
                    <h2>Digit sum</h2>
                    <span className="text-sm text-ink-3">third attempt</span>
                  </div>
                  <VerdictSquares verdicts={["passed", "passed", "passed", "wrong_answer"]} large />
                  <p className="plain">
                    <b className="text-ink">3 of 4 tests pass.</b> The hidden test checks negative
                    numbers.
                  </p>
                </div>
              </Card>
              <p className="text-sm text-ink-3">Software Engineering project, UTCN</p>
            </section>
            <Card className="mx-auto w-full max-w-md">
              <div className="pad grid gap-2 py-8">
                <div className="mb-4 lg:hidden">
                  <Logo />
                </div>
                {children}
              </div>
            </Card>
          </div>
        </main>
      </div>
    </>
  );
}
