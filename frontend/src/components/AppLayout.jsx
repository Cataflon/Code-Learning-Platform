import { BarChart3, BookOpen, LayoutGrid, MessageSquare } from "lucide-react";
import { Link, NavLink, Outlet } from "react-router-dom";

import { homePathFor, useAuth } from "../auth/AuthContext.jsx";
import { Avatar, Logo } from "./ui.jsx";

const STUDENT_NAV = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutGrid },
  { to: "/courses", label: "Courses", icon: MessageSquare },
  { to: "/learn", label: "Learn", icon: BookOpen },
  { to: "/report", label: "Concept report", icon: BarChart3 },
];

const TEACHER_NAV = [{ to: "/courses", label: "My courses", icon: MessageSquare }];

function navClass({ isActive }) {
  return (
    "flex items-center gap-2.5 rounded-lg px-4 py-2.5 transition-colors " +
    (isActive ? "bg-accent-tint font-semibold text-accent-soft" : "text-muted hover:text-ink")
  );
}

/** Header with role-based navigation; the routed page renders below it. */
export default function AppLayout() {
  const { user } = useAuth();
  const nav = user.role === "teacher" ? TEACHER_NAV : STUDENT_NAV;

  return (
    <div className="min-h-screen">
      <header className="border-b border-line bg-header">
        <div className="flex items-center gap-8 px-6 py-3">
          <Link to={homePathFor(user)} aria-label="Autograder home">
            <Logo />
          </Link>
          <nav className="flex flex-1 flex-wrap items-center gap-1" aria-label="Main">
            {nav.map(({ to, label, icon: Icon }) => (
              <NavLink key={to} to={to} className={navClass}>
                <Icon className="h-4 w-4" aria-hidden="true" />
                {label}
              </NavLink>
            ))}
          </nav>
          <Link
            to="/profile"
            className="flex items-center gap-4 rounded-lg px-2 py-1 hover:bg-raised"
            aria-label="Your profile"
          >
            <span className="text-right leading-tight">
              <span className="block font-semibold">{user.full_name}</span>
              <span className="block text-sm capitalize text-muted">{user.role}</span>
            </span>
            <Avatar name={user.full_name} />
          </Link>
        </div>
      </header>
      <main className="mx-auto max-w-[1180px] px-6 py-12">
        <Outlet />
      </main>
    </div>
  );
}
