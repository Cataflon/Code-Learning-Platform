// Public landing page at "/" for visitors who are not signed in. Its structure follows the
// classic product landing page (sticky header with section links, hero with two calls to action,
// a "runs on" strip, the lifecycle loop, role tabs, a feature grid, a trust section, a final call
// to action and a footer); the look is the platform's own 8-bit theme (docs/design-8bit).

import {
  ArrowRight,
  BarChart3,
  BookOpen,
  Check,
  Code,
  Container,
  GraduationCap,
  ListChecks,
  Lock,
  PenLine,
  Play,
  ShieldCheck,
  Sparkles,
  Timer,
  Users,
  WifiOff,
} from "lucide-react";
import { useRef, useState } from "react";
import { Link } from "react-router-dom";

import GlyphTideBackground from "../components/GlyphTideBackground.jsx";
import { buttonClass, Card, Chip, IconBadge, Logo, ProgressBar } from "../components/ui.jsx";
import VerdictSquares from "../components/VerdictSquares.jsx";

const SECTIONS = [
  { id: "features", label: "Features" },
  { id: "how-it-works", label: "How it works" },
  { id: "roles", label: "Students & teachers" },
  { id: "trust", label: "Sandbox" },
];

const STACK = ["Python 3.12", "Docker sandbox", "FastAPI", "PostgreSQL", "React"];

const LOOP = [
  { icon: PenLine, title: "Create", text: "The teacher writes the task and its tests, each linked to the concepts it checks." },
  { icon: Code, title: "Code", text: "The student writes Python in the browser editor, with the public examples beside it." },
  { icon: Play, title: "Run", text: "Every submission runs in its own isolated container, with time and memory limits." },
  { icon: ListChecks, title: "Verdict", text: "A verdict on every test: passed, wrong answer, time limit, memory limit or error." },
  { icon: BarChart3, title: "Review", text: "Failed tests add up per concept, so the student sees where they go wrong." },
  { icon: BookOpen, title: "Learn", text: "Each failed test points to the exact pages of the course material that explain it." },
];

const FEATURES = [
  {
    icon: Container,
    tint: "accent",
    title: "Autograder in a sandbox",
    text: "Code runs in a Docker container with no network, a read-only file system and strict time and memory limits.",
  },
  {
    icon: ListChecks,
    tint: "ok",
    title: "A verdict on every test",
    text: "Not just a score: each test says what happened, with input and output for public tests and a hint for hidden ones.",
  },
  {
    icon: BarChart3,
    tint: "bad",
    title: "Where you go wrong",
    text: "A report per concept, from the latest attempt at each assignment: to review, in progress or mastered.",
  },
  {
    icon: BookOpen,
    tint: "warn",
    title: "Materials that answer the error",
    text: "Lectures and labs as PDF or PPTX, read in the browser. A failed test opens the recommended pages.",
  },
  {
    icon: Sparkles,
    tint: "pink",
    title: "AI test drafts",
    text: "From the task statement alone, the AI writes a solution, a second one to check it, and test inputs. Expected outputs come from the sandbox.",
  },
  {
    icon: Users,
    tint: "blue",
    title: "Class statistics",
    text: "Submissions, scores and a class concept report show the teacher which topics need another lecture.",
  },
];

const ROLES = {
  students: {
    label: "For students",
    icon: GraduationCap,
    title: "Know exactly what to fix before the next attempt",
    points: [
      "Join a course with the code from your teacher",
      "See the task, the public tests and your remaining attempts",
      "Get a verdict per test in seconds, with input, expected and actual output",
      "Follow your concept report and the recommended pages",
    ],
  },
  teachers: {
    label: "For teachers",
    icon: Users,
    title: "Spend your time on teaching, not on grading",
    points: [
      "Create courses, assignments and tests linked to concepts",
      "Upload lectures and labs and link pages to tests",
      "Generate test drafts with AI from the task statement alone",
      "Follow submissions and the class concept report",
    ],
  },
};

const TRUST = [
  { icon: WifiOff, title: "No network", text: "A submission cannot reach the internet or other services." },
  { icon: Lock, title: "Read-only", text: "The code is mounted read-only; nothing it writes survives the run." },
  { icon: Timer, title: "Time and memory limits", text: "Each test stops at the limit and gets its own clear verdict." },
  { icon: ShieldCheck, title: "Fair tests", text: "Expected outputs come from a reference solution run in the same sandbox." },
];

const AI_STEPS = [
  { title: "You write the statement", text: "Title and task are enough. You may also paste your own solution." },
  { title: "The AI writes two solutions", text: "Separately, plus normal, edge and larger inputs, each with a reason." },
  { title: "The sandbox computes outputs", text: "The solution must pass the example; tests where the two disagree are flagged." },
  { title: "You approve the drafts", text: "Drafts never count until you approve them, one by one or all at once." },
];

function SectionTitle({ eyebrow, title, children }) {
  return (
    <div className="grid max-w-3xl gap-4">
      <span className="font-display text-[11px] uppercase tracking-wider text-accent-strong">{eyebrow}</span>
      <h2 className="text-[clamp(16px,2.2vw,22px)] leading-relaxed">{title}</h2>
      {children && <p className="lede font-plain">{children}</p>}
    </div>
  );
}

function Header() {
  return (
    <header className="top">
      <div className="wrap justify-between">
        <Link to="/" aria-label="Autograder home">
          <Logo />
        </Link>
        <nav aria-label="Sections" className="hidden gap-6 text-ink-3 md:flex">
          {SECTIONS.map((section) => (
            <a key={section.id} href={`#${section.id}`} className="hover:text-ink">
              {section.label}
            </a>
          ))}
        </nav>
        <div className="flex items-center">
          <Link to="/login" className={buttonClass("outline", "sm")}>
            Sign in
          </Link>
          <Link to="/register" className={buttonClass("primary", "sm", "hidden sm:inline-flex")}>
            Create account
          </Link>
        </div>
      </div>
    </header>
  );
}

function HeroPreview() {
  const tests = [
    { name: "Example from the task", verdict: "passed", tone: "ok", label: "Passed", ms: "18 ms" },
    { name: "Zero", verdict: "passed", tone: "ok", label: "Passed", ms: "16 ms" },
    { name: "Large number", verdict: "passed", tone: "ok", label: "Passed", ms: "21 ms" },
    { name: "Hidden test #1", verdict: "wrong_answer", tone: "bad", label: "Wrong answer", ms: "17 ms" },
  ];
  return (
    <Card className="hero">
      <div className="pad grid gap-5">
        <i className="spark" style={{ right: "7%", top: "10%", "--c": "#ffbe4f" }} aria-hidden="true" />
        <i className="spark s" style={{ right: "16%", top: "48%", "--c": "#ff92d4", animationDelay: "-.8s" }} aria-hidden="true" />
        <div className="flex flex-wrap items-baseline justify-between gap-3">
          <h3 className="font-display text-[12px] text-ink">Digit sum</h3>
          <span className="text-sm text-ink-3">attempt 3 of 10</span>
        </div>
        <pre className="io overflow-x-auto p-4 font-mono text-[13px] leading-relaxed text-ink-2">
          {"n = int(input())\ntotal = 0\nwhile n > 0:\n    total += n % 10\n    n //= 10\nprint(total)"}
        </pre>
        <VerdictSquares verdicts={tests.map((test) => test.verdict)} large />
        <ul className="grid gap-2 font-plain text-sm">
          {tests.map((test) => (
            <li key={test.name} className="flex items-center justify-between gap-3">
              <span className="truncate text-ink-2">{test.name}</span>
              <span className="flex shrink-0 items-center gap-2">
                <span className="text-ink-3">{test.ms}</span>
                <Chip tone={test.tone}>{test.label}</Chip>
              </span>
            </li>
          ))}
        </ul>
        <p className="plain dash-top pt-4 text-ink-2">
          <b className="text-ink">3 of 4 tests pass.</b> The hidden test checks negative numbers:
          see <span className="text-warn">Lecture 4, pages 12-15</span>.
        </p>
      </div>
    </Card>
  );
}

function Hero() {
  return (
    <section className="grid items-center gap-12 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)]">
      <div className="grid gap-7">
        <span>
          <Chip tone="pink" icon={Sparkles}>
            New: AI test drafts from the task statement
          </Chip>
        </span>
        <h1 className="text-[clamp(20px,2.7vw,32px)] leading-snug">
          From task to verdict.
          <br />
          One platform for programming courses.
        </h1>
        <p className="lede font-plain">
          Teachers publish Python assignments with tests linked to concepts. Students submit code,
          get a verdict on every test within seconds and see which concepts and which course pages
          to review before the next attempt.
        </p>
        <div className="flex flex-wrap items-center gap-2">
          <Link to="/register" className={buttonClass("primary")}>
            Create a free account <ArrowRight className="go" aria-hidden="true" />
          </Link>
          <a href="#how-it-works" className={buttonClass("outline")}>
            See how it works
          </a>
        </div>
        <p className="text-sm text-ink-3">Free for the course. No installation: everything runs in the browser.</p>
      </div>
      <HeroPreview />
    </section>
  );
}

function StackStrip() {
  return (
    <section aria-label="Built with" className="dash-top grid gap-4 pt-8 text-center">
      <p className="text-sm text-ink-3">Built on open, proven technology</p>
      <ul className="flex flex-wrap justify-center gap-x-10 gap-y-3">
        {STACK.map((name) => (
          <li key={name} className="font-display text-[12px] text-ink-3">
            {name}
          </li>
        ))}
      </ul>
    </section>
  );
}

function Loop() {
  return (
    <section id="how-it-works" className="grid scroll-mt-24 gap-10">
      <SectionTitle eyebrow="How it works" title="One loop, from the task statement to mastery">
        Every attempt goes through the same six steps, so each submission teaches something.
      </SectionTitle>
      <ol className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {LOOP.map((step, index) => (
          <li key={step.title}>
            <Card lift className="h-full">
              <div className="pad grid gap-3">
                <div className="flex items-center gap-3">
                  <IconBadge icon={step.icon} />
                  <span className="font-display text-[11px] text-ink-3">{String(index + 1).padStart(2, "0")}</span>
                  <h3 className="font-display text-[12px] text-ink">{step.title}</h3>
                </div>
                <p className="plain text-ink-2">{step.text}</p>
              </div>
            </Card>
          </li>
        ))}
      </ol>
    </section>
  );
}

function Features() {
  return (
    <section id="features" className="grid scroll-mt-24 gap-10">
      <SectionTitle eyebrow="Features" title="Everything a programming course needs, in one place" />
      <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
        {FEATURES.map((feature) => (
          <Card key={feature.title} tint={feature.tint} lift className="h-full">
            <div className="pad grid gap-3">
              <feature.icon className="h-6 w-6 text-ink" aria-hidden="true" />
              <h3 className="font-display text-[12px] leading-relaxed text-ink">{feature.title}</h3>
              <p className="plain text-ink-2">{feature.text}</p>
            </div>
          </Card>
        ))}
      </div>
    </section>
  );
}

function StudentPreview() {
  const concepts = [
    { name: "Recursion", value: 92, color: "var(--ok)", level: "Mastered" },
    { name: "Loops", value: 71, color: "var(--warn)", level: "In progress" },
    { name: "Lists", value: 38, color: "var(--bad)", level: "To review" },
  ];
  return (
    <Card tint="bad">
      <div className="pad grid gap-4">
        <h3 className="font-display text-[12px] text-ink">Where you go wrong</h3>
        {concepts.map((concept) => (
          <div key={concept.name} className="grid gap-2">
            <div className="flex justify-between gap-3 font-plain text-sm">
              <span className="text-ink">{concept.name}</span>
              <span className="text-ink-3">
                {concept.value}% · {concept.level}
              </span>
            </div>
            <ProgressBar value={concept.value} color={concept.color} label={`${concept.name}: ${concept.value}%`} />
          </div>
        ))}
      </div>
    </Card>
  );
}

function TeacherPreview() {
  return (
    <Card tint="pink">
      <div className="pad grid gap-4">
        <div className="flex flex-wrap items-center gap-2">
          <h3 className="flex-1 font-display text-[12px] text-ink">AI drafts</h3>
          <Chip tone="pink">8 ready for review</Chip>
        </div>
        {[
          ["Negative number", "-9075", "21"],
          ["Largest value", "999999999999999999", "162"],
        ].map(([name, input, output]) => (
          <div key={name} className="dash-top grid gap-2 pt-3 font-plain text-sm">
            <div className="flex flex-wrap items-center gap-2">
              <b className="text-ink">{name}</b>
              <Chip tone="pink">AI draft</Chip>
              <Chip tone="neutral">hidden</Chip>
            </div>
            <span className="font-mono text-ink-3">
              in: {input} → out: {output}
            </span>
          </div>
        ))}
        <span className="text-sm text-ink-3">Expected outputs computed in the sandbox and cross-checked by a second solution.</span>
      </div>
    </Card>
  );
}

function Roles() {
  const [active, setActive] = useState("students");
  const tabs = useRef({});
  const keys = Object.keys(ROLES);
  const role = ROLES[active];

  function onKeyDown(event) {
    const step = { ArrowRight: 1, ArrowLeft: -1 }[event.key];
    if (!step) return;
    const next = keys[(keys.indexOf(active) + step + keys.length) % keys.length];
    setActive(next);
    tabs.current[next]?.focus();
  }

  return (
    <section id="roles" className="grid scroll-mt-24 gap-8">
      <SectionTitle eyebrow="Students & teachers" title="Built for both sides of the course" />
      <div role="tablist" aria-label="Who it is for" className="tabs" onKeyDown={onKeyDown}>
        {keys.map((key) => {
          const Icon = ROLES[key].icon;
          return (
            <button
              key={key}
              ref={(node) => (tabs.current[key] = node)}
              type="button"
              role="tab"
              id={`tab-${key}`}
              aria-selected={active === key}
              aria-controls={`panel-${key}`}
              tabIndex={active === key ? 0 : -1}
              className="tab flex items-center gap-2"
              onClick={() => setActive(key)}
            >
              <Icon className="h-4 w-4" aria-hidden="true" />
              {ROLES[key].label}
            </button>
          );
        })}
      </div>
      <div
        role="tabpanel"
        id={`panel-${active}`}
        aria-labelledby={`tab-${active}`}
        className="grid items-center gap-10 lg:grid-cols-2"
      >
        <div className="grid gap-5">
          <h3 className="font-display text-[14px] leading-relaxed text-ink">{role.title}</h3>
          <ul className="grid gap-3">
            {role.points.map((point) => (
              <li key={point} className="flex gap-3 font-plain text-ink-2">
                <Check className="mt-1 h-4 w-4 shrink-0 text-ok" aria-hidden="true" />
                {point}
              </li>
            ))}
          </ul>
          <span>
            <Link to="/register" className={buttonClass("primary", "sm")}>
              {active === "students" ? "Join your course" : "Create your course"}
            </Link>
          </span>
        </div>
        {active === "students" ? <StudentPreview /> : <TeacherPreview />}
      </div>
    </section>
  );
}

function AiSection() {
  return (
    <Card tint="pink">
      <div className="pad grid gap-8 py-10 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)] lg:items-center">
        <div className="grid gap-4">
          <Chip tone="pink" icon={Sparkles} className="justify-self-start">
            AI, the careful way
          </Chip>
          <h2 className="text-[clamp(14px,1.8vw,18px)] leading-relaxed">AI drafts the tests. The sandbox decides the answers.</h2>
          <p className="plain text-ink-2">
            A wrong expected output would punish correct code, so the model never writes one: a solution
            runs on every input in the sandbox. When the AI writes that solution, it must pass the example
            in the statement and a second, independent solution checks it. The teacher approves every test.
          </p>
        </div>
        <ol className="grid gap-4 sm:grid-cols-2">
          {AI_STEPS.map((step, index) => (
            <li key={step.title} className="grid content-start gap-2 p-4" style={{ background: "var(--card-2)" }}>
              <span className="font-display text-[11px] text-pink">{index + 1}</span>
              <b className="font-plain text-ink">{step.title}</b>
              <span className="font-plain text-sm text-ink-3">{step.text}</span>
            </li>
          ))}
        </ol>
      </div>
    </Card>
  );
}

function Trust() {
  return (
    <section id="trust" className="grid scroll-mt-24 gap-10">
      <SectionTitle eyebrow="Sandbox" title="A verdict you can trust">
        Student code never runs on the server itself. Every submission gets a fresh container that is
        thrown away when the tests finish.
      </SectionTitle>
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {TRUST.map((item) => (
          <Card key={item.title} tint="edge" className="h-full">
            <div className="pad grid gap-3">
              <IconBadge icon={item.icon} />
              <h3 className="font-display text-[11px] leading-relaxed text-ink">{item.title}</h3>
              <p className="plain text-sm text-ink-2">{item.text}</p>
            </div>
          </Card>
        ))}
      </div>
      <AiSection />
    </section>
  );
}

function FinalCta() {
  return (
    <Card className="hero">
      <div className="pad grid justify-items-center gap-6 py-14 text-center">
        <i className="spark" style={{ left: "10%", top: "22%", "--c": "#5ee08c" }} aria-hidden="true" />
        <i className="spark s" style={{ right: "12%", top: "60%", "--c": "#5cc6ff", animationDelay: "-.6s" }} aria-hidden="true" />
        <VerdictSquares verdicts={["passed", "passed", "passed", "passed"]} large />
        <h2 className="text-[clamp(14px,2vw,20px)] leading-relaxed">Ready for your next attempt?</h2>
        <p className="lede font-plain">Create an account, join your course with its code and submit your first solution.</p>
        <div className="flex flex-wrap justify-center gap-2">
          <Link to="/register" className={buttonClass("primary")}>
            Create a free account
          </Link>
          <Link to="/login" className={buttonClass("outline")}>
            I already have an account
          </Link>
        </div>
      </div>
    </Card>
  );
}

function Footer() {
  const columns = [
    { title: "Platform", links: [["Features", "#features"], ["How it works", "#how-it-works"], ["Sandbox", "#trust"]] },
    { title: "Account", links: [["Sign in", "/login"], ["Create account", "/register"], ["System status", "/status"]] },
  ];
  return (
    <footer className="dash-top mt-6">
      <div className="wrap grid gap-10 py-12 sm:grid-cols-[minmax(0,2fr)_repeat(2,minmax(0,1fr))]">
        <div className="grid content-start gap-4">
          <Logo />
          <p className="plain max-w-sm text-sm text-ink-3">
            A programming platform with an autograder, concept reports and course materials.
            Software Engineering project, UTCN.
          </p>
        </div>
        {columns.map((column) => (
          <nav key={column.title} aria-label={column.title} className="grid content-start gap-3">
            <h2 className="text-[11px]">{column.title}</h2>
            {column.links.map(([label, href]) =>
              href.startsWith("#") ? (
                <a key={label} href={href} className="text-ink-3 hover:text-ink">
                  {label}
                </a>
              ) : (
                <Link key={label} to={href} className="text-ink-3 hover:text-ink">
                  {label}
                </Link>
              ),
            )}
          </nav>
        ))}
      </div>
    </footer>
  );
}

export default function LandingPage() {
  return (
    <>
      <GlyphTideBackground />
      <div className="app">
        <Header />
        <main className="page">
          <div className="wrap view gap-24">
            <Hero />
            <StackStrip />
            <Loop />
            <Features />
            <Roles />
            <Trust />
            <FinalCta />
          </div>
        </main>
        <Footer />
      </div>
    </>
  );
}

